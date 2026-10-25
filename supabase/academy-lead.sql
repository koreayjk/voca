-- 학원 영업 리스트를 만들기 위한 두 가지.
--
-- 왜 필요한가: 가입자가 1만 명이 돼도 members 에는 학교·지역·학년이 없어서
-- "어느 학원에 전화할지"를 모른다. 이 두 개가 있어야 1만 명이 영업 리스트가 된다.
--
-- ⚠️ 이 SQL 을 먼저 돌리고 index.html 이 배포된 뒤에 써야 한다.
--    (컬럼이 없으면 가입 시 members INSERT 가 통째로 400 이 난다)

-- ① 가입할 때 받는 '다니는 학원' (선택 입력)
alter table members add column if not exists academy_name text;
comment on column members.academy_name is '학생이 가입 때 적은 다니는 학원 이름. 자유 입력이라 표기가 제각각이다';

-- ② 학생이 직접 누르는 '우리 학원에 추천하기'
create table if not exists academy_leads (
  id            uuid primary key default gen_random_uuid(),
  created_at    timestamptz not null default now(),
  member_id     uuid references members(id) on delete set null,
  student_name  text,
  academy_name  text not null,
  contact       text,          -- 원장님 연락처(선택). 학생이 모르면 비워둔다
  memo          text,
  status        text not null default 'new'   -- new | contacted | won | lost
);
create index if not exists academy_leads_name_idx on academy_leads (lower(academy_name));
create index if not exists academy_leads_created_idx on academy_leads (created_at desc);

alter table academy_leads enable row level security;

-- 본인 추천만 넣을 수 있다. 읽기 정책은 일부러 두지 않았다 —
-- 영업 리스트라 사용자끼리 서로 보면 안 된다. 조회는 대시보드(service_role)로 한다.
drop policy if exists "academy_leads insert own" on academy_leads;
create policy "academy_leads insert own" on academy_leads
  for insert to authenticated with check (member_id = auth.uid());

-- ── 영업할 때 쓰는 조회 ───────────────────────────────────────────────
-- 같은 학원 이름이 몇 명이나 모였는지 (많은 순)
--   select lower(academy_name) 학원, count(*) 명수
--     from (
--       select academy_name from members      where academy_name is not null and academy_name <> ''
--       union all
--       select academy_name from academy_leads
--     ) t
--    group by 1 having count(*) >= 2 order by 2 desc;
--
-- 학생이 직접 추천한 건 (전환율이 가장 높다)
--   select created_at, academy_name, student_name, contact, status
--     from academy_leads where status = 'new' order by created_at desc;
