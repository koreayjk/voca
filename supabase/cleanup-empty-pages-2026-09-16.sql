-- ============================================================
-- IM VOCA — 빈 페이지 & 빈 페이지 복습 정리 (2026-09-16)
--
-- 정합성 점검이 잡은 것:
--   · 빈 페이지(단어 0)        1건 — 페이지는 만들어졌는데 단어 저장이 중단된 잔재
--   · 빈 페이지 복습(단어 0)   1건 — 그 페이지를 가리키는 복습 → 열면 "0개 단어라
--                                     외울 수 없음" 이 뜨고 영영 안 없어진다
--
-- ⚠️ 순서가 중요하다. 복습을 먼저 지워야 한다 — 페이지를 먼저 지우면 복습이
--    '가리키는 페이지가 없는' 상태가 되어 이 쿼리로는 더 이상 찾을 수 없다.
--
-- 실행: Supabase SQL Editor 에서 ①②로 확인 → ③④로 삭제 → ⑤로 검증
-- ============================================================

-- ── ① 확인: 단어가 0개인 페이지 ─────────────────────────────────
select p.id, p.page_num, p.created_at, b.title as book_title, b.user_id
from voca_pages p
join voca_books b on b.id = p.book_id
where not exists (select 1 from voca_words w where w.page_id = p.id)
order by p.created_at;

-- ── ② 확인: 그 페이지를 가리키는 복습 ───────────────────────────
-- voca_review.book_id 는 text, voca_pages.book_id 는 uuid 라 양쪽을 text 로 맞춘다.
-- (::uuid 로 캐스팅하면 uuid 가 아닌 값이 섞여 있을 때 쿼리 전체가 죽는다)
--
-- ⚠️ 단순 join 으로 '단어 0인 페이지'에 붙이면 안 된다. 같은 Day 에 중복 페이지가
--    있고 그중 하나에만 단어가 있으면 학습이 가능한데, join 은 빈 쪽에도 붙어서
--    멀쩡한 복습까지 대상으로 잡는다. voca_integrity_check() 의 11번과 같은 기준
--    — '단어가 있는 페이지가 하나도 없을 때'만 — 을 쓴다.
select vr.id, vr.user_id, vr.book_id, vr.page_num, vr.completed, vr.first_studied_at
from voca_review vr
where exists (select 1 from voca_pages p
              where p.book_id::text = vr.book_id and p.page_num = vr.page_num)
  and not exists (select 1 from voca_pages p2
              where p2.book_id::text = vr.book_id and p2.page_num = vr.page_num
                and exists (select 1 from voca_words w2 where w2.page_id = p2.id));

-- ── ③ 삭제: 빈 페이지 복습 ──────────────────────────────────────
-- 단어가 0개면 학습도 복습도 불가능한 유령 행이다. 지워도 학습 기록 손실이 없다.
delete from voca_review vr
where exists (select 1 from voca_pages p
              where p.book_id::text = vr.book_id and p.page_num = vr.page_num)
  and not exists (select 1 from voca_pages p2
              where p2.book_id::text = vr.book_id and p2.page_num = vr.page_num
                and exists (select 1 from voca_words w2 where w2.page_id = p2.id));

-- ── ④ 삭제: 빈 페이지 ───────────────────────────────────────────
-- 만든 지 1일이 지난 것만. 지금 막 저장 중인(단어가 아직 안 올라온) 페이지를 보호한다.
delete from voca_pages p
where not exists (select 1 from voca_words w where w.page_id = p.id)
  and p.created_at < now() - interval '1 day';

-- ── ⑤ 검증 ─────────────────────────────────────────────────────
select * from public.voca_integrity_check() order by issues desc;
-- '빈 페이지(단어 0)' 와 '빈 페이지 복습(단어 0)' 이 0 이면 완료.
