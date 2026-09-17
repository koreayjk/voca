-- ============================================================
-- IM VOCA — '무료 스캔 소진' 안내 메일
--
-- 왜 필요한가:
--   앱스토어 가이드라인 3.1.1 때문에 iOS 앱 안에서는 가격도, 결제 링크도
--   보여줄 수 없다. 그러면 무료 10장을 다 쓴 사용자는 "어디서 결제하지?" 하고
--   그냥 이탈한다. **애플 규정은 앱 안만 규율하고 이메일은 자유롭다** —
--   그래서 막힌 직후 메일로 안내한다.
--
-- 적용: Supabase SQL Editor 에 이 파일 전체 실행.
-- ============================================================

-- ── 1) 발송 상태 컬럼 ───────────────────────────────────────────
alter table public.members
  -- 언제 보냈는지. null 이면 아직 안 보냄 → 한 사람에게 평생 1회만 간다.
  add column if not exists limit_email_sent_at timestamptz,
  -- 수신거부 시각. CAN-SPAM 상 거부한 사람에게는 절대 다시 보내면 안 된다.
  add column if not exists email_optout_at timestamptz,
  -- 수신거부 링크용 토큰. 로그인 없이 눌러야 하므로 추측 불가능한 값이 필요하다.
  -- (user_id 를 그대로 쓰면 남의 수신거부를 대신 눌러버릴 수 있다)
  add column if not exists email_token uuid default gen_random_uuid(),
  -- 메일 언어. 지금까지 화면 언어는 브라우저 localStorage 에만 있어서 서버가 몰랐다.
  -- 앱이 접속할 때마다 채워준다(loadUserPlan 의 방문 기록 PATCH 에 같이 실림).
  add column if not exists native_lang text;

-- 기존 회원 토큰 채우기
update public.members set email_token = gen_random_uuid() where email_token is null;

create unique index if not exists uq_members_email_token on public.members(email_token);

-- 발송 대상 조회용 (무료 + 아직 안 보냄)
create index if not exists idx_members_limit_mail
  on public.members(plan, scan_count) where limit_email_sent_at is null;


-- ── 2) 발송 대상 집계 (엣지 함수가 쓴다) ────────────────────────
-- 조건을 SQL 한 곳에 모아두면 함수 코드와 어긋날 일이 없다.
--   · 무료 플랜이고
--   · 무료 스캔 10장을 다 썼고
--   · 아직 안 보냈고, 수신거부도 안 했고
--   · 이메일이 있고
--   · 단체(학원) 소속 승인 학생이 아니다
--     → 학원이 결제하는 구조라 "프리미엄 사세요" 메일이 가면 안 된다
create or replace function public.limit_email_targets(p_limit int default 25)
returns table (id uuid, email text, name text, lang text, token uuid)
language sql stable security definer set search_path = public as $$
  -- 언어: members 에 기록된 값 → 알림 구독에 남은 값 → 한국어 순으로 고른다.
  -- (native_lang 은 이번에 추가한 컬럼이라, 아직 접속 안 한 기존 회원은 비어 있다)
  select m.id, m.email, m.name,
         coalesce(nullif(m.native_lang, ''),
                  (select s.lang from public.voca_push_subs s
                    where s.user_id = m.id and s.lang is not null limit 1),
                  'ko') as lang,
         m.email_token
  from public.members m
  where m.plan = 'free'
    and coalesce(m.scan_count, 0) >= 10
    and m.limit_email_sent_at is null
    and m.email_optout_at is null
    and m.email is not null and m.email <> ''
    and not (m.org_id is not null and m.org_status = 'approved')
  order by m.scan_count desc
  limit p_limit
$$;

revoke all on function public.limit_email_targets(int) from public, anon, authenticated;
grant execute on function public.limit_email_targets(int) to service_role;


-- ── 3) 매시간 발송 ──────────────────────────────────────────────
-- 매시간 도는 건 '다 쓴 뒤 한 시간 안에' 닿기 위해서다. 한 사람에게 1회만 가므로
-- 반복 발송 걱정은 없다.
--   select cron.schedule('imvoca-limit-email', '10 * * * *', $cron$
--     select net.http_post(
--       url     := 'https://<프로젝트>.supabase.co/functions/v1/send-limit-email',
--       headers := jsonb_build_object('Authorization', 'Bearer <SB_SERVICE_ROLE_KEY>',
--                                     'Content-Type', 'application/json'),
--       body    := '{}'::jsonb
--     );
--   $cron$);
--
-- 확인:  select * from cron.job where jobname = 'imvoca-limit-email';
-- 발송 현황:
--   select count(*) filter (where limit_email_sent_at is not null) as 보냄,
--          count(*) filter (where email_optout_at is not null)     as 수신거부
--   from members;
