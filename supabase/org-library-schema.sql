-- ============================================================
-- ⚠️ DEPRECATED / 폐기됨 — 이 파일의 정책을 적용했다면 아래 "롤백"을 실행해 제거하세요.
--
-- 원래 목적: 단체장·공동관리자가 서로가 만든 개인 단어장을 열람·배정.
-- 폐기 사유:
--   1) 실제 요구사항은 "개인 책 공유"가 아니라 "공식 단어장(수능/중등/토익)을
--      단체 관리자가 보는 것"이었음 → 앱에서 개인책 공유 기능 제거함.
--   2) 이 RLS 정책(pages_org_admin_read / words_org_admin_read 등)이 남아 있으면,
--      승인된 owner 가 공식책을 pages/words embed 로 읽을 때 모든 행마다 평가되면서
--      voca_books 조회가 500 에러 → "단체 관리자에게만 공식책이 안 보이는" 버그를 유발함.
--
-- ✅ 해야 할 일: 아래 "롤백" 블록을 Supabase SQL Editor 에서 실행해 정책·함수를 제거하세요.
--    (공식책 읽기는 official-books.sql 의 books/pages/words_official_read 정책으로 정상 동작)
-- ============================================================

-- ── 롤백 (이것만 실행) ──────────────────────────────────────
drop policy if exists books_org_admin_read on voca_books;
drop policy if exists pages_org_admin_read on voca_pages;
drop policy if exists words_org_admin_read on voca_words;
drop function if exists public._voca_page_admin_visible(uuid);
drop function if exists public._voca_book_admin_visible(uuid);
drop function if exists public._voca_admin_sees_owner(uuid);
-- ============================================================
