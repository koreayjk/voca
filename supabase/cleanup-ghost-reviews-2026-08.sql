-- ============================================================
-- IM VOCA — '유령 복습' 정리 (2026-08-24)
-- 증상: 복습 탭에 "추가하지 않은 페이지 · 0개 단어"가 뜨고, 시작하면
--       "단어를 불러올 수 없어요" (load_fail: review words empty).
-- 원인: 책/페이지 삭제·이름변경 시 voca_review 가 정리되지 않고 남음.
--       (앱 코드도 함께 수정됨 — deleteBook/deletePage/renamePage가 이제 복습을 정리/이관)
-- 이 SQL: ① 기존 유령 행 3종 삭제 ② 정합성 점검 함수에 페이지 단위 검사 2종 추가.
-- 실행: Supabase SQL Editor 에 전체 붙여넣고 Run.
-- 타입 주의: voca_review.book_id/page_num = TEXT, voca_books.id/voca_pages.book_id = UUID.
-- ============================================================

-- ── 실행 전 확인 ─────────────────────────────────────────────
select '실행 전' as when_,
  (select count(*) from voca_review vr
     where not exists (select 1 from voca_books b where b.id::text = vr.book_id)) as orphan_book,
  (select count(*) from voca_review vr
     where exists (select 1 from voca_books b where b.id::text = vr.book_id)
       and not exists (select 1 from voca_pages p
                       where p.book_id::text = vr.book_id and p.page_num = vr.page_num)) as orphan_page,
  (select count(*) from voca_review vr
     where exists (select 1 from voca_pages p
                   where p.book_id::text = vr.book_id and p.page_num = vr.page_num
                     and not exists (select 1 from voca_words w where w.page_id = p.id))
       and not exists (select 1 from voca_pages p2
                   where p2.book_id::text = vr.book_id and p2.page_num = vr.page_num
                     and exists (select 1 from voca_words w2 where w2.page_id = p2.id))) as empty_page;

begin;

-- ── STEP 1. 고아 복습(책 없음) 삭제 — 이번 리포트의 7건 ─────────
delete from voca_review vr
where not exists (select 1 from voca_books b where b.id::text = vr.book_id);

-- ── STEP 2. 고아 복습(페이지 없음) 삭제 — 페이지 삭제/이름변경 잔재 ──
delete from voca_review vr
where exists (select 1 from voca_books b where b.id::text = vr.book_id)
  and not exists (select 1 from voca_pages p
                  where p.book_id::text = vr.book_id and p.page_num = vr.page_num);

-- ── STEP 3. 빈 페이지 복습(단어 0) 삭제 — "Page 3 · 0개 단어" 케이스 ──
-- (같은 book+page 이름의 페이지가 여러 개면, 전부 비어있을 때만 삭제)
delete from voca_review vr
where exists (select 1 from voca_pages p
              where p.book_id::text = vr.book_id and p.page_num = vr.page_num)
  and not exists (select 1 from voca_pages p2
              where p2.book_id::text = vr.book_id and p2.page_num = vr.page_num
                and exists (select 1 from voca_words w2 where w2.page_id = p2.id));

commit;

-- ── 실행 후 확인 — 셋 다 0 이어야 완료 ──────────────────────────
select '실행 후' as when_,
  (select count(*) from voca_review vr
     where not exists (select 1 from voca_books b where b.id::text = vr.book_id)) as orphan_book,
  (select count(*) from voca_review vr
     where exists (select 1 from voca_books b where b.id::text = vr.book_id)
       and not exists (select 1 from voca_pages p
                       where p.book_id::text = vr.book_id and p.page_num = vr.page_num)) as orphan_page,
  (select count(*) from voca_review vr
     where exists (select 1 from voca_pages p
                   where p.book_id::text = vr.book_id and p.page_num = vr.page_num
                     and not exists (select 1 from voca_words w where w.page_id = p.id))
       and not exists (select 1 from voca_pages p2
                   where p2.book_id::text = vr.book_id and p2.page_num = vr.page_num
                     and exists (select 1 from voca_words w2 where w2.page_id = p2.id))) as empty_page;

