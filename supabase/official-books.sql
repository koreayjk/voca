-- ============================================================
-- IM VOCA — 공식 단어장(Official Books) 지원
-- voca_books 에 is_official 플래그 + 누구나 읽기 가능한 RLS.
-- Supabase SQL 에디터에서 실행하세요. (시드는 tools/seed_official.py 로)
-- ============================================================

-- 1) 플래그 컬럼 -------------------------------------------------
alter table voca_books add column if not exists is_official boolean not null default false;
create index if not exists idx_books_official on voca_books(is_official) where is_official;

-- 2) 공식책 여부 헬퍼 (RLS 서브쿼리 재귀 방지용 SECURITY DEFINER) -----
create or replace function public._voca_book_is_official(p_book uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (select 1 from voca_books where id = p_book and is_official = true);
$$;
create or replace function public._voca_page_is_official(p_page uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (
    select 1 from voca_pages pg join voca_books b on b.id = pg.book_id
    where pg.id = p_page and b.is_official = true
  );
$$;
grant execute on function public._voca_book_is_official(uuid) to authenticated, anon;
grant execute on function public._voca_page_is_official(uuid) to authenticated, anon;

-- 3) 읽기 정책(기존 user_id 정책과 OR 로 합쳐짐 = 본인 책 + 공식책) -----
drop policy if exists books_official_read on voca_books;
create policy books_official_read on voca_books
  for select using (is_official = true);

drop policy if exists pages_official_read on voca_pages;
create policy pages_official_read on voca_pages
  for select using (public._voca_book_is_official(book_id));

drop policy if exists words_official_read on voca_words;
create policy words_official_read on voca_words
  for select using (public._voca_page_is_official(page_id));

-- 참고:
--  - 공식책은 읽기 전용. 쓰기(수정/삭제)는 기존 owner 정책만 허용 → 일반 사용자는 불가.
--  - 교사 배정(voca_assignments.book_id) 은 공식책 uuid 를 그대로 참조하면 됨
--    (assignments-for-student / org-report Edge Function 수정 불필요).
--  - 무료/유료 잠금은 앱(클라이언트)에서 Day1 만 열고 나머지 잠금 처리.
