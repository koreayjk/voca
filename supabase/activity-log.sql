-- ============================================================
-- IM VOCA — 학습/복습 일별 활동 로그
-- 목적: 관리자·담당쌤이 학생별 "그날 새 단어 몇 개, 복습 몇 개 했는지"를 확인.
-- 방식: 학생이 첫 암기(퀴즈 통과) / 복습 완료할 때마다 한 줄 기록. 앱이 날짜별로 집계.
-- 적용: Supabase SQL Editor 에서 이 파일 전체 실행.
-- 전제: assignments-schema.sql 의 _voca_is_org_owner(org_id) 가 이미 있어야 함.
-- ※ 과거 기록은 없음(이 테이블 생성 이후부터 쌓임).
-- ============================================================

create table if not exists public.voca_activity (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null default auth.uid(),
  org_id     uuid,                         -- 학생의 단체(있으면). 관리자 조회용.
  book_id    uuid,
  page_num   text,
  kind       text not null,                -- 'study'(첫 암기) | 'review'(복습 완료)
  words      int  not null default 0,      -- 그 페이지 단어 수
  -- ⚠️ 이 기본값은 '클라이언트가 day 를 안 보냈을 때'의 보조값일 뿐이다.
  --    앱은 항상 사용자 현지 날짜(_todayStr())를 day 에 실어 보내므로 이 값은 적용되지 않는다.
  --    KST 로 고정돼 있으면 미국 사용자는 현지 오전 10시부터 '내일' 로 기록돼
  --    하루가 두 날짜로 쪼개지고 연속일·일별 집계가 깨진다.
  day        date not null default (now() at time zone 'Asia/Seoul')::date,
  created_at timestamptz not null default now()
);
create index if not exists idx_activity_user_day on public.voca_activity(user_id, day desc);
create index if not exists idx_activity_org_day  on public.voca_activity(org_id, day desc);

alter table public.voca_activity enable row level security;

-- 본인은 자기 활동 INSERT
drop policy if exists activity_insert_self on public.voca_activity;
create policy activity_insert_self on public.voca_activity
  for insert with check (user_id = auth.uid());

-- 본인 조회 + 같은 org 승인 owner(주·공동) 조회
drop policy if exists activity_select on public.voca_activity;
create policy activity_select on public.voca_activity
  for select using (
    user_id = auth.uid()
    or (org_id is not null and public._voca_is_org_owner(org_id))
  );
