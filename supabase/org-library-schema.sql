-- ============================================================
-- IM VOCA — 단체 공유 라이브러리 (관리자 간 단어장 열람)
-- 목적: 단체장(주 관리자)과 공동관리자가 서로가 만든 단어장을 보고,
--       학생에게 배정할 수 있게 함. 학생은 여전히 접근 불가(배정 경유만).
-- 방식: voca_books/pages/words 에 "같은 단체의 승인된 owner 끼리 읽기" SELECT 정책 추가.
--       (기존 본인 책 정책 + 공식책 정책과 OR 로 합쳐짐. 학생은 role=student 라 해당 안 됨)
-- 적용: Supabase SQL Editor 에서 이 파일 전체 실행.
-- 전제: assignments-schema.sql / official-books.sql 이 이미 적용돼 있어야 함.
-- ============================================================

-- 1) 호출자(승인된 owner)가 p_owner(같은 단체의 owner)의 책을 볼 수 있는지 --------
create or replace function public._voca_admin_sees_owner(p_owner uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (
    select 1
    from members me
    join members bo on bo.org_id = me.org_id
    where me.id = auth.uid()
      and me.org_role = 'owner' and me.org_status = 'approved'   -- 나: 승인된 관리자
      and bo.id = p_owner and bo.org_role = 'owner'              -- 책 주인: 같은 단체 관리자
  );
$$;

-- 페이지/단어 정책용: 책 소유자 기준으로 판정 (재귀 방지 SECURITY DEFINER)
create or replace function public._voca_book_admin_visible(p_book uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select public._voca_admin_sees_owner((select user_id from voca_books where id = p_book));
$$;
create or replace function public._voca_page_admin_visible(p_page uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select public._voca_book_admin_visible((select book_id from voca_pages where id = p_page));
$$;

grant execute on function public._voca_admin_sees_owner(uuid)   to authenticated;
grant execute on function public._voca_book_admin_visible(uuid) to authenticated;
grant execute on function public._voca_page_admin_visible(uuid) to authenticated;

-- 2) 읽기 정책 (기존 본인/공식책 정책과 OR 로 합쳐짐) ------------------
drop policy if exists books_org_admin_read on voca_books;
create policy books_org_admin_read on voca_books
  for select using (public._voca_admin_sees_owner(user_id));

drop policy if exists pages_org_admin_read on voca_pages;
create policy pages_org_admin_read on voca_pages
  for select using (public._voca_book_admin_visible(book_id));

drop policy if exists words_org_admin_read on voca_words;
create policy words_org_admin_read on voca_words
  for select using (public._voca_page_admin_visible(page_id));

-- ============================================================
-- 참고 / 보안:
--  • 이 정책은 SELECT(읽기) 전용. 쓰기(수정/삭제)는 기존 본인 소유 정책만 → 남의 책 편집 불가.
--    앱에서도 _orgLib 책은 읽기전용(_readonly)으로 표시.
--  • 학생(org_role='student')은 _voca_admin_sees_owner 가 false → 다른 사람 책 못 봄(기존과 동일).
--    학생이 단체장 책을 보는 유일한 경로는 배정(assignments-for-student, service_role)뿐.
--  • 배정된 책의 무료/유료 잠금(무료 학원=Day1만, 결제 학원=전체)은 앱(클라이언트)에서 처리.
--
-- 되돌리기:
--   drop policy if exists books_org_admin_read on voca_books;
--   drop policy if exists pages_org_admin_read on voca_pages;
--   drop policy if exists words_org_admin_read on voca_words;
--   drop function if exists public._voca_page_admin_visible(uuid);
--   drop function if exists public._voca_book_admin_visible(uuid);
--   drop function if exists public._voca_admin_sees_owner(uuid);
-- ============================================================
