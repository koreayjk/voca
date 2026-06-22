// ============================================================
// IM VOCA — assignments-for-student
// 학생 JWT로 호출 → 본인 org 의 활성 배정 + 각 배정 책(읽기전용: pages/words) 반환
// 배포: supabase functions deploy assignments-for-student
// 필요한 env (기존 create-checkout 과 동일):
//   SUPABASE_URL, SB_SERVICE_ROLE_KEY
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

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })
  try {
    // 1) JWT 에서 호출자 식별
    const authHeader = req.headers.get('Authorization') || ''
    const token = authHeader.replace(/^Bearer\s+/i, '')
    if (!token) return json({ error: 'no_token' }, 401)
    const { data: ures, error: uerr } = await svc.auth.getUser(token)
    if (uerr || !ures?.user) return json({ error: 'invalid_token' }, 401)
    const uid = ures.user.id

    // 2) 호출자 member → org 확인 (승인된 회원만)
    const { data: me, error: meErr } = await svc
      .from('members')
      .select('id, org_id, org_role, org_status')
      .eq('id', uid)
      .single()
    if (meErr || !me || !me.org_id || me.org_status !== 'approved') {
      return json({ assignments: [], books: [] })
    }
    const orgId = me.org_id

    // 3) 활성 배정: target_type='all' 또는 본인이 selected 대상
    const { data: allAssigns, error: aErr } = await svc
      .from('voca_assignments')
      .select('id, org_id, assigned_by, book_id, page_num, title, due_date, target_type, active, created_at')
      .eq('org_id', orgId)
      .eq('active', true)
      .order('created_at', { ascending: false })
    if (aErr) return json({ error: 'assign_query_failed', detail: aErr.message }, 500)

    let assignments = allAssigns || []
    const selectedOnes = assignments.filter((a) => a.target_type === 'selected').map((a) => a.id)
    let mySelectedSet = new Set<string>()
    if (selectedOnes.length) {
      const { data: links } = await svc
        .from('voca_assignment_students')
        .select('assignment_id')
        .eq('student_id', uid)
        .in('assignment_id', selectedOnes)
      mySelectedSet = new Set((links || []).map((l) => l.assignment_id))
    }
    assignments = assignments.filter((a) => a.target_type === 'all' || mySelectedSet.has(a.id))

    if (!assignments.length) return json({ assignments: [], books: [] })

    // 4) 배정에 쓰인 book_id 들의 책+페이지+단어 (읽기전용)
    const bookIds = [...new Set(assignments.map((a) => a.book_id))]
    const { data: rawBooks, error: bErr } = await svc
      .from('voca_books')
      .select('id, user_id, title, author, color, description, cover_url, category, voca_pages(id, page_num, voca_words(id, en, ipa, base, ctx, sentence, level, is_favorite, analysis, created_at))')
      .in('id', bookIds)
    if (bErr) return json({ error: 'book_query_failed', detail: bErr.message }, 500)

    return json({ assignments, books: rawBooks || [] })
  } catch (e) {
    return json({ error: String((e as Error)?.message || e) }, 500)
  }
})
