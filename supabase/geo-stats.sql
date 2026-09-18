-- 회원이 어느 나라에서 가입하고 쓰는지 보기 위한 컬럼
-- ⚠️ IP 주소는 저장하지 않는다. 기기가 스스로 알려주는 표준시간대와 언어만 남긴다
--    (개인정보 부담이 적고, 지역 분포를 보기에는 충분하다).
--
--   tz         : 지금 쓰는 기기의 표준시간대 (예: Asia/Seoul, America/New_York) — 접속할 때마다 갱신
--   signup_tz  : 가입 직후 처음 확인된 표준시간대 — 비어 있을 때 한 번만 기록
--   locale     : 기기 언어 (예: ko-KR, en-US) — 표준시간대가 없을 때의 보조 단서
--
-- 나라 이름으로 바꾸는 일은 admin.html 이 IANA zone.tab 대조표로 처리한다.
-- (DB 에 나라를 굳혀 두지 않아야 대조표를 고쳐도 과거 데이터가 같이 고쳐진다)

alter table public.members add column if not exists tz text;
alter table public.members add column if not exists signup_tz text;
alter table public.members add column if not exists locale text;

-- 확인용
select count(*) as 전체,
       count(tz) as 지역_확인됨,
       count(signup_tz) as 가입지역_확인됨
from public.members;
