-- ============================================================
-- IM VOCA — 보안 하드닝 (2026-08)
-- Supabase Security Advisor 대응. SQL Editor 에서 "전체" 실행(여러 번 재실행해도 안전).
-- 적용 후: Advisor → Rerun linter 로 확인. 아래 "적용 후 테스트" 꼭 확인.
-- ============================================================

-- ── ① voca_activity: RLS 활성화 (Advisor 의 유일한 Error) ────
--  파일(activity-log.sql)엔 이미 있었지만 실제 DB엔 적용 안 됐던 상태.
--  활동 로그는 append-only → INSERT 는 본인만, 조회는 본인+담당 관리자.
alter table public.voca_activity enable row level security;

drop policy if exists activity_insert_self on public.voca_activity;
create policy activity_insert_self on public.voca_activity
  for insert with check (user_id = auth.uid());

drop policy if exists activity_select on public.voca_activity;
create policy activity_select on public.voca_activity
  for select using (
    user_id = auth.uid()
    or (org_id is not null and public._voca_is_org_owner(org_id))
  );

-- ── ② voca_settings: Gemini 키 공개읽기 차단 ────────────────
--  문제: settings_read(USING true) → 아무나 GET 하면 gemini_key 노출(요금 폭탄).
--  앱은 키를 클라이언트에서 안 읽음(엣지함수 gemini-proxy 전용) → 읽기정책 삭제해도 무해.
--  관리자 write 정책(settings_admin_write, ALL)은 그대로 두어 관리자 저장/조회 유지.
drop policy if exists settings_read on public.voca_settings;

-- ── ③ members: 전체 개인정보 공개읽기 차단 ──────────────────
--  문제: members_select_all(USING true) → 아무나 email/birth_date/stripe_customer_id 덤프.
--  해결: (a) 리더보드용 안전 뷰로 "안전 컬럼만" 공개
--        (b) 베이스 테이블은 본인 / 같은 org / 어드민 만 조회

-- 3-1) 리더보드·명예의전당 전용 안전 뷰 (민감컬럼 제외).
--      SECURITY DEFINER 뷰(뷰 소유자 권한으로 실행)라 RLS 우회 → 모두의 name/스탯만 공개.
--      Advisor 가 "Security Definer View" 경고를 띄울 수 있으나, 안전컬럼만 노출하므로 의도된 것.
create or replace view public.members_public as
  select id, name, total_words, perfect_reviews, last_scored_at,
         org_id, org_role, org_status
  from public.members;

grant select on public.members_public to anon, authenticated;

-- 3-2) 전체공개 SELECT 정책 제거
drop policy if exists members_select_all on public.members;

-- 3-3) 본인 행 조회 (개인회원 로그인/프로필)
drop policy if exists members_select_own on public.members;
create policy members_select_own on public.members
  for select using (auth.uid() = id);

-- 3-4) 어드민 대시보드(admin.html) 전체 조회 — admin.html 이 members 를 필터없이 읽음.
--      기존에 members_admin_update/errors_admin_read 와 동일한 어드민 이메일 패턴.
--      ⚠️ 어드민 이메일이 바뀌면 여기와 다른 어드민 정책들도 함께 갱신.
drop policy if exists members_admin_read on public.members;
create policy members_admin_read on public.members
  for select using ((auth.jwt() ->> 'email'::text) = 'koreayjk@gmail.com'::text);

--  유지되는 기존 조회 정책(그대로 둠):
--    · members_select_same_org  : 같은 org 학생/멤버 조회
--    · members_select_org_owner : 단체 관리자의 소속 학생 조회

-- ============================================================
-- 적용 후 테스트 (하나라도 깨지면 아래 롤백):
--   1) [개인] 로그인 → 내 프로필/플랜/스캔수 정상 표시 (members_select_own)
--   2) [개인] 명예의전당(리더보드) 이름·단어수 표시 (members_public 뷰)
--   3) [단체장] 소속 학생 목록·이메일 조회 정상 (members_select_org_owner)
--   4) [어드민 koreayjk] admin.html 전체 회원 목록 표시 (members_admin_read)
--   5) [유출차단 확인] 로그아웃/타계정 상태에서
--        GET /rest/v1/members?select=email  →  본인 것 외 안 나와야 정상
--        GET /rest/v1/voca_settings         →  빈 배열이어야 정상(키 안 나옴)
--   6) 단어 스캔(Gemini) 정상 — 엣지함수라 영향 없음
--
-- 롤백(문제 시, 원상복구):
--   -- members
--   drop policy if exists members_select_own  on public.members;
--   drop policy if exists members_admin_read   on public.members;
--   drop view   if exists public.members_public;
--   create policy members_select_all on public.members for select using (true);
--   -- voca_settings
--   create policy settings_read on public.voca_settings for select using (true);
--   -- voca_activity (원한다면 RLS 끄기 — 권장하지 않음)
--   -- alter table public.voca_activity disable row level security;
-- ============================================================
