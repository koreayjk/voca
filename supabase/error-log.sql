-- ============================================================
-- IM VOCA — 에러/실패 로깅 (조용한 실패를 눈에 보이게)
-- 목적: 복습 누락·점수 미지급 같은 "조용히 실패하던" 문제를 실제로
--       어디서 몇 건 나는지 수집해서, 스크린샷 없이도 먼저 파악·수정.
-- 적용: Supabase SQL Editor 에서 이 파일 전체 실행.
-- 성격: write-only 싱크 — 누구나 에러를 남길 수 있고, 읽기는 서버
--       (SQL Editor = service_role)만. (에러 로그엔 민감정보 안 담음)
-- ============================================================

create table if not exists public.voca_errors (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  user_id     uuid,          -- 로그인 상태면 채움
  user_email  text,          -- 식별 도움(있으면)
  org_id      uuid,          -- 단체(있으면)
  kind        text,          -- js_error | unhandled_rejection | write_fail | load_fail | custom
  context     text,          -- 어디서(함수/화면). 예: 'saveReviewSchedule', 'renderReviewPage'
  message     text,          -- 에러 메시지
  detail      jsonb,         -- 부가정보(bookId, pageNum, status 등)
  url         text,
  ua          text,          -- User-Agent (기기/브라우저 파악)
  app_version text
);
create index if not exists idx_errors_created on public.voca_errors(created_at desc);
create index if not exists idx_errors_kind    on public.voca_errors(kind, created_at desc);
create index if not exists idx_errors_user    on public.voca_errors(user_id, created_at desc);

alter table public.voca_errors enable row level security;

-- 누구나 에러를 남길 수 있음(로그인 전 에러도 잡기 위해). 읽기 정책은 없음
-- → 앱(anon/authenticated)은 INSERT만, 조회는 SQL Editor(service_role, RLS 우회)로.
drop policy if exists errors_insert_any on public.voca_errors;
create policy errors_insert_any on public.voca_errors
  for insert with check (true);

-- 관리자(koreayjk@gmail.com)만 앱 안 '상태' 대시보드에서 읽기 가능
drop policy if exists errors_admin_read on public.voca_errors;
create policy errors_admin_read on public.voca_errors
  for select using ((auth.jwt() ->> 'email') = 'koreayjk@gmail.com');

-- (선택) 30일 지난 로그 자동 정리 — pg_cron 있으면 매일 새벽 실행
do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    if exists (select 1 from cron.job where jobname = 'voca-errors-cleanup') then
      perform cron.unschedule('voca-errors-cleanup');
    end if;
    perform cron.schedule('voca-errors-cleanup', '0 18 * * *',
      $cron$ delete from public.voca_errors where created_at < now() - interval '30 days'; $cron$);
  end if;
end $$;

-- ============================================================
-- 매일 볼 조회 (SQL Editor 에서 실행)
-- ============================================================
-- ▸ 최근 24시간 에러를 종류·위치별로 집계 (제일 자주 보는 것)
--   select kind, context, count(*) c, max(created_at) last_seen,
--          count(distinct user_id) users
--   from voca_errors
--   where created_at > now() - interval '24 hours'
--   group by kind, context order by c desc;
--
-- ▸ 특정 학생의 최근 에러 (이메일로)
--   select created_at, kind, context, message, detail
--   from voca_errors where user_email = '학생이메일'
--   order by created_at desc limit 50;
--
-- ▸ 앱 버전별 에러 수 (새 배포가 에러를 줄였는지 확인)
--   select app_version, count(*) from voca_errors
--   where created_at > now() - interval '3 days'
--   group by app_version order by app_version desc;
--
-- 되돌리기: drop table if exists public.voca_errors;
-- ============================================================
