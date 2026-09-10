-- ============================================================
-- IM VOCA — 명예의 전당 월별 집계 뷰 (2026-09-10)
-- 목적: 명예의 전당에 월별/연도별/누적 순위를 제공.
--   voca_activity(학습·복습 활동)를 사용자×월 단위로 집계해 공개 뷰로 노출.
--   점수 = 해당 기간의 학습·복습 활동 횟수 (1회 = 1점).
-- 실행: Supabase SQL Editor 에 전체 붙여넣고 Run.
-- 보안: members_public 과 같은 패턴 — 뷰 소유자(postgres) 권한으로 실행되어
--   RLS 를 우회하되, 이름·소속·활동수만 노출 (개인 단어 내용은 노출 안 됨).
-- ============================================================

create or replace view public.hall_monthly_public as
select
  a.user_id,
  max(coalesce(m.name, ''))       as name,
  max(m.org_id::text)             as org_id,
  max(m.org_role)                 as org_role,
  max(m.org_status)               as org_status,
  substr(a.day::text, 1, 7)       as month,   -- 'YYYY-MM'
  count(*)::int                   as acts     -- 그 달의 학습+복습 활동 수
from public.voca_activity a
join public.members m on m.id = a.user_id
group by a.user_id, substr(a.day::text, 1, 7);

-- 로그인 사용자만 조회 가능 (anon 차단)
revoke all on public.hall_monthly_public from anon;
grant select on public.hall_monthly_public to authenticated;

-- 확인: 최근 달 상위 5명
-- select * from public.hall_monthly_public order by month desc, acts desc limit 5;
