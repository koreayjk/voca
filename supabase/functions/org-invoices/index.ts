// ============================================================
// IM VOCA — org-invoices (학원/단체 결제 내역 조회)
// 단체 관리자(owner) JWT로 호출 → 그 단체의 Stripe 고객 실제 청구서 목록 반환.
// 매월 1일 결제될 때마다 Stripe 가 청구서를 자동 생성하므로, 여기서 그대로 읽어와
// 결제 화면에 리스트로 보여준다. (읽기 전용 — 아무 상태도 바꾸지 않음)
// 배포: supabase functions deploy org-invoices
// env: STRIPE_SECRET_KEY, SUPABASE_URL, SB_SERVICE_ROLE_KEY
// 입력(body): { org_id, limit? }
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
    const token = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '')
    if (!token) return json({ error: 'no_token' }, 401)
    const { data: ures, error: uerr } = await svc.auth.getUser(token)
    if (uerr || !ures?.user) return json({ error: 'invalid_token' }, 401)
    const uid = ures.user.id

    const { org_id, limit } = await req.json().catch(() => ({}))
    if (!org_id) return json({ error: 'org_id_required' }, 400)

    // 호출자가 그 org 의 승인된 관리자(owner)인지 검증
    const { data: me } = await svc
      .from('members').select('id, org_id, org_role, org_status')
      .eq('id', uid).single()
    if (!me || me.org_id !== org_id || me.org_role !== 'owner' || me.org_status !== 'approved') {
      return json({ error: 'forbidden' }, 403)
    }

    const { data: org } = await svc
      .from('orgs').select('id, stripe_customer_id, billing_active')
      .eq('id', org_id).single()
    if (!org) return json({ error: 'org_not_found' }, 404)
    if (!org.stripe_customer_id) return json({ invoices: [] })   // 아직 결제 시작 전

    const list = await stripe.invoices.list({
      customer: org.stripe_customer_id as string,
      limit: Math.min(Math.max(Number(limit) || 24, 1), 100),
    })

    const invoices = (list.data || []).map((inv) => ({
      id: inv.id,
      number: inv.number,
      status: inv.status,                                   // paid | open | void | uncollectible | draft
      created: inv.created,                                 // unix (초)
      paid_at: inv.status_transitions?.paid_at ?? null,
      amount_paid: inv.amount_paid,                         // cents
      amount_due: inv.amount_due,                           // cents
      currency: inv.currency,
      period_start: inv.period_start,
      period_end: inv.period_end,
      hosted_invoice_url: inv.hosted_invoice_url,           // 온라인 보기
      invoice_pdf: inv.invoice_pdf,                         // PDF 다운로드
    }))
    return json({ invoices })
  } catch (e) {
    console.error('org-invoices error:', e)
    return json({ error: String((e as Error)?.message || e) }, 500)
  }
})
