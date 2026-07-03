// ============================================================
// IM VOCA — admin-set-plan (관리자 전용 프리미엄 부여/해제)
// members.plan 은 harden-members.sql 트리거로 클라이언트가 못 바꾸므로,
// 관리자가 무료 프리미엄을 주려면 service_role 로 기록하는 이 함수를 경유한다.
// 호출자 검증: JWT 이메일이 ADMIN_EMAILS 허용목록에 있어야 함.
// 배포: supabase functions deploy admin-set-plan
// env: SUPABASE_URL, SB_SERVICE_ROLE_KEY, (선택) ADMIN_EMAILS(콤마구분, 기본 koreayjk@gmail.com)
// 입력(body): { user_id, premium: boolean, months?: number(0=무기한) }
// ============================================================
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const svc = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SB_SERVICE_ROLE_KEY') ?? '',
)

const ADMIN_EMAILS = (Deno.env.get('ADMIN_EMAILS') || 'koreayjk@gmail.com')
  .split(',').map((s) => s.trim().toLowerCase()).filter(Boolean)

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
    // 1) 호출자 인증 + 관리자 검증
    const token = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '')
    if (!token) return json({ error: 'no_token' }, 401)
    const { data: ures, error: uerr } = await svc.auth.getUser(token)
    if (uerr || !ures?.user) return json({ error: 'invalid_token' }, 401)
    const email = (ures.user.email || '').toLowerCase()
    if (!ADMIN_EMAILS.includes(email)) return json({ error: 'forbidden' }, 403)

    // 2) 입력
    const { user_id, premium, months } = await req.json().catch(() => ({}))
    if (!user_id) return json({ error: 'user_id_required' }, 400)

    // 3) plan / premium_until 계산
    const upd: Record<string, unknown> = {}
    if (premium) {
      upd.plan = 'premium'
      const m = Number(months)
      if (Number.isFinite(m) && m > 0) {
        const d = new Date()
        d.setMonth(d.getMonth() + Math.floor(m))
        upd.premium_until = d.toISOString()
      } else {
        upd.premium_until = null // 무기한
      }
    } else {
      upd.plan = 'free'
      upd.premium_until = null
    }

    // 4) service_role 로 기록 (트리거의 service_role 우회 경로)
    const { data, error } = await svc.from('members').update(upd).eq('id', user_id).select('id, plan, premium_until')
    if (error) return json({ error: String(error.message || error) }, 500)
    if (!data || !data.length) return json({ error: 'member_not_found' }, 404)

    return json({ ok: true, member: data[0] })
  } catch (e) {
    console.error('admin-set-plan error:', e)
    return json({ error: String((e as Error)?.message || e) }, 500)
  }
})
