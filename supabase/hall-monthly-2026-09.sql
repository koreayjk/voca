-- ============================================================
-- IM VOCA — 명예의 전당 점수 일지 + 월별 집계 뷰 v5 (2026-09-10)
-- 구조:
--   · voca_score_log: 오늘부터 점수를 줄 때마다 (누가·언제·몇 점) 기록 → 이후 월별은 1점 단위 정확
--   · 과거(일지 이전): 원본 총점수에서 일지 합을 뺀 나머지를, "첫 일지 이전 활동" 비율로 배분 (기존 방식 유지)
--   · 사용자별: 월별 합 = 연도별 = 전체 누적(원본 perfect_reviews) 일치
-- 실행: Supabase SQL Editor 에 전체 붙여넣고 Run. (v4 실행했어도 그대로 실행 — drop 후 재생성)
-- ============================================================

-- ── 1. 점수 일지 테이블 ─────────────────────────────────────────
create table if not exists public.voca_score_log (
  id         bigint generated always as identity primary key,
  user_id    uuid not null,
  score      int  not null check (score > 0),
  day        date not null default ((now() at time zone 'Asia/Seoul')::date),
  created_at timestamptz not null default now()
);
create index if not exists voca_score_log_user_day on public.voca_score_log (user_id, day);

alter table public.voca_score_log enable row level security;
drop policy if exists "score_log_insert_own" on public.voca_score_log;
create policy "score_log_insert_own" on public.voca_score_log
  for insert to authenticated with check (auth.uid() = user_id);
drop policy if exists "score_log_select_own" on public.voca_score_log;
create policy "score_log_select_own" on public.voca_score_log
  for select to authenticated using (auth.uid() = user_id);

-- ── 2. 월별 집계 뷰 v5 ─────────────────────────────────────────
drop view if exists public.hall_monthly_public;

create view public.hall_monthly_public as
with first_log as (
  select user_id, min(day)::text as fday from public.voca_score_log group by user_id
),
page_scores as (
  select p.book_id::text as book_id, p.page_num, max(sub.score) as score
  from voca_pages p
  join (
    select w.page_id,
           sum(case w.level when 'C2' then 5 when 'C1' then 4 when 'B2' then 3 when 'B1' then 2 else 1 end)::int as score
    from voca_words w group by w.page_id
  ) sub on sub.page_id = p.id
  group by p.book_id::text, p.page_num
),
acts as (
  select a.user_id, substr(a.day::text,1,7) as month,
         substr(a.day::text,1,10) as day, a.kind,
         a.book_id::text as book_id, a.page_num,
         row_number() over (partition by a.user_id, a.book_id::text, a.page_num, a.kind
                            order by a.day) as rn
  from voca_activity a
),
raw_pre as (
  -- 첫 일지 '이전' 활동만 배분 비율에 사용 (일지 시작 후엔 일지가 정확값이므로 중복 방지)
  select ac.user_id, ac.month,
         sum(coalesce(ps.score, 0))::int as score,
         max(ac.day) as last_day
  from acts ac
  left join first_log f on f.user_id = ac.user_id
  left join page_scores ps on ps.book_id = ac.book_id and ps.page_num = ac.page_num
  where (ac.kind = 'review' or (ac.kind = 'study' and ac.rn = 1))
    and (f.fday is null or ac.day < f.fday)
  group by ac.user_id, ac.month
),
log_m as (
  select user_id, to_char(day, 'YYYY-MM') as month,
         sum(score)::int as exact_score, max(day)::text as last_day
  from public.voca_score_log
  group by user_id, to_char(day, 'YYYY-MM')
),
merged as (
  select coalesce(r.user_id, l.user_id) as user_id,
         coalesce(r.month, l.month)     as month,
         coalesce(r.score, 0)           as score,        -- 배분 비율용(일지 이전 활동)
         coalesce(l.exact_score, 0)     as exact_score,  -- 일지 정확 점수
         greatest(coalesce(r.last_day, ''), coalesce(l.last_day, '')) as last_day
  from raw_pre r
  full outer join log_m l on l.user_id = r.user_id and l.month = r.month
)
select
  mg.user_id,
  max(coalesce(m.name, ''))  as name,
  max(m.org_id::text)        as org_id,
  max(m.org_role)            as org_role,
  max(m.org_status)          as org_status,
  mg.month,
  max(mg.score)              as score,
  max(mg.exact_score)        as exact_score,
  max(mg.last_day)           as last_day,
  max(coalesce(m.perfect_reviews, 0))::int as perfect_total
from merged mg
join public.members m on m.id = mg.user_id
group by mg.user_id, mg.month;

revoke all on public.hall_monthly_public from anon;
grant select on public.hall_monthly_public to authenticated;

-- 확인: select * from public.hall_monthly_public order by month desc, exact_score desc, score desc limit 5;
