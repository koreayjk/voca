-- ============================================================
-- IM VOCA — 명예의 전당 월별 집계 뷰 v2 (2026-09-10)
-- 점수 = 기존 방식 그대로 CEFR 가중 페이지 점수 (A2=1 · B1=2 · B2=3 · C1=4 · C2=5)
--   · 첫 암기(study): 페이지당 1회만 페이지 점수 적립 (앱의 _awardFirstStudyPoints 와 동일)
--   · 복습(review): 완료할 때마다 페이지 점수 적립 (앱의 updateReviewStep 와 동일)
--   voca_activity(날짜별 기록) × 페이지 단어 CEFR 점수를 SQL 에서 재계산해
--   과거 달까지 월별/연도별 순위를 복원한다.
-- 실행: Supabase SQL Editor 에 전체 붙여넣고 Run. (v1 을 이미 실행했다면 그대로 실행 — drop 후 재생성)
-- ============================================================

drop view if exists public.hall_monthly_public;

create view public.hall_monthly_public as
with page_scores as (
  -- 페이지(책×페이지번호)별 CEFR 가중 점수
  select p.book_id::text as book_id, p.page_num,
         max(sub.score) as score        -- 같은 책·번호 중복 페이지는 최대값 (합산 시 과대 방지)
  from voca_pages p
  join (
    select w.page_id,
           sum(case w.level when 'C2' then 5 when 'C1' then 4 when 'B2' then 3 when 'B1' then 2 else 1 end)::int as score
    from voca_words w group by w.page_id
  ) sub on sub.page_id = p.id
  group by p.book_id::text, p.page_num
),
acts as (
  select a.user_id, substr(a.day::text,1,7) as month, a.kind,
         a.book_id::text as book_id, a.page_num,
         row_number() over (partition by a.user_id, a.book_id::text, a.page_num, a.kind
                            order by a.day) as rn
  from voca_activity a
)
select
  ac.user_id,
  max(coalesce(m.name, ''))  as name,
  max(m.org_id::text)        as org_id,
  max(m.org_role)            as org_role,
  max(m.org_status)          as org_status,
  ac.month,                                  -- 'YYYY-MM'
  sum(coalesce(ps.score, 0))::int as score   -- 그 달에 적립된 CEFR 가중 점수
from acts ac
join public.members m on m.id = ac.user_id
left join page_scores ps
  on ps.book_id = ac.book_id and ps.page_num = ac.page_num
where ac.kind = 'review'                      -- 복습: 매번 적립
   or (ac.kind = 'study' and ac.rn = 1)       -- 첫 암기: 페이지당 1회만
group by ac.user_id, ac.month;

-- 로그인 사용자만 조회 가능 (anon 차단)
revoke all on public.hall_monthly_public from anon;
grant select on public.hall_monthly_public to authenticated;

-- 확인: 최근 달 상위 5명
-- select * from public.hall_monthly_public order by month desc, score desc limit 5;
