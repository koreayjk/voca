// ============================================================
// IM VOCA — delete-account (회원 탈퇴)
// 본인 JWT로 호출 → 그 사용자의 모든 데이터 삭제 + Stripe 구독 해지 + auth 계정 삭제.
// 앱스토어 요건: 애플은 앱 내 '계정 삭제' 기능을 의무화(2022~).
// 배포: supabase functions deploy delete-account
// 필요한 env: SUPABASE_URL, SB_SERVICE_ROLE_KEY, STRIPE_SECRET_KEY(선택 — 없으면 구독 해지 생략)
// 응답: 200 {ok:true} · 409 {error:'org_has_members'} (다른 멤버가 있는 단체의 owner)
// ============================================================
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

const svc = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SB_SERVICE_ROLE_KEY') ?? '',
)

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, 'Content-Type': 'application/json' },
  })
}

// in-리스트 삭제를 100개씩 끊어서 (URL 길이 제한 회피)
async function delIn(table: string, col: string, ids: string[]) {
  for (let i = 0; i < ids.length; i += 100) {
    await svc.from(table).delete().in(col, ids.slice(i, i + 100))
  }
}
// 실패해도 전체 흐름을 막지 않는 삭제 (테이블/컬럼이 없어도 무시)
async function tryDel(table: string, col: string, val: string) {
  try { await svc.from(table).delete().eq(col, val) } catch (_) {}
}

async function cancelStripe(customerId: string) {
  const key = Deno.env.get('STRIPE_SECRET_KEY')
  if (!key || !customerId) return
  try {
    const res = await fetch(`https://api.stripe.com/v1/subscriptions?customer=${customerId}&status=active&limit=10`, {
      headers: { Authorization: `Bearer ${key}` },
    })
    const data = await res.json()
    for (const sub of data?.data ?? []) {
      await fetch(`https://api.stripe.com/v1/subscriptions/${sub.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${key}` },
      })
    }
  } catch (_) { /* 구독 해지 실패는 탈퇴를 막지 않음 — 콘솔에서 수동 처리 가능 */ }
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })
  if (req.method !== 'POST') return json({ error: 'method' }, 405)

  // 1) 호출자 확인 (본인만 탈퇴 가능)
  const token = (req.headers.get('authorization') ?? '').replace(/^Bearer\s+/i, '')
  const { data: userData, error: authErr } = await svc.auth.getUser(token)
  const user = userData?.user
  if (authErr || !user) return json({ error: 'unauthorized' }, 401)
  const uid = user.id

  // 2) 단체 owner 가드: 내 단체에 다른 승인 멤버가 있으면 탈퇴 불가 (단체 먼저 정리)
  const { data: myOrgs } = await svc.from('orgs').select('id, stripe_customer_id').eq('owner_id', uid)
  for (const org of myOrgs ?? []) {
    const { count } = await svc.from('members')
      .select('id', { count: 'exact', head: true })
      .eq('org_id', org.id).neq('id', uid).eq('org_status', 'approved')
    if ((count ?? 0) > 0) return json({ error: 'org_has_members' }, 409)
  }

  // 3) Stripe 구독 해지 (개인 + 1인 단체)
  const { data: meRow } = await svc.from('members').select('stripe_customer_id').eq('id', uid).maybeSingle()
  await cancelStripe(meRow?.stripe_customer_id ?? '')
  for (const org of myOrgs ?? []) await cancelStripe(org.stripe_customer_id ?? '')

  // 4) 1인 단체 정리 (다른 멤버 없음이 위에서 보장됨)
  for (const org of myOrgs ?? []) {
    const { data: asg } = await svc.from('voca_assignments').select('id').eq('org_id', org.id)
    await delIn('voca_assignment_students', 'assignment_id', (asg ?? []).map((a: { id: string }) => a.id))
    await tryDel('voca_assignments', 'org_id', org.id)
    await tryDel('voca_tests', 'org_id', org.id)        // voca_test_results 는 FK cascade
    await tryDel('demo_links', 'org_id', org.id)
    await tryDel('orgs', 'id', org.id)
  }

  // 5) 내 책 → 페이지 → 단어 (FK 순서대로)
  const { data: myBooks } = await svc.from('voca_books').select('id').eq('user_id', uid)
  const bookIds = (myBooks ?? []).map((b: { id: string }) => b.id)
  if (bookIds.length) {
    const pageIds: string[] = []
    for (let i = 0; i < bookIds.length; i += 50) {
      const { data: pgs } = await svc.from('voca_pages').select('id').in('book_id', bookIds.slice(i, i + 50))
      for (const p of pgs ?? []) pageIds.push(p.id)
    }
    await delIn('voca_words', 'page_id', pageIds)
    await delIn('voca_pages', 'book_id', bookIds)
    await delIn('voca_books', 'id', bookIds)
  }

  // 6) 사용자별 데이터
  for (const [table, col] of [
    ['voca_review', 'user_id'], ['voca_stats', 'user_id'], ['voca_activity', 'user_id'],
    ['voca_score_log', 'user_id'], ['voca_hidden_words', 'user_id'], ['voca_reviews', 'user_id'],
    ['voca_notice_reactions', 'user_id'], ['voca_test_results', 'user_id'],
    ['voca_assignment_students', 'student_id'], ['voca_settings', 'user_id'],
  ] as [string, string][]) await tryDel(table, col, uid)
  await tryDel('members', 'id', uid)

  // 7) 인증 계정 삭제
  const { error: delErr } = await svc.auth.admin.deleteUser(uid)
  if (delErr) return json({ error: 'auth_delete_failed', detail: delErr.message }, 500)

  return json({ ok: true })
})
