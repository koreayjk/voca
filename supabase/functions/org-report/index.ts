// ============================================================
// IM VOCA — org-report
// owner JWT로 호출 → 같은 org 학생들의 voca_review 를 집계해
// 학생별 "며칠차 복습" / 충실도 / 다음예정일을 파생 반환.
// 배포: supabase functions deploy org-report
// 필요한 env: SUPABASE_URL, SB_SERVICE_ROLE_KEY
// 입력(body): { org_id, assignment_id?, student_id? }
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

// 복습 단계 컬럼(이른→늦은 순)과 라벨 키 (index.html 의 step1..step30 매핑과 동일)
const STEP_COLS = [
  { col: 'review_2d',  stepKey: 'step1',  dayLabel: '1일차' },
  { col: 'review_3d',  stepKey: 'step2',  dayLabel: '2일차' },
  { col: 'review_6d',  stepKey: 'step3',  dayLabel: '3일차' },
  { col: 'review_15d', stepKey: 'step6',  dayLabel: '6일차' },
  { col: 'review_30d', stepKey: 'step15', dayLabel: '15일차' },
  { col: 'review_60d', stepKey: 'step30', dayLabel: '30일차' },
]

// 한 voca_review 행 → 파생 상태
function deriveStage(row: Record<string, unknown> | null) {
  if (!row) {
    return { exists: false, completed: false, reviewsDone: 0, nextStepKey: null, nextDayLabel: null, nextReviewDate: null, onTime: true, stageLabel: '시작 전' }
  }
  if (row.completed) {
    return { exists: true, completed: true, reviewsDone: STEP_COLS.length + 1, nextStepKey: null, nextDayLabel: null, nextReviewDate: null, onTime: row.is_perfect !== false, stageLabel: '완주 🎉' }
  }
  // null 로 지워진 단계 수 = 완료한 복습 횟수, 첫 단계 비-null = 다음 복습
  let reviewsDone = 1 // 첫 암기 = 1일차 완료로 간주
  let next: typeof STEP_COLS[number] | null = null
  let nextDate: string | null = null
  for (const s of STEP_COLS) {
    const v = row[s.col]
    if (v == null) { reviewsDone++; continue }
    next = s
    nextDate = v as string
    break
  }
  if (!next) {
    return { exists: true, completed: false, reviewsDone, nextStepKey: null, nextDayLabel: null, nextReviewDate: null, onTime: row.is_perfect !== false, stageLabel: '복습 마무리 단계' }
  }
  return {
    exists: true,
    completed: false,
    reviewsDone,
    nextStepKey: next.stepKey,
    nextDayLabel: next.dayLabel,
    nextReviewDate: nextDate,
    onTime: row.is_perfect !== false,
    stageLabel: `${next.dayLabel} 복습 중`,
  }
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })
  try {
    const authHeader = req.headers.get('Authorization') || ''
    const token = authHeader.replace(/^Bearer\s+/i, '')
    if (!token) return json({ error: 'no_token' }, 401)
    const { data: ures, error: uerr } = await svc.auth.getUser(token)
    if (uerr || !ures?.user) return json({ error: 'invalid_token' }, 401)
    const uid = ures.user.id

    const { org_id, assignment_id, student_id } = await req.json().catch(() => ({}))
    if (!org_id) return json({ error: 'org_id_required' }, 400)

    // 호출자가 그 org 의 승인된 owner 인지 검증
    const { data: me } = await svc
      .from('members')
      .select('id, org_id, org_role, org_status')
      .eq('id', uid)
      .single()
    if (!me || me.org_id !== org_id || me.org_role !== 'owner' || me.org_status !== 'approved') {
      return json({ error: 'forbidden' }, 403)
    }

    // (주/공동 관리자 모두 단체 전체 진도 열람 가능 — 위에서 org owner 승인 검증 완료)

    // 대상 배정 결정
    let assignQuery = svc
      .from('voca_assignments')
      .select('id, book_id, page_num, title, due_date, target_type, active')
      .eq('org_id', org_id)
      .eq('active', true)
    if (assignment_id) assignQuery = assignQuery.eq('id', assignment_id)
    const { data: assigns } = await assignQuery
    const assignments = assigns || []

    // 대상 학생들
    let stuQuery = svc
      .from('members')
      .select('id, name, email, teacher_id')
      .eq('org_id', org_id)
      .eq('org_role', 'student')
      .eq('org_status', 'approved')
    // 공동 관리자도 단체 전체 학생 진도를 볼 수 있음(주 관리자와 동일). 특정 학생만 보려면 student_id.
    if (student_id) stuQuery = stuQuery.eq('id', student_id)
    const { data: students } = await stuQuery
    const studentList = students || []

    // '지정(selected)' 배정의 대상 학생 링크 → 그 배정은 대상 학생에게만 표시
    const selIds = assignments.filter((a) => a.target_type === 'selected').map((a) => a.id)
    const linkMap: Record<string, Set<string>> = {}
    if (selIds.length) {
      const { data: links } = await svc
        .from('voca_assignment_students')
        .select('assignment_id, student_id')
        .in('assignment_id', selIds)
      for (const l of (links || [])) {
        (linkMap[l.assignment_id] ||= new Set<string>()).add(l.student_id as string)
      }
    }

    // 관련 voca_review 한 번에 로드 (학생들 × 배정 book_id)
    const studentIds = studentList.map((s) => s.id)
    const bookIds = [...new Set(assignments.map((a) => a.book_id))]
    let reviews: Record<string, unknown>[] = []
    if (studentIds.length && bookIds.length) {
      const { data: rv } = await svc
        .from('voca_review')
        .select('user_id, book_id, page_num, completed, is_perfect, first_studied_at, last_reviewed_at, review_2d, review_3d, review_6d, review_15d, review_30d, review_60d')
        .in('user_id', studentIds)
        .in('book_id', bookIds)
      reviews = rv || []
    }

    // 배정별 × 학생별 리포트 구성
    const report = assignments.map((a) => {
      // '지정' 배정은 대상 학생에게만. '전체'는 모두.
      const targeted = a.target_type === 'selected' ? (linkMap[a.id] || new Set<string>()) : null
      const rows = studentList.filter((stu) => targeted === null || targeted.has(stu.id)).map((stu) => {
        // 해당 학생의 (book_id [, page_num]) review 행 찾기
        const matches = reviews.filter((r) =>
          r.user_id === stu.id &&
          r.book_id === a.book_id &&
          (a.page_num == null || String(r.page_num) === String(a.page_num))
        )
        // 책 전체 배정이면 여러 페이지가 있을 수 있음 → 가장 진행이 앞선 행 기준
        // (완주 > 진행 > 없음). 간단히: 완료 행 우선, 아니면 reviewsDone 최대.
        let chosen: Record<string, unknown> | null = null
        if (matches.length) {
          chosen = matches.reduce((best, cur) => {
            const b = deriveStage(best)
            const c = deriveStage(cur)
            const score = (x: ReturnType<typeof deriveStage>) => (x.completed ? 100 : x.reviewsDone)
            return score(c) > score(b) ? cur : best
          })
        }
        const st = deriveStage(chosen)
        // 이 학생의 이 과제 관련 행 중 가장 최근 복습 시각(오늘 활동 판별용)
        const lastReviewedAt = matches.reduce((mx: string | null, r) => {
          const v = r.last_reviewed_at as string | null
          return (v && (!mx || v > mx)) ? v : mx
        }, null as string | null)
        return {
          student_id: stu.id,
          name: stu.name || stu.email || '학생',
          pagesStudied: matches.length,
          lastReviewedAt,
          ...st,
        }
      })
      return {
        assignment_id: a.id,
        book_id: a.book_id,
        page_num: a.page_num,
        title: a.title,
        due_date: a.due_date,
        target_type: a.target_type,
        students: rows,
      }
    }).filter((a) => a.students.length > 0) // 대상 학생 없는 배정(지정에서 전원 제외 등)은 숨김

    return json({ org_id, report })
  } catch (e) {
    return json({ error: String((e as Error)?.message || e) }, 500)
  }
})
