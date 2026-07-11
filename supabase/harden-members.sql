-- ============================================================
-- IM VOCA — members 권한 하드닝 (상용화 전 필수)
-- 문제: 앱이 members 를 클라이언트 JWT로 self-PATCH 하므로, members UPDATE RLS가
--       컬럼을 안 막으면 학생이 자기 행을 PATCH 해서
--         plan:'premium'      → 무료로 프리미엄 + 전체 공식단어
--         org_status:'approved' → 승인 대기 없이 자기승인(결제중 학원이면 무제한)
--         org_role:'owner'    → 스스로 단체 관리자로 승격
--       할 수 있음. (scan_count 자기수정으로 무료 스캔한도 우회는 별도 — 아래 주석)
-- 해결: BEFORE INSERT/UPDATE 트리거로 권한 컬럼을 클라이언트로부터 보호.
--       service_role(웹훅·엣지함수)은 무조건 통과. org_status/org_role 변경은
--       "같은 org 의 승인된 owner"만 허용(_voca_is_org_owner 재사용).
-- 적용: Supabase SQL Editor 에서 실행. 실행 후 아래 "적용 후 테스트" 꼭 확인.
--       문제가 있으면 즉시 되돌리기: 파일 하단 롤백 SQL.
-- 전제: assignments-schema.sql 의 public._voca_is_org_owner(uuid) 가 이미 있어야 함.
-- ============================================================

-- ── 가드 함수 ────────────────────────────────────────────────
create or replace function public._members_guard()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  is_service boolean := (coalesce(current_setting('request.jwt.claim.role', true),
                                   (current_setting('request.jwt.claims', true)::json ->> 'role'),
                                   auth.role()) = 'service_role');
  -- 슈퍼 어드민(어드민 대시보드) 이메일. admin.html 은 클라이언트 JWT로 members 를 PATCH 해서
  -- 개인회원을 단체장으로 승격하거나 공동관리자·학생으로 배정함. 이 이메일은 org_role/org_status
  -- 변경을 허용. (plan/scan 카운터는 여전히 잠금 — plan 은 admin-set-plan 엣지함수로만 변경)
  -- ⚠️ 어드민 이메일이 바뀌면 여기와 엣지함수 ADMIN_EMAILS 둘 다 갱신.
  admin_emails text[] := array['koreayjk@gmail.com'];
  caller_email text := lower(coalesce(
    current_setting('request.jwt.claims', true)::json ->> 'email', ''));
  is_admin boolean := caller_email <> '' and caller_email = any(admin_emails);
begin
  -- 웹훅/엣지함수(service_role)는 모든 컬럼 자유롭게 기록 (결제 반영 등)
  if is_service then return new; end if;

  if (tg_op = 'INSERT') then
    -- 가입 시 자기 자신을 프리미엄/관리자/승인으로 만드는 것 차단
    new.plan := 'free';
    if new.org_role is distinct from 'student' then
      -- 최초 가입은 항상 student·pending. 단체장은 별도 승격 경로로.
      new.org_role := 'student';
    end if;
    if new.org_id is not null then
      new.org_status := 'pending';   -- 코드로 가입하면 승인 대기
    end if;
    return new;
  end if;

  -- UPDATE ---------------------------------------------------
  -- plan / billing_active 은 클라이언트가 절대 못 바꿈 (결제 웹훅만)
  if new.plan is distinct from old.plan then
    raise exception 'members.plan 은 클라이언트가 변경할 수 없습니다(결제 웹훅 전용).';
  end if;

  -- org_role / org_status 는 "슈퍼 어드민" 또는 "같은 org 의 승인된 owner" 또는
  -- "그 org 를 직접 만든 사람(orgs.owner_id)" 만 변경 가능 (본인 무단 자가승격 차단).
  --  · 어드민: 개인→단체장 승격/배정을 어드민 대시보드에서 수행.
  --  · org 생성자: createOrg 에서 자기 자신을 owner/approved 로 승격(정당 — 자기가 만든 단체).
  if (new.org_role is distinct from old.org_role)
     or (new.org_status is distinct from old.org_status) then
    if not (is_admin
            or public._voca_is_org_owner(coalesce(old.org_id, new.org_id))
            or exists (select 1 from public.orgs o
                       where o.id = coalesce(new.org_id, old.org_id)
                         and o.owner_id = auth.uid())) then
      raise exception 'org_role/org_status 는 단체 관리자만 변경할 수 있습니다.';
    end if;
  end if;

  -- 스캔 카운터는 서버(gemini-proxy, service_role)만 기록. 클라이언트가 0으로 리셋해
  -- 무료 스캔 한도를 우회하는 것 차단. (앱은 더 이상 이 컬럼을 클라이언트로 안 씀)
  if (new.scan_count is distinct from old.scan_count)
     or (new.daily_scan_count is distinct from old.daily_scan_count)
     or (new.daily_scan_date is distinct from old.daily_scan_date) then
    raise exception 'scan 카운터는 서버에서만 관리합니다.';
  end if;

  return new;
end;
$$;

-- ── 트리거 부착 ──────────────────────────────────────────────
drop trigger if exists members_guard_ins on public.members;
create trigger members_guard_ins
  before insert on public.members
  for each row execute function public._members_guard();

drop trigger if exists members_guard_upd on public.members;
create trigger members_guard_upd
  before update on public.members
  for each row execute function public._members_guard();

-- ============================================================
-- 적용 후 테스트 (실패하면 롤백):
--   1) 무료 계정으로 앱에서: 프리미엄/승인/관리자 되기 시도가 막히는지
--      (개발자도구 콘솔) fetch('<SB_URL>/rest/v1/members?id=eq.<내id>',{method:'PATCH',
--        headers:{apikey:'<anon>',Authorization:'Bearer <내jwt>','Content-Type':'application/json',Prefer:'return=minimal'},
--        body:JSON.stringify({plan:'premium'})}).then(r=>r.status)  // → 4xx 여야 정상
--   2) 단체 주 관리자로: 학생 승인/거절/공동관리자 임명/담당 지정이 여전히 되는지
--   3) 결제 후 stripe-webhook 이 plan/billing_active 반영되는지(service_role → 통과)
--   4) 신규 가입(개인/학생/단체장)이 정상 동작하는지
--
-- 롤백(문제 시):
--   drop trigger if exists members_guard_ins on public.members;
--   drop trigger if exists members_guard_upd on public.members;
--   drop function if exists public._members_guard();
--
-- 남은 하드닝(별도 처리 필요 — 이 파일 범위 밖):
--   • scan_count/daily_scan_count: 무료 스캔한도 우회 방지는 gemini-proxy(엣지함수)
--     에서 서버측 증가·검증으로 옮겨야 함. 그 후 여기서도 두 컬럼 보호 추가 가능.
--   • voca_settings(gemini_key): 관리자만 읽기/쓰기로 RLS 잠그기(현재 모든 로그인
--     사용자가 REST로 접근 가능). 또는 Gemini를 엣지함수로만 호출.
--   • voca_notices: INSERT 를 관리자만 가능하도록 RLS 확인(아니면 XSS·스팸 위험).
--   • 공식 단어 잠금(Day2+)은 RLS가 아니라 앱에서만 막힘 → 엔타이틀먼트 엣지함수 권장.
-- ============================================================
