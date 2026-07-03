// ============================================================
// IM VOCA — create-checkout (학원/단체 구독 결제)
// 과금 대상 = 주 관리자(원장) 제외한 승인된 모든 구성원
//   = 승인 학생 + 공동 관리자(선생님). 원장(단체장)만 무료.
// 배포: supabase functions deploy create-checkout
// env: STRIPE_SECRET_KEY, SUPABASE_URL, SB_SERVICE_ROLE_KEY
// ============================================================
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import Stripe from 'https://esm.sh/stripe@12.0.0?target=deno'

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') ?? '', {
  apiVersion: '2023-10-16',
  httpClient: Stripe.createFetchHttpClient(),
})

const supabase = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SB_SERVICE_ROLE_KEY') ?? '',
)

// 학원 요금제 가격 (Live, $2.99/인/월, Quantity 방식)
const ORG_PRICE_ID = 'price_1TkwZQ972sPWG4wXklhImMFD'

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

// 다음 "한국시간(KST) 1일 0시"의 Unix timestamp(초)
function nextKstFirstUnix(): number {
  const now = new Date()
  const kstNow = new Date(now.getTime() + 9 * 3600 * 1000)
  const y = kstNow.getUTCFullYear()
  const m = kstNow.getUTCMonth()
  const kstFirst = Date.UTC(y, m + 1, 1, 0, 0, 0)
  const utcMs = kstFirst - 9 * 3600 * 1000
  return Math.floor(utcMs / 1000)
}

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })

  try {
    const { org_id } = await req.json()
    if (!org_id) {
      return new Response(JSON.stringify({ error: 'org_id required' }), { status: 400, headers: { ...cors, 'Content-Type': 'application/json' } })
    }

    // 0) 호출자 인증 — 로그인한 "주 관리자(원장)" 본인만 결제 세션 생성 가능.
    //    (미검증 시: 누구나 임의 org 로 세션 생성 + redirect URL 조작 가능했음)
    const token = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '')
    if (!token) {
      return new Response(JSON.stringify({ error: 'no_token' }), { status: 401, headers: { ...cors, 'Content-Type': 'application/json' } })
    }
    const { data: ures, error: uerr } = await supabase.auth.getUser(token)
    if (uerr || !ures?.user) {
      return new Response(JSON.stringify({ error: 'invalid_token' }), { status: 401, headers: { ...cors, 'Content-Type': 'application/json' } })
    }
    const uid = ures.user.id

    // 1) 단체 조회
    const { data: org, error: orgErr } = await supabase
      .from('orgs')
      .select('id, name, owner_id, stripe_customer_id, stripe_subscription_id, billing_active')
      .eq('id', org_id)
      .single()
    if (orgErr || !org) {
      return new Response(JSON.stringify({ error: 'org not found' }), { status: 404, headers: { ...cors, 'Content-Type': 'application/json' } })
    }
    if (org.owner_id !== uid) {
      return new Response(JSON.stringify({ error: 'forbidden' }), { status: 403, headers: { ...cors, 'Content-Type': 'application/json' } })
    }
    if (org.billing_active) {
      return new Response(JSON.stringify({ error: 'already_active' }), { status: 400, headers: { ...cors, 'Content-Type': 'application/json' } })
    }
    // redirect URL 은 클라이언트 입력을 신뢰하지 않고 고정(오픈리다이렉트/피싱 방지)
    const success_url = 'https://imvoca.app/?org_paid=1'
    const cancel_url = 'https://imvoca.app/?org_cancel=1'

    // 2) 주 관리자(원장) 이메일
    const { data: owner } = await supabase
      .from('members')
      .select('email')
      .eq('id', org.owner_id)
      .single()
    const ownerEmail = owner?.email || undefined

    // 3) 과금 대상 수 = 원장(owner_id) 제외한 승인된 모든 구성원 (학생 + 공동관리자)
    const { count } = await supabase
      .from('members')
      .select('id', { count: 'exact', head: true })
      .eq('org_id', org_id)
      .eq('org_status', 'approved')
      .neq('id', org.owner_id)
    const quantity = Math.max(1, count ?? 1)

    // 4) Checkout 세션 — 매달 1일 청구 고정 + 첫 기간 일할 청구
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [{ price: ORG_PRICE_ID, quantity }],
      customer: org.stripe_customer_id || undefined,
      customer_email: org.stripe_customer_id ? undefined : ownerEmail,
      client_reference_id: org_id,
      metadata: { type: 'org', org_id },
      subscription_data: {
        metadata: { type: 'org', org_id },
        billing_cycle_anchor: nextKstFirstUnix(),
        proration_behavior: 'create_prorations',
      },
      success_url: success_url || 'https://imvoca.app/?org_paid=1',
      cancel_url: cancel_url || 'https://imvoca.app/?org_cancel=1',
    })

    return new Response(JSON.stringify({ url: session.url }), {
      headers: { ...cors, 'Content-Type': 'application/json' },
      status: 200,
    })
  } catch (e) {
    console.error('create-checkout error:', e)
    return new Response(JSON.stringify({ error: String((e as Error)?.message || e) }), {
      status: 500, headers: { ...cors, 'Content-Type': 'application/json' },
    })
  }
})
