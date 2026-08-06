-- ============================================================
-- IM VOCA — 정합성 이상 데이터 정리 (2026-08)
-- voca_integrity_check() 에서 잡힌 과거 잔재를 안전하게 청소.
-- ⚠️ 삭제/수정이 포함됨. 아래 순서대로, 한 블록씩 실행 권장.
--    (삭제 대상은 전부 '고아·중복' 등 무의미한 행이라 학습 데이터 손실 없음)
-- 실행 후: select * from public.voca_integrity_check() order by issues desc; 로 0 확인.
-- ============================================================

-- ── STEP 1. 고아 복습 삭제 (94) — 존재하지 않는 책을 가리키는 복습 ──────────
-- (먼저 확인) 어떤 book_id 들인지 보기:
--   select book_id, count(*) from voca_review vr
--   where not exists (select 1 from voca_books b where b.id::text = vr.book_id)
--   group by book_id order by count(*) desc;
delete from voca_review vr
where not exists (select 1 from voca_books b where b.id::text = vr.book_id);

-- ── STEP 2. 중복 복습 정리 (148) — (학생·책·Day)별 '가장 진행된' 1행만 남김 ──
with ranked as (
  select id,
         row_number() over (
           partition by user_id, book_id, page_num
           order by (completed is true) desc,
             ( (review_2d is null)::int + (review_3d is null)::int + (review_6d is null)::int
             + (review_15d is null)::int + (review_30d is null)::int + (review_60d is null)::int ) desc,
             first_studied_at asc nulls last, id asc
         ) rn
  from voca_review
)
delete from voca_review where id in (select id from ranked where rn > 1);

-- ── STEP 3. 재발 방지 — (user_id, book_id, page_num) 유니크 인덱스 ──────────
create unique index if not exists uq_voca_review_user_book_page
  on voca_review (user_id, book_id, page_num);

-- ── STEP 4. 순서 꼬인 복습 정규화 (94) — 완료 개수는 유지, 단계 순서만 바로잡음 ─
-- 완료(=null)한 개수 K 를 세서, 앞에서부터 K개를 완료로, 나머지는 첫 학습일 기준
-- 표준 간격(+1/+2/+3/+6/+15/+30일)으로 재설정 → 순서가 항상 앞에서부터 채워짐.
update voca_review vr
set review_2d  = case when s.knull >= 1 then null else date_trunc('day', s.fs) + interval '1 day'  end,
    review_3d  = case when s.knull >= 2 then null else date_trunc('day', s.fs) + interval '2 day'  end,
    review_6d  = case when s.knull >= 3 then null else date_trunc('day', s.fs) + interval '3 day'  end,
    review_15d = case when s.knull >= 4 then null else date_trunc('day', s.fs) + interval '6 day'  end,
    review_30d = case when s.knull >= 5 then null else date_trunc('day', s.fs) + interval '15 day' end,
    review_60d = case when s.knull >= 6 then null else date_trunc('day', s.fs) + interval '30 day' end
from (
  select id, first_studied_at::timestamptz as fs,
    ( (review_2d is null)::int + (review_3d is null)::int + (review_6d is null)::int
    + (review_15d is null)::int + (review_30d is null)::int + (review_60d is null)::int ) as knull
  from voca_review
  where (review_2d  is null)::int < (review_3d  is null)::int
     or (review_3d  is null)::int < (review_6d  is null)::int
     or (review_6d  is null)::int < (review_15d is null)::int
     or (review_15d is null)::int < (review_30d is null)::int
     or (review_30d is null)::int < (review_60d is null)::int
) s
where vr.id = s.id;

-- ── STEP 5. 중복 페이지 안전 병합 (7) — 단어 손실 없이 합침 ──────────────────
-- (book_id, page_num)별로 '단어 최다' 페이지를 keeper 로, 나머지 페이지의 단어 중
-- keeper 에 없는 것만 이동, 겹치는 단어는 삭제, 빈 페이지 삭제.
create temp table _dup_merge on commit drop as
with dups as (
  select book_id, page_num from voca_pages group by book_id, page_num having count(*) > 1
),
ranked as (
  select p.id, p.book_id, p.page_num,
    row_number() over (partition by p.book_id, p.page_num
      order by (select count(*) from voca_words w where w.page_id = p.id) desc, p.id) rn
  from voca_pages p join dups d on d.book_id = p.book_id and d.page_num = p.page_num
)
select r.id as lose_id, k.id as keep_id
from ranked r
join ranked k on k.book_id = r.book_id and k.page_num = r.page_num and k.rn = 1
where r.rn > 1;

update voca_words w set page_id = m.keep_id
from _dup_merge m
where w.page_id = m.lose_id
  and not exists (select 1 from voca_words w2
                  where w2.page_id = m.keep_id and lower(trim(w2.en)) = lower(trim(w.en)));
delete from voca_words w using _dup_merge m where w.page_id = m.lose_id;
delete from voca_pages p using _dup_merge m where p.id = m.lose_id;

-- ── STEP 6. 빈 페이지 삭제 (5) — 단어가 0개인 페이지 ─────────────────────────
delete from voca_pages p
where not exists (select 1 from voca_words w where w.page_id = p.id);

-- ── STEP 7. 단체학생 활동 org_id 백필 (1) ─────────────────────────────────
update voca_activity a
set org_id = m.org_id
from members m
where a.user_id = m.id and a.org_id is null and m.org_id is not null;

-- ── STEP 8. 고아 배정 비활성화 (1) — 삭제 대신 비활성(이력 보존) ────────────
update voca_assignments a
set active = false
where a.active and not exists (select 1 from voca_books b where b.id::text = a.book_id::text);

-- ── 확인 ──────────────────────────────────────────────────────────────────
-- select * from public.voca_integrity_check() order by issues desc;   -- 전부 0 이면 완료
