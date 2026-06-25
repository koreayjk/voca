// ============================================================
// IM VOCA — sync-org-seats (학원/단체 구독 좌석수 동기화)
// 승인 학생/공동관리자 수가 바뀔 때 호출 → Stripe 구독 quantity 를
// 현재 인원(원장 제외 승인 구성원)에 맞춰 갱신한다.
//   proration_behavior:'create_prorations'
//   → 중도 가입자는 남은 기간만큼 일할(proration) 계산되어
//     다음 청구일(매월 1일)에 합산 청구된다.
// 과금 대상 = create-checkout 과 동일: org_status='approved' AND id != owner_id
// 배포: supabase functions deploy sync-org-seats
// env: STRIPE_SECRET_KEY, SUPABASE_URL, SB_SERVICE_ROLE_KEY
// 입력(body): { org_id }
// ============================================================
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import Stripe from 'https://esm.sh/stripe@12.0.0?target=deno'

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') ?? '', {
  apiVersion: '2023-10-16',
  httpClient: Stripe.createFetchHttpClient(),
})

const svc = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SB_SERVICE_ROLE_KEY') ?? '',
)

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}
function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { ...cors, 'Content-Type': 'application/json' } })
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })
  try {
    // 1) 호출자 인증 (단체 관리자 JWT)
    const token = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '')
    if (!token) return json({ error: 'no_token' }, 401)
    const { data: ures, error: uerr } = await svc.auth.getUser(token)
    if (uerr || !ures?.user) return json({ error: 'invalid_token' }, 401)
    const uid = ures.user.id

    const { org_id } = await req.json().catch(() => ({}))
    if (!org_id) return json({ error: 'org_id_required' }, 400)

    // 2) 호출자가 해당 org 의 승인된 관리자(owner 역할)인지 검증
    //    (주 관리자/공동 관리자 모두 학생 승인 권한이 있으므로 둘 다 허용.
    //     좌석수는 입력값이 아니라 DB 에서 다시 세므로 위·변조 위험 없음)
    const { data: me } = await svc
      .from('members')
      .select('id, org_id, org_role, org_status')
      .eq('id', uid)
      .single()
    if (!me || me.org_id !== org_id || me.org_role !== 'owner' || me.org_status !== 'approved') {
      return json({ error: 'forbidden' }, 403)
    }

    // 3) 단체 결제 상태 조회
    const { data: org } = await svc
      .from('orgs')
      .select('id, owner_id, stripe_customer_id, stripe_subscription_id, billing_active')
      .eq('id', org_id)
      .single()
    if (!org) return json({ error: 'org_not_found' }, 404)
    // 결제중이 아니면 동기화할 구독이 없음 → 무시 (결제 시작 시 create-checkout 이 정확히 카운트)
    if (!org.billing_active) return json({ skipped: 'not_billing' })

    // 4) 현재 과금 대상 수 = 원장 제외 승인 구성원 (학생 + 공동관리자)
    const { count } = await svc
      .from('members')
      .select('id', { count: 'exact', head: true })
      .eq('org_id', org_id)
      .eq('org_status', 'approved')
      .neq('id', org.owner_id)
    const quantity = Math.max(1, count ?? 1)

    // 5) 대상 구독 찾기 (저장된 subscription_id 우선, 없으면 customer 로 조회)
    let subId = org.stripe_subscription_id as string | null
    if (!subId && org.stripe_customer_id) {
      const subs = await stripe.subscriptions.list({ customer: org.stripe_customer_id, status: 'active', limit: 1 })
      subId = subs.data[0]?.id ?? null
    }
    if (!subId) return json({ skipped: 'no_subscription' })

    const sub = await stripe.subscriptions.retrieve(subId)
    const item = sub.items.data[0]
    if (!item) return json({ error: 'no_subscription_item' }, 500)
    const currentQty = item.quantity ?? 0
    if (currentQty === quantity) return json({ ok: true, unchanged: true, quantity })

    // 6) 수량 갱신 — 남은 기간 일할 계산 후 다음 청구일에 합산
    await stripe.subscriptions.update(subId, {
      items: [{ id: item.id, quantity }],
      proration_behavior: 'create_prorations',
    })

    return json({ ok: true, quantity, previous: currentQty })
  } catch (e) {
    console.error('sync-org-seats error:', e)
    return json({ error: String((e as Error)?.message || e) }, 500)
  }
})
