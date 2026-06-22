-- ============================================================
-- IM VOCA — 학원 과제(배정) 기능 스키마
-- Supabase SQL 에디터에서 그대로 실행하세요.
-- 진행 추적은 기존 voca_review 를 재사용합니다(별도 progress 테이블 없음).
-- ============================================================

-- 5.1 과제(배정) 테이블 ----------------------------------------
create table if not exists voca_assignments (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null,                 -- orgs.id
  assigned_by uuid not null,            -- members.id (배정한 관리자)
  book_id uuid not null,                -- voca_books.id (배정 원본; 복사 아님)
  page_num text,                        -- 특정 페이지. null = 책 전체
  title text,                           -- 표시용 스냅샷(책/페이지 제목)
  due_date date,                        -- 마감일(선택)
  target_type text not null default 'all',  -- 'all' = 승인학생 전체, 'selected' = 지정
  active boolean not null default true,
  created_at timestamptz not null default now()
);
create index if not exists idx_assign_org  on voca_assignments(org_id, active);
create index if not exists idx_assign_book on voca_assignments(book_id);

-- 5.2 지정 대상(target_type='selected'일 때만 사용) -------------
create table if not exists voca_assignment_students (
  assignment_id uuid not null references voca_assignments(id) on delete cascade,
  student_id uuid not null,             -- members.id
  primary key (assignment_id, student_id)
);
create index if not exists idx_assign_students_student on voca_assignment_students(student_id);

-- ============================================================
-- RLS
--  주의: 테이블끼리 정책에서 서로 참조하면 무한 재귀(42P17)가 납니다.
--  → 소유권/멤버십 체크를 SECURITY DEFINER 헬퍼 함수로 빼내 RLS를 우회합니다.
-- ============================================================
alter table voca_assignments enable row level security;
alter table voca_assignment_students enable row level security;

-- 헬퍼 1: 호출자가 특정 org 의 승인된 owner 인지 (RLS 우회)
create or replace function public._voca_is_org_owner(p_org uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from members
    where id = auth.uid()
      and org_id = p_org
      and org_role = 'owner'
      and org_status = 'approved'
  );
$$;

-- 헬퍼 2: 호출자가 특정 배정(assignment)의 org owner 인지 (RLS 우회)
create or replace function public._voca_owner_of_assignment(p_assignment uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1
    from voca_assignments a
    join members m on m.org_id = a.org_id
    where a.id = p_assignment
      and m.id = auth.uid()
      and m.org_role = 'owner'
      and m.org_status = 'approved'
  );
$$;

grant execute on function public._voca_is_org_owner(uuid) to authenticated;
grant execute on function public._voca_owner_of_assignment(uuid) to authenticated;

-- 이전(재귀) 정책 제거
drop policy if exists assign_owner_all          on voca_assignments;
drop policy if exists assign_student_select     on voca_assignments;
drop policy if exists assign_students_owner_all on voca_assignment_students;
drop policy if exists assign_students_self_select on voca_assignment_students;

-- voca_assignments: owner(주+공동) 는 자기 org 의 배정을 CRUD
create policy assign_owner_all on voca_assignments
  for all
  using (public._voca_is_org_owner(org_id))
  with check (public._voca_is_org_owner(org_id));

-- voca_assignment_students: owner CRUD
create policy assign_students_owner_all on voca_assignment_students
  for all
  using (public._voca_owner_of_assignment(assignment_id))
  with check (public._voca_owner_of_assignment(assignment_id));

-- voca_assignment_students: 학생 본인 행 SELECT (재귀 없음)
create policy assign_students_self_select on voca_assignment_students
  for select
  using (student_id = auth.uid());

-- ============================================================
-- 참고
--  - 학생의 배정 목록/원본(voca_books/pages/words) 읽기는
--    Edge Function `assignments-for-student`(service role)가 처리합니다.
--    그래서 학생용 voca_assignments 직접 SELECT 정책은 두지 않습니다(재귀 방지 + 보안 단순).
--  - 교사 리포트 voca_review 집계도 Edge Function `org-report` 경유.
-- ============================================================
