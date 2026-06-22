-- ============================================================
-- IM VOCA — 담임제(선생님 ↔ 학생 매칭)
-- members.teacher_id = 그 학생의 담당 선생님(같은 org 의 owner) member id
-- Supabase SQL 에디터에서 실행하세요. (추가 RLS 불필요 — owner 는 이미
--  같은 org members 를 PATCH 할 수 있는 정책을 갖고 있음)
-- ============================================================
alter table members add column if not exists teacher_id uuid;
create index if not exists idx_members_teacher on members(teacher_id);

-- 참고:
--  - teacher_id 가 null 이면 '미배정' 학생.
--  - 주 관리자는 전체 학생을 보고 담당 선생님을 지정합니다.
--  - 공동 관리자(선생님)는 teacher_id 가 본인인 학생만 보게 됩니다(앱·org-report에서 필터).
