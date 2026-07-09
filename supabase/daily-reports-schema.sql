-- ============================================================
-- IM VOCA — 일일 학습 리포트 (자동 스냅샷)
-- 목적: 관리자·담당쌤이 매일 밤 9시(KST) 기준으로 학생별
--       "오늘 복습 했는지 / 밀린 복습 / 과제 진행 / 개인공부"를
--       단체 페이지에서 자동으로 확인(관리자가 일일이 안 들어가도 됨).
-- 방식: pg_cron 이 매일 12:00 UTC(=21:00 KST)에 build_daily_reports() 실행 →
--       학생별 한 줄을 voca_daily_reports 에 저장(upsert). 앱은 그 스냅샷만 읽음.
-- 적용: Supabase SQL Editor 에서 이 파일 전체 실행.
--       ※ pg_cron 확장은 Dashboard → Database → Extensions 에서 'pg_cron' Enable 필요.
-- 전제: assignments-schema.sql (voca_assignments, _voca_is_org_owner) 가 이미 있어야 함.
-- ============================================================

-- 1) 복습 이벤트 시각: '오늘 복습했다' 판별용 (앱이 복습 완료 PATCH 때 기록) --------
alter table public.voca_review
  add column if not exists last_reviewed_at timestamptz;

-- 2) 일일 리포트 스냅샷 테이블 ---------------------------------------------------
create table if not exists public.voca_daily_reports (
  id            uuid primary key default gen_random_uuid(),
  org_id        uuid not null,
  student_id    uuid not null,
  teacher_id    uuid,                    -- 담당쌤(스냅샷). 담당쌤은 자기 학생만 봄
  report_date   date not null,           -- 기준 날짜(KST)
  student_name  text,
  studied_today       boolean not null default false,  -- 오늘 접속/학습 여부
  reviews_done_today  int not null default 0,           -- 오늘 완료한 복습 페이지 수
  reviews_due_today   int not null default 0,           -- 오늘 예정된 복습 수
  reviews_overdue     int not null default 0,           -- 밀린 복습(예정일 지남)
  new_words_today     int not null default 0,           -- 오늘 새로 담은 단어(누적 diff)
  assign_total    int not null default 0,   -- 이 학생에게 배정된 활성 과제 수
  assign_progress int not null default 0,   -- 그중 시작한 과제 수
  assign_done     int not null default 0,   -- 그중 완주한 과제 수
  personal_pages  int not null default 0,   -- 과제 아닌 개인공부 페이지 수
  total_words_snapshot int not null default 0,  -- 오늘 누적 단어(내일 diff용)
  streak_days     int not null default 0,   -- 연속 학습일수
  last_seen_at    timestamptz,
  created_at      timestamptz not null default now(),
  unique (org_id, student_id, report_date)
);
create index if not exists idx_daily_org_date on public.voca_daily_reports(org_id, report_date desc);

-- RLS: 같은 org 의 승인된 owner(주+공동)만 읽기. 쓰기는 서버(집계 함수)만.
alter table public.voca_daily_reports enable row level security;
drop policy if exists daily_owner_select on public.voca_daily_reports;
create policy daily_owner_select on public.voca_daily_reports
  for select using (public._voca_is_org_owner(org_id));

