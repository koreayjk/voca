-- ============================================================
-- IM VOCA — 공지를 이메일로도 보내기
--
-- 앱 공지함(voca_notices)에 올린 글을 회원 메일함으로도 보낼 때 쓰는 테이블·함수.
-- 실제 발송은 엣지 함수 send-notice-email 이 한다 (Resend).
--
-- 두 가지를 지킨다:
--   1) 수신거부한 사람(email_optout_at)에게는 절대 보내지 않는다
--   2) 같은 공지를 두 번 받지 않는다 — 한 번에 200명씩 나눠 보내다 중간에
--      멈추거나 다시 눌러도, 이미 보낸 사람은 로그로 걸러진다
-- ============================================================

-- 어느 공지를 언제 몇 명에게 보냈는지 (공지 목록에 표시)
alter table public.voca_notices
  add column if not exists email_sent_at timestamptz,
  add column if not exists email_sent_count int not null default 0;

-- 누구에게 보냈는지 (중복 발송 방지 · 감사 기록)
-- campaign = 공지 id, 또는 공지 없이 메일만 보낼 때 만들어 쓰는 id
create table if not exists public.notice_email_log (
  campaign  uuid not null,
  member_id uuid not null,
  sent_at   timestamptz not null default now(),
  primary key (campaign, member_id)
);
alter table public.notice_email_log enable row level security;
-- 정책을 두지 않는다 = service_role(엣지 함수)만 읽고 쓴다

-- 이번 회차에 보낼 사람 목록
--   p_audience: all | active30 | dormant | never_scanned | ko | en | zh | es | premium | free
--   active30      = 최근 30일 안에 접속한 회원. 오래 묵은 주소가 많을 때 첫 발송은
--                   이쪽으로 하는 게 안전하다 (반송률이 높으면 도메인 평판이 깎인다)
--   dormant       = 가입 후 한 번 들어와 보고 다시 오지 않은 회원 (visit_count <= 1)
--   never_scanned = 사진 스캔을 한 번도 안 해본 회원 — 핵심 기능을 경험하지 못한 사람들
create or replace function public.notice_email_targets(
  p_campaign uuid,
  p_audience text default 'all',
  p_limit int default 200
)
returns table (id uuid, email text, name text, lang text, token uuid)
language plpgsql
security definer
set search_path = public
as $$
begin
  -- 모르는 조건이 들어오면 조용히 0명이 아니라 에러를 낸다.
  -- (이 파일을 다시 실행하지 않은 채 관리자 화면에만 새 대상을 추가하면,
  --  '보낼 대상이 없었어요' 만 뜨고 왜 그런지 알 수가 없다)
  if p_audience not in ('all','active30','dormant','never_scanned',
                        'ko','en','zh','es','premium','free') then
    raise exception 'notice_email_targets: 모르는 대상 조건 "%" — notice-email.sql 을 다시 실행하세요', p_audience;
  end if;

  -- 수신거부 토큰이 없으면 수신거부 링크를 만들 수 없다 → 없는 사람만 지금 채운다
  update public.members set email_token = gen_random_uuid() where email_token is null;

  return query
  select m.id,
         m.email,
         m.name,
         coalesce(nullif(m.native_lang, ''), 'ko') as lang,
         m.email_token
  from public.members m
  where m.email is not null
    and m.email <> ''
    and m.email_optout_at is null                     -- 수신거부자 제외
    and (
      p_audience = 'all'
      or (p_audience = 'active30' and m.last_seen_at > now() - interval '30 days')
      or (p_audience = 'dormant' and coalesce(m.visit_count, 0) <= 1)
      or (p_audience = 'never_scanned' and coalesce(m.scan_count, 0) = 0)
      or (p_audience in ('ko','en','zh','es') and coalesce(nullif(m.native_lang,''),'ko') = p_audience)
      or (p_audience = 'premium' and m.plan = 'premium')
      or (p_audience = 'free' and coalesce(m.plan,'free') <> 'premium')
    )
    and not exists (
      select 1 from public.notice_email_log l
      where l.campaign = p_campaign and l.member_id = m.id
    )
  order by m.created_at
  limit greatest(1, least(p_limit, 500));
end $$;

-- 이 함수는 엣지 함수(service_role)만 부른다
revoke all on function public.notice_email_targets(uuid, text, int) from public;
revoke all on function public.notice_email_targets(uuid, text, int) from anon;
revoke all on function public.notice_email_targets(uuid, text, int) from authenticated;

-- 확인용 ① 지금 보낼 수 있는 사람 수
select count(*) filter (where email is not null and email <> '' and email_optout_at is null) as 받을수있는회원,
       count(*) filter (where email_optout_at is not null) as 수신거부,
       count(*) as 전체
from public.members;

-- 확인용 ② 대상별 인원 (관리자 화면에 뜨는 숫자와 맞는지 비교)
select 'dormant' as 대상, count(*) from notice_email_targets('00000000-0000-0000-0000-000000000000'::uuid,'dormant',500)
union all
select 'never_scanned', count(*) from notice_email_targets('00000000-0000-0000-0000-000000000000'::uuid,'never_scanned',500)
union all
select 'active30', count(*) from notice_email_targets('00000000-0000-0000-0000-000000000000'::uuid,'active30',500)
union all
select 'all', count(*) from notice_email_targets('00000000-0000-0000-0000-000000000000'::uuid,'all',500);
