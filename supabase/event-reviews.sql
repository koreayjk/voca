-- ============================================================
-- IM VOCA — 사용후기 이벤트 (voca_reviews)
-- 목적: 학생/사용자가 후기(글)와 영상 링크를 남기고, 관리자가 1·2·3등을 선정.
--       앱의 🎉 이벤트 화면에서 작성/열람/선정이 모두 이뤄짐.
-- 적용: Supabase SQL Editor 에서 이 파일 전체 실행. (한 번만)
-- 주의: 복습표 voca_review 와 이름이 다름(voca_reviewS). 충돌 없음.
-- ============================================================

create table if not exists public.voca_reviews (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  user_id     uuid,               -- 작성자 (auth.uid())
  user_name   text,               -- 표시 이름
  user_email  text,               -- 연락/식별용(당첨 안내)
  org_id      uuid,               -- 소속 학원(있으면)
  body        text,               -- 후기 내용(글) — 후기 부문
  link        text,               -- 영상 링크(유튜브/인스타/틱톡) — 영상 부문
  rank        int,                -- 후기 부문 1/2/3 당첨(6개월), null=미선정
  video_rank  int,                -- 영상 부문 1/2/3 당첨(12개월), null=미선정
  published   boolean not null default true
);
-- 이미 테이블이 있던 경우에도 새 컬럼 보장 (재실행 안전)
alter table public.voca_reviews add column if not exists video_rank int;
create index if not exists idx_reviews_created on public.voca_reviews(created_at desc);
create index if not exists idx_reviews_rank    on public.voca_reviews(rank);
create index if not exists idx_reviews_vrank   on public.voca_reviews(video_rank);

alter table public.voca_reviews enable row level security;

-- 읽기: 게시된 후기는 누구나(로그인 사용자) 열람 — 모두의 후기 목록
drop policy if exists reviews_read on public.voca_reviews;
create policy reviews_read on public.voca_reviews
  for select using (published = true);

-- 작성: 로그인 사용자가 '본인 이름'으로만 (user_id = 로그인 uid)
drop policy if exists reviews_insert on public.voca_reviews;
create policy reviews_insert on public.voca_reviews
  for insert with check (auth.uid() = user_id);

-- 수정: 관리자(등수 선정) 또는 본인 (등수 partitioning 은 앱에서 처리)
drop policy if exists reviews_update on public.voca_reviews;
create policy reviews_update on public.voca_reviews
  for update using (
    (auth.jwt() ->> 'email') in ('koreayjk@gmail.com','imamerica2414@gmail.com')
    or auth.uid() = user_id
  );

-- 삭제: 관리자 또는 본인
drop policy if exists reviews_delete on public.voca_reviews;
create policy reviews_delete on public.voca_reviews
  for delete using (
    (auth.jwt() ->> 'email') in ('koreayjk@gmail.com','imamerica2414@gmail.com')
    or auth.uid() = user_id
  );

-- ============================================================
-- 관리에 쓰는 조회 (SQL Editor)
--  · 전체 후기:        select created_at, user_name, user_email, rank, video_rank, link, body from voca_reviews order by created_at desc;
--  · 후기 부문 당첨(6개월): select rank, user_name, user_email, body from voca_reviews where rank between 1 and 3 order by rank;
--  · 영상 부문 당첨(12개월): select video_rank, user_name, user_email, link from voca_reviews where video_rank between 1 and 3 order by video_rank;
-- 되돌리기: drop table if exists public.voca_reviews;
-- ============================================================
