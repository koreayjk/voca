-- ============================================================
-- IM VOCA — Day별 테스트 점수 (voca_stats 확장)
-- 퀴즈 결과를 Day(page) 단위로 기록 + 교사(org owner)가 학생 점수 조회.
-- Supabase SQL 에디터에서 실행하세요.
-- ============================================================

-- 1) page_num 컬럼(어느 Day 테스트인지) ----------------------
alter table voca_stats add column if not exists page_num text;
create index if not exists idx_stats_user_book on voca_stats(user_id, book_id);

-- 2) 교사(같은 org 의 승인 owner)가 학생 점수 읽기 (RLS) --------
create or replace function public._voca_can_read_stats(p_user uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (
    select 1 from members stu
    join members own on own.org_id = stu.org_id
    where stu.id = p_user
      and own.id = auth.uid()
      and own.org_role = 'owner'
      and own.org_status = 'approved'
  );
$$;
grant execute on function public._voca_can_read_stats(uuid) to authenticated;

drop policy if exists stats_owner_read on voca_stats;
create policy stats_owner_read on voca_stats
  for select using (public._voca_can_read_stats(user_id));

-- 참고: 학생 본인 읽기/쓰기 정책은 기존대로 둠. 위 정책은 OR 로 합쳐져 owner 도 읽기 가능.