-- 3) 집계 함수: 하루치 학생별 리포트 계산 → upsert -------------------------------
create or replace function public.build_daily_reports(
  p_date date default (now() at time zone 'Asia/Seoul')::date
)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare n int;
begin
  with
  -- 승인된 학생(담당쌤·누적단어·최근접속 포함)
  stu as (
    select m.id as student_id, m.org_id, m.teacher_id,
           coalesce(m.name, m.email, '학생') as student_name,
           coalesce(m.total_words, 0) as total_words, m.last_seen_at
    from members m
    where m.org_role = 'student' and m.org_status = 'approved' and m.org_id is not null
  ),
  -- 학생 복습 행 + 다음 예정일(가장 이른 비-null 단계). least() 는 NULL 무시.
  rr as (
    select vr.user_id, vr.book_id, vr.page_num, coalesce(vr.completed,false) as completed,
           vr.last_reviewed_at,
           least(vr.review_2d::timestamptz, vr.review_3d::timestamptz, vr.review_6d::timestamptz,
                 vr.review_15d::timestamptz, vr.review_30d::timestamptz, vr.review_60d::timestamptz) as next_due
    from voca_review vr
    where vr.user_id in (select student_id from stu)
  ),
  -- 활성 과제
  act as (
    select a.id, a.org_id, a.book_id, a.page_num, a.target_type
    from voca_assignments a where a.active = true
  ),
  -- 학생 × 배정(대상인 것만)
  sa as (
    select s.student_id, s.org_id, a.id as assignment_id, a.book_id, a.page_num
    from stu s
    join act a on a.org_id = s.org_id
    where a.target_type = 'all'
       or exists (select 1 from voca_assignment_students x
                  where x.assignment_id = a.id and x.student_id = s.student_id)
  ),
  -- 과제별 진행(시작/완주)
  saprog as (
    select sa.student_id, sa.org_id, sa.assignment_id,
           bool_or(rr.user_id is not null) as started,
           bool_or(rr.completed)           as done
    from sa
    left join rr on rr.user_id = sa.student_id and rr.book_id = sa.book_id
                and (sa.page_num is null or rr.page_num::text = sa.page_num)
    group by sa.student_id, sa.org_id, sa.assignment_id
  ),
  assignagg as (
    select student_id, org_id,
           count(*)                          as assign_total,
           count(*) filter (where started)   as assign_progress,
           count(*) filter (where done)      as assign_done
    from saprog group by student_id, org_id
  ),
  -- 복습 집계(오늘 완료/오늘 예정/밀림)
  rvagg as (
    select s.student_id, s.org_id,
      count(*) filter (
        where rr.last_reviewed_at is not null
          and (rr.last_reviewed_at at time zone 'Asia/Seoul')::date = p_date
      ) as reviews_done_today,
      count(*) filter (
        where not rr.completed and rr.next_due is not null
          and (rr.next_due at time zone 'Asia/Seoul')::date = p_date
      ) as reviews_due_today,
      count(*) filter (
        where not rr.completed and rr.next_due is not null
          and (rr.next_due at time zone 'Asia/Seoul')::date < p_date
      ) as reviews_overdue,
      -- 개인공부: 어떤 활성 과제와도 안 맞는 복습 행 수
      count(*) filter (
        where not exists (
          select 1 from sa
          where sa.student_id = s.student_id and sa.book_id = rr.book_id
            and (sa.page_num is null or rr.page_num::text = sa.page_num)
        )
      ) as personal_pages
    from stu s
    left join rr on rr.user_id = s.student_id
    group by s.student_id, s.org_id
  ),
  -- 어제 스냅샷(누적단어 diff · streak 이어가기)
  yday as (
    select student_id, total_words_snapshot, streak_days
    from voca_daily_reports where report_date = p_date - 1
  ),
  final as (
    select
      s.org_id, s.student_id, s.teacher_id, p_date as report_date, s.student_name,
      coalesce(rv.reviews_done_today,0) as reviews_done_today,
      coalesce(rv.reviews_due_today,0)  as reviews_due_today,
      coalesce(rv.reviews_overdue,0)    as reviews_overdue,
      greatest(0, s.total_words - coalesce(y.total_words_snapshot, s.total_words)) as new_words_today,
      coalesce(ag.assign_total,0)    as assign_total,
      coalesce(ag.assign_progress,0) as assign_progress,
      coalesce(ag.assign_done,0)     as assign_done,
      coalesce(rv.personal_pages,0)  as personal_pages,
      s.total_words as total_words_snapshot,
      s.last_seen_at,
      (coalesce(rv.reviews_done_today,0) > 0
        or (s.last_seen_at is not null
            and (s.last_seen_at at time zone 'Asia/Seoul')::date = p_date)) as studied_today
    from stu s
    left join rvagg rv on rv.student_id = s.student_id
    left join assignagg ag on ag.student_id = s.student_id
    left join yday y on y.student_id = s.student_id
  )
  insert into voca_daily_reports as d (
    org_id, student_id, teacher_id, report_date, student_name,
    studied_today, reviews_done_today, reviews_due_today, reviews_overdue,
    new_words_today, assign_total, assign_progress, assign_done, personal_pages,
    total_words_snapshot, streak_days, last_seen_at
  )
  select
    f.org_id, f.student_id, f.teacher_id, f.report_date, f.student_name,
    f.studied_today, f.reviews_done_today, f.reviews_due_today, f.reviews_overdue,
    f.new_words_today, f.assign_total, f.assign_progress, f.assign_done, f.personal_pages,
    f.total_words_snapshot,
    case when f.studied_today then coalesce((select streak_days from yday where student_id=f.student_id),0) + 1
         else 0 end as streak_days,
    f.last_seen_at
  from final f
  on conflict (org_id, student_id, report_date) do update set
    teacher_id = excluded.teacher_id,
    student_name = excluded.student_name,
    studied_today = excluded.studied_today,
    reviews_done_today = excluded.reviews_done_today,
    reviews_due_today = excluded.reviews_due_today,
    reviews_overdue = excluded.reviews_overdue,
    new_words_today = excluded.new_words_today,
    assign_total = excluded.assign_total,
    assign_progress = excluded.assign_progress,
    assign_done = excluded.assign_done,
    personal_pages = excluded.personal_pages,
    total_words_snapshot = excluded.total_words_snapshot,
    streak_days = excluded.streak_days,
    last_seen_at = excluded.last_seen_at;

  get diagnostics n = row_count;
  return n;
end;
$$;

-- 4) 매일 밤 9시(KST=12:00 UTC) 자동 실행 (pg_cron) ------------------------------
--    pg_cron 확장이 켜져 있어야 함(Dashboard → Database → Extensions → pg_cron Enable).
do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    if exists (select 1 from cron.job where jobname = 'voca-daily-report') then
      perform cron.unschedule('voca-daily-report');
    end if;
    perform cron.schedule('voca-daily-report', '0 12 * * *',
      $cron$ select public.build_daily_reports(); $cron$);
  else
    raise notice 'pg_cron 미설치 — Extensions 에서 pg_cron Enable 후 이 파일을 다시 실행하세요.';
  end if;
end $$;

-- ============================================================
-- 최초 1회 지금 바로 채우고 싶으면(테스트):
--   select public.build_daily_reports();               -- 오늘(KST) 기준
--   select public.build_daily_reports(current_date-1);  -- 특정 날짜
-- 확인:
--   select report_date, student_name, studied_today, reviews_done_today,
--          reviews_overdue, assign_done, assign_total, personal_pages, streak_days
--   from voca_daily_reports order by report_date desc, reviews_overdue desc limit 50;
--
-- 되돌리기:
--   select cron.unschedule('voca-daily-report');
--   drop table if exists public.voca_daily_reports;
--   -- (last_reviewed_at 컬럼은 남겨둬도 무해)
-- ============================================================
