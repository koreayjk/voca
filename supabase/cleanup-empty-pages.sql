-- ============================================================
-- IM VOCA — 빈 페이지(단어 0) 정리 (2026-09-11)
-- 원인: 페이지 생성 후 단어 저장이 네트워크 등으로 중단되면 빈 페이지가 남음.
-- 실행: Supabase SQL Editor 에서 ①로 먼저 확인 → ②로 삭제.
-- ============================================================

-- ① 미리보기: 어떤 빈 페이지가 있는지 확인
select p.id, p.page_num, p.created_at, b.title as book_title, b.user_id
from voca_pages p
join voca_books b on b.id = p.book_id
where not exists (select 1 from voca_words w where w.page_id = p.id)
order by p.created_at desc;

-- ② 정리: 만든 지 1일 지난 빈 페이지만 삭제 (지금 막 저장 중인 페이지 보호)
delete from voca_pages p
where not exists (select 1 from voca_words w where w.page_id = p.id)
  and p.created_at < now() - interval '1 day';

-- ③ (참고) write_fail 리포트 검증: 해당 사용자의 Day 1 기록이 재전송 큐로
--    실제 저장됐는지 확인 — 행이 있으면 유실 없이 자가 복구된 것
select kind, page_num, day, created_at
from voca_activity
where book_id = '3efe06ac-1858-4475-92aa-a60de6c13f62' and page_num = 'Day 1'
order by created_at desc limit 5;
