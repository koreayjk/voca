-- 무료 스캔 한도를 '평생 10장' → '하루 5장 + 월 60장' 으로 바꾸기 위한 컬럼.
--
-- ⚠️ 이 SQL 을 먼저 돌리고 gemini-proxy 를 배포해야 한다.
--    (순서가 바뀌면 edge function 이 없는 컬럼을 select 해서 스캔이 전부 막힌다.
--     voca_push_subs.platform 때 똑같이 당했다. 함수에 폴백을 넣어뒀지만
--     폴백은 월 한도를 건너뛰므로 SQL 을 먼저 돌리는 게 맞다.)
--
-- 하루 한도만 두면 한 계정이 연 1,825장까지 간다. 월 한도는 그 상한을 막는 보험이다.
-- 진짜 학생은 월 60장(주 5일 × 3장)을 넘길 일이 없다.

alter table members add column if not exists monthly_scan_count int not null default 0;
alter table members add column if not exists monthly_scan_month text;  -- 'YYYY-MM' (사용자 현지 기준)

comment on column members.monthly_scan_count is '이번 달 스캔 수 — monthly_scan_month 가 이번 달일 때만 유효';
comment on column members.monthly_scan_month is '카운트 기준 월(YYYY-MM). 달이 바뀌면 서버가 0부터 다시 센다';
