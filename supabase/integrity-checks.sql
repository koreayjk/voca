-- ============================================================
-- IM VOCA — 데이터 정합성 자동 점검
-- 목적: 지금까지 겪은 버그 유형(중복 복습·순서 꼬임·중복 페이지·고아 복습 등)을
--       데이터 레벨에서 미리 발견. 한 번의 쿼리로 전부 카운트.
-- 적용: Supabase SQL Editor 에서 이 파일 전체 실행.
-- 전제: 자동 기록(리포트)은 error-log.sql 의 voca_errors 테이블이 있어야 함.
-- 타입 주의: voca_review.book_id / page_num 은 TEXT, voca_books.id 는 UUID.
-- ============================================================

-- ── 한 방 점검 함수: 모든 검사 항목의 이상 건수를 표로 반환 ──────────────
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
$$;
grant execute on function public.voca_integrity_check() to authenticated, service_role;

-- ── 매일 자동 기록: 이상(>0)만 voca_errors 에 남겨 1단계 모니터링과 통합 ──
create or replace function public.voca_integrity_report()
returns integer language plpgsql security definer set search_path = public as $$
declare n int;
begin
  insert into voca_errors(kind, context, message, detail)
  select 'integrity', check_name, note,
         jsonb_build_object('issues', issues, 'severity', severity)
  from voca_integrity_check()
  where issues > 0;
  get diagnostics n = row_count;
  return n;
end $$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    if exists (select 1 from cron.job where jobname = 'voca-integrity-daily') then
      perform cron.unschedule('voca-integrity-daily');
    end if;
    -- 매일 03:30 KST (18:30 UTC)
    perform cron.schedule('voca-integrity-daily', '30 18 * * *',
      $cron$ select public.voca_integrity_report(); $cron$);
  end if;
end $$;

-- ============================================================
-- ▶ 지금 바로 전체 점검 (제일 자주 쓰는 것):
--     select * from public.voca_integrity_check() order by issues desc;
--
-- ── 이상이 잡혔을 때 '어느 행인지' 파고드는 상세 쿼리들 ──────────────
--
-- (1) 중복 복습 목록
--   select user_id, book_id, page_num, count(*)
--   from voca_review group by user_id, book_id, page_num having count(*)>1;
--
-- (2) 순서 꼬인 복습 목록
--   select user_id, book_id, page_num, review_2d, review_3d, review_6d,
--          review_15d, review_30d, review_60d
--   from voca_review where
--        (review_2d  is null)::int < (review_3d  is null)::int
--     or (review_3d  is null)::int < (review_6d  is null)::int
--     or (review_6d  is null)::int < (review_15d is null)::int
--     or (review_15d is null)::int < (review_30d is null)::int
--     or (review_30d is null)::int < (review_60d is null)::int;
--
-- (3) 중복 페이지 목록
--   select b.title, p.page_num, count(*)
--   from voca_pages p join voca_books b on b.id=p.book_id
--   group by b.title, p.page_num having count(*)>1 order by count(*) desc;
--
-- (5) 고아 복습 목록 (어떤 책 id 를 가리키는지)
--   select vr.user_id, vr.book_id, vr.page_num
--   from voca_review vr
--   where not exists (select 1 from voca_books b where b.id::text = vr.book_id);
--
-- 되돌리기:
--   select cron.unschedule('voca-integrity-daily');
--   drop function if exists public.voca_integrity_report();
--   drop function if exists public.voca_integrity_check();
-- ============================================================
