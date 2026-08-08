-- ============================================================
-- IM VOCA — 시험(Test) 시스템 (온라인 자동채점 + PDF 출제 공용)
-- 관리자(원장)가 배정 단어장에서 문제를 '스냅샷'으로 출제 → 온라인 응시(자동채점)
-- 및 PDF 시험지 출력에 동일한 문제 사용. 결과는 리포트/학부모 카드에 반영.
-- 적용: Supabase SQL Editor 에서 전체 실행. (한 번)
-- ============================================================

-- 시험 정의 (문제는 questions jsonb 로 스냅샷 저장 → 온라인·종이 동일, 채점 결정적)
create table if not exists public.voca_tests (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  org_id      uuid,
  created_by  uuid,                 -- 출제한 관리자(auth.uid())
  title       text,                 -- 시험명
  book_id     text,                 -- 출처 단어장
  book_title  text,
  pages       jsonb,                -- 출처 Day 목록 (["Day 1","Day 2"])
  qtype       text,                 -- 'mc'(객관식) | 'spell'(주관식) | 'mix'
  questions   jsonb not null,       -- [{n,type,en,meaning,prompt,answer,choices?}]
  num         int,                  -- 문항 수
  student_ids uuid[],               -- 대상 학생(null=승인 학생 전원)
  due_date    date,
  active      boolean not null default true
);
create index if not exists idx_tests_org on public.voca_tests(org_id, created_at desc);

-- 응시 결과
create table if not exists public.voca_test_results (
  id           uuid primary key default gen_random_uuid(),
  created_at   timestamptz not null default now(),
  test_id      uuid references public.voca_tests(id) on delete cascade,
  user_id      uuid,
  user_name    text,
  org_id       uuid,
  score        int,
  total        int,
  answers      jsonb,               -- 학생 답안 [{n,given,ok}]
  submitted_at timestamptz not null default now()
);
create index if not exists idx_tresults_test on public.voca_test_results(test_id);
create index if not exists idx_tresults_user on public.voca_test_results(user_id, created_at desc);

alter table public.voca_tests        enable row level security;
alter table public.voca_test_results enable row level security;

grant select, insert, update, delete on public.voca_tests        to authenticated;
grant select, insert                on public.voca_test_results   to authenticated;

-- 시험 조회: 출제자 본인 or (활성 & 같은 org 승인학생 & 대상에 포함)
drop policy if exists tests_read on public.voca_tests;
create policy tests_read on public.voca_tests for select using (
  created_by = auth.uid()
  or ( active and exists (
        select 1 from members m
        where m.id = auth.uid() and m.org_id = voca_tests.org_id
          and m.org_role = 'student' and m.org_status = 'approved')
      and (student_ids is null or auth.uid() = any(student_ids)) )
);
drop policy if exists tests_insert on public.voca_tests;
create policy tests_insert on public.voca_tests for insert with check (created_by = auth.uid());
drop policy if exists tests_update on public.voca_tests;
create policy tests_update on public.voca_tests for update using (created_by = auth.uid());
drop policy if exists tests_delete on public.voca_tests;
create policy tests_delete on public.voca_tests for delete using (created_by = auth.uid());

-- 결과: 학생은 본인 것 작성/열람, 출제자는 자기 시험 결과 전체 열람
drop policy if exists tresults_insert on public.voca_test_results;
create policy tresults_insert on public.voca_test_results for insert with check (user_id = auth.uid());
drop policy if exists tresults_read on public.voca_test_results;
create policy tresults_read on public.voca_test_results for select using (
  user_id = auth.uid()
  or exists (select 1 from voca_tests t where t.id = voca_test_results.test_id and t.created_by = auth.uid())
);

-- 관리 조회:
--  · 시험별 성적: select user_name, score, total, submitted_at from voca_test_results where test_id='...' order by score desc;
-- 되돌리기: drop table if exists public.voca_test_results; drop table if exists public.voca_tests;
-- ============================================================