-- ============================================================
-- ── STEP 4. 정합성 점검 함수 갱신: 페이지 단위 검사 2종 추가 ──
--    (매일 자동 리포트가 '유령 복습' 재발을 즉시 감지하도록)
-- ============================================================
create or replace function public.voca_integrity_check()
returns table(check_name text, severity text, issues bigint, note text)
language sql stable security definer set search_path = public as $$
  -- 1) 중복 복습 (같은 학생·책·Day 가 2행 이상)
  select '중복 복습 행'::text, 'high'::text,
    (select count(*) from (select 1 from voca_review
       group by user_id, book_id, page_num having count(*) > 1) t),
    '같은 학생·책·Day 복습이 2행 이상 (복습 두 번 뜨는 원인)'::text
  union all
  -- 2) 순서 꼬인 복습 (뒤 단계가 앞 단계보다 먼저 완료)
  select '순서 꼬인 복습', 'high',
    (select count(*) from voca_review where
        (review_2d  is null)::int < (review_3d  is null)::int
     or (review_3d  is null)::int < (review_6d  is null)::int
     or (review_6d  is null)::int < (review_15d is null)::int
     or (review_15d is null)::int < (review_30d is null)::int
     or (review_30d is null)::int < (review_60d is null)::int),
    '3일차는 됐는데 2일차가 남는 식의 순서 꼬임'
  union all
  -- 3) 중복 페이지 (같은 책·Day 페이지가 2행 이상)
  select '중복 페이지', 'medium',
    (select count(*) from (select 1 from voca_pages
       group by book_id, page_num having count(*) > 1) t),
    '같은 책·Day 페이지가 2행 이상 (복습 단어 20↔40 원인)'
  union all
  -- 4) 빈 페이지 (단어 0개)
  select '빈 페이지(단어 0)', 'medium',
    (select count(*) from voca_pages p
       where not exists (select 1 from voca_words w where w.page_id = p.id)),
    '단어가 하나도 없는 페이지'
  union all
  -- 5) 고아 복습 (가리키는 책이 존재하지 않음)
  select '고아 복습(책 없음)', 'high',
    (select count(*) from voca_review vr
       where not exists (select 1 from voca_books b where b.id::text = vr.book_id)),
    '복습이 가리키는 책이 없음 (복습이 목록에 안 뜨는 원인)'
  union all
  -- 6) 단체 학생인데 활동 로그에 org_id 누락
  select '단체학생 활동 org_id 누락', 'low',
    (select count(*) from voca_activity a
       where a.org_id is null
         and exists (select 1 from members m where m.id = a.user_id and m.org_id is not null)),
    '단체 소속 학생인데 활동에 org_id 없음 (원장 리포트에서 누락)'
  union all
  -- 7) 고아 배정 (활성 배정인데 책이 없음)
  select '고아 배정(책 없음)', 'medium',
    (select count(*) from voca_assignments a
       where a.active and not exists
         (select 1 from voca_books b where b.id::text = a.book_id::text)),
    '활성 배정이 가리키는 책이 없음'
  union all
  -- 8) 멈춘 복습 (6단계 다 완료인데 completed=false)
  select '멈춘 복습(다 됐는데 미완주)', 'low',
    (select count(*) from voca_review where completed = false
        and review_2d is null and review_3d is null and review_6d is null
        and review_15d is null and review_30d is null and review_60d is null),
    'completed 플래그만 안 켜진 행'
  union all
  -- 9) first_studied_at 없는 복습 (비정상 행)
  select '복습 first_studied_at 없음', 'low',
    (select count(*) from voca_review where first_studied_at is null),
    '첫 학습일이 비어있는 비정상 복습 행'
  union all
  -- 10) 고아 복습 (책은 있는데 페이지가 없음 — 페이지 삭제/이름변경 잔재)
  select '고아 복습(페이지 없음)', 'high',
    (select count(*) from voca_review vr
       where exists (select 1 from voca_books b where b.id::text = vr.book_id)
         and not exists (select 1 from voca_pages p
                         where p.book_id::text = vr.book_id and p.page_num = vr.page_num)),
    '복습이 가리키는 페이지가 없음 ("추가하지 않은 페이지" 유령 복습)'
  union all
  -- 11) 빈 페이지 복습 (페이지는 있는데 단어 0개)
  select '빈 페이지 복습(단어 0)', 'medium',
    (select count(*) from voca_review vr
       where exists (select 1 from voca_pages p
                     where p.book_id::text = vr.book_id and p.page_num = vr.page_num)
         and not exists (select 1 from voca_pages p2
                     where p2.book_id::text = vr.book_id and p2.page_num = vr.page_num
                       and exists (select 1 from voca_words w2 where w2.page_id = p2.id))),
    '복습 페이지에 단어가 0개 ("0개 단어라 외울 수 없음" 원인)'
$$;
grant execute on function public.voca_integrity_check() to authenticated, service_role;

-- 전체 재점검:
--   select * from public.voca_integrity_check() order by issues desc;
