-- ============================================================
-- IM VOCA — 공식 단어장 단어 '나에게만 숨기기' (2026-09-11)
-- 공식·과제 책은 모두가 공유하므로 진짜 삭제 대신 사용자별 숨김 처리.
-- 숨긴 단어는 그 사용자에게만 목록·암기·퀴즈·복습·단어 수에서 제외됨.
-- 실행: Supabase SQL Editor 에 전체 붙여넣고 Run.
-- ============================================================

create table if not exists public.voca_hidden_words (
  user_id    uuid not null,
  word_id    uuid not null,
  created_at timestamptz not null default now(),
  primary key (user_id, word_id)
);

alter table public.voca_hidden_words enable row level security;

drop policy if exists "hidden_insert_own" on public.voca_hidden_words;
create policy "hidden_insert_own" on public.voca_hidden_words
  for insert to authenticated with check (auth.uid() = user_id);

drop policy if exists "hidden_select_own" on public.voca_hidden_words;
create policy "hidden_select_own" on public.voca_hidden_words
  for select to authenticated using (auth.uid() = user_id);

drop policy if exists "hidden_delete_own" on public.voca_hidden_words;
create policy "hidden_delete_own" on public.voca_hidden_words
  for delete to authenticated using (auth.uid() = user_id);

-- 확인: select count(*) from public.voca_hidden_words;
