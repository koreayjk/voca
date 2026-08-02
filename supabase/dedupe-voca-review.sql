-- ============================================================
-- IM VOCA — voca_review 중복 복습 행 정리 + 재발 방지
-- 증상: 같은 단어장·같은 Day 복습 카드가 두 번(이상) 뜸.
-- 원인: 앱이 "있으면 skip, 없으면 insert" 방식이라, 암기카드 완료와
--       퀴즈 완료가 거의 동시에 등록되면 둘 다 insert → 중복 행 생성.
--       + voca_review 에 (user_id, book_id, page_num) 유니크 제약이 없었음.
-- 적용: Supabase SQL Editor 에서 이 파일을 위에서부터 순서대로 실행.
-- ============================================================

-- 1) 중복 현황 확인 (실행해서 몇 개나 겹쳤는지 눈으로 확인) -------------------
select user_id, book_id, page_num, count(*) as cnt
from public.voca_review
group by user_id, book_id, page_num
having count(*) > 1
order by cnt desc, user_id;

-- 2) 중복 제거 — (user,book,page)별로 '가장 진행된' 한 행만 남기고 삭제 -------
--    남길 우선순위:
--      (1) 완주(completed=true) 행 우선
--      (2) 완료한 복습 수(=null 로 지워진 단계 수)가 많은 행
--      (3) 먼저 학습한 행(first_studied_at 이른 것)
--      (4) 그래도 같으면 id 작은 행
with ranked as (
  select id,
         row_number() over (
           partition by user_id, book_id, page_num
           order by
             (completed is true) desc,
             ( (review_2d  is null)::int + (review_3d  is null)::int
             + (review_6d  is null)::int + (review_15d is null)::int
             + (review_30d is null)::int + (review_60d is null)::int ) desc,
             first_studied_at asc nulls last,
             id asc
         ) as rn
  from public.voca_review
)
delete from public.voca_review
where id in (select id from ranked where rn > 1);

-- 3) 재발 방지 — 유니크 인덱스 (앞으로 DB가 중복 자체를 거부) ----------------
--    (앱은 이 충돌(409)을 정상으로 처리하도록 이미 수정됨)
create unique index if not exists uq_voca_review_user_book_page
  on public.voca_review (user_id, book_id, page_num);

-- 4) 확인 — 이제 중복이 0개여야 함 -------------------------------------------
select user_id, book_id, page_num, count(*) as cnt
from public.voca_review
group by user_id, book_id, page_num
having count(*) > 1;
-- (아무 행도 안 나오면 정상)
