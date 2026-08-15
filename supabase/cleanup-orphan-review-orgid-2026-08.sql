-- ============================================================
-- IM VOCA — 정합성 정리 (2026-08-15)
-- 대상 2건만 집중 처리:
--   · 고아 복습(책 없음)         1건  [high]
--   · 단체학생 활동 org_id 누락    6건  [low]
-- 실행: Supabase SQL Editor 에 이 파일 전체 붙여넣고 실행(Run).
--   삭제 대상은 '존재하지 않는 책을 가리키는 무의미한 복습 행'뿐이라 학습 데이터 손실 없음.
-- 타입 주의: voca_review.book_id / page_num = TEXT, voca_books.id = UUID.
-- ============================================================

-- ── (선택) 실행 전 확인 — 지금 몇 건인지 ────────────────────────────────
select '실행 전' as when_,
  (select count(*) from voca_review vr
     where not exists (select 1 from voca_books b where b.id::text = vr.book_id)) as orphan_reviews,
  (select count(*) from voca_activity a
     where a.org_id is null
       and exists (select 1 from members m where m.id = a.user_id and m.org_id is not null)) as missing_org_id;

-- ── (선택) 어떤 행인지 미리 보기 ────────────────────────────────────────
-- 고아 복습이 가리키는 book_id 들:
--   select vr.user_id, vr.book_id, vr.page_num
--   from voca_review vr
--   where not exists (select 1 from voca_books b where b.id::text = vr.book_id);
-- org_id 누락 활동 행:
--   select a.id, a.user_id, m.org_id
--   from voca_activity a join members m on m.id = a.user_id
--   where a.org_id is null and m.org_id is not null;

begin;

-- ── STEP 1. 고아 복습 삭제 — 존재하지 않는 책을 가리키는 복습 행 제거 ──────
delete from voca_review vr
where not exists (select 1 from voca_books b where b.id::text = vr.book_id);

-- ── STEP 2. 단체학생 활동 org_id 백필 — 소속(members.org_id)으로 채움 ──────
update voca_activity a
set org_id = m.org_id
from members m
where a.user_id = m.id
  and a.org_id is null
  and m.org_id is not null;

commit;

-- ── 실행 후 확인 — 둘 다 0 이어야 완료 ──────────────────────────────────
select '실행 후' as when_,
  (select count(*) from voca_review vr
     where not exists (select 1 from voca_books b where b.id::text = vr.book_id)) as orphan_reviews,
  (select count(*) from voca_activity a
     where a.org_id is null
       and exists (select 1 from members m where m.id = a.user_id and m.org_id is not null)) as missing_org_id;

-- 전체 정합성 재점검(있으면):
--   select * from public.voca_integrity_check() order by issues desc;
