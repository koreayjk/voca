-- ============================================================
-- IM VOCA — iOS 앱(APNs) 알림을 기존 구독 표에 얹기
--
-- 왜 표를 새로 만들지 않는가:
--   보낼 대상을 고르는 로직(시간대·발송 시각·오늘 보냈는지·밀린 복습 개수)이
--   이미 voca_push_subs 에 맞춰져 있다. 전송 방식만 다르므로 platform 으로 갈라
--   엣지 함수 안에서 웹(VAPID) / iOS(APNs) 를 나눠 보낸다.
--
--   endpoint 컬럼:  웹 = 푸시 서비스 URL,  iOS = 기기 토큰(hex)
--   p256dh/auth:    웹에만 있다 → iOS 행을 위해 null 허용으로 바꾼다
--
-- 적용: Supabase SQL Editor 에 붙여넣고 실행 (여러 번 실행해도 안전)
-- ============================================================

alter table public.voca_push_subs
  add column if not exists platform text not null default 'web';

-- 웹 구독에만 있는 값들 — iOS 행은 비워둔다
alter table public.voca_push_subs alter column p256dh drop not null;
alter table public.voca_push_subs alter column auth   drop not null;

-- 형식이 섞여 들어오는 걸 막는다. (앱 버그로 platform 을 안 보내면 'web' 으로 들어가
--  APNs 토큰을 웹 푸시로 보내려다 조용히 실패한다 — 그 상황을 여기서 차단)
alter table public.voca_push_subs drop constraint if exists voca_push_subs_platform_ck;
alter table public.voca_push_subs add constraint voca_push_subs_platform_ck
  check (
    (platform = 'web' and p256dh is not null and auth is not null)
    or (platform = 'ios')
  );

create index if not exists idx_push_subs_platform on public.voca_push_subs(platform);
