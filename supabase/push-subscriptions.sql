-- ============================================================
-- IM VOCA — 웹 푸시 구독 + '오늘 복습' 집계
--
-- 왜 필요한가:
--   안드로이드(Play 앱)는 navigator.setAppBadge() 를 지원하지 않는다.
--   대신 '읽지 않은 알림'이 있으면 OS 가 런처 아이콘에 배지를 붙여준다.
--   즉 아이콘 배지를 띄우려면 알림을 보내야 하고, 웹에는 예약 알림이 없으므로
--   서버가 매일 밀어줘야 한다. (iOS 16.4+ / PC 는 setAppBadge 로 숫자까지 표시)
--
-- 적용: Supabase SQL Editor 에 붙여넣고 실행
-- ============================================================

-- ── 1) 구독 테이블 ──────────────────────────────────────────
create table if not exists public.voca_push_subs (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  endpoint    text not null,
  p256dh      text not null,
  auth        text not null,
  -- 알림을 '사용자 현지 시각' 기준으로 보내기 위한 정보.
  -- (앱 전체가 로컬 시간대 기준으로 동작하므로 푸시도 같은 기준을 따른다)
  tz          text not null default 'Asia/Seoul',   -- IANA 이름 (예: America/Chicago)
  send_hour   int  not null default 9,              -- 현지 몇 시에 보낼지 (0~23)
  lang        text not null default 'ko',           -- 알림 문구 언어
  enabled     boolean not null default true,
  fail_count  int  not null default 0,              -- 연속 실패 — 일정 횟수 넘으면 정리
  last_sent_on date,                                -- 같은 날 중복 발송 방지
  created_at  timestamptz not null default now(),
  unique (endpoint)
);

create index if not exists idx_push_subs_user on public.voca_push_subs(user_id);

alter table public.voca_push_subs enable row level security;

-- 본인 구독만 읽고/쓰고/지울 수 있다. (발송은 service_role 이 RLS 우회)
drop policy if exists push_subs_select_own on public.voca_push_subs;
create policy push_subs_select_own on public.voca_push_subs
  for select using (auth.uid() = user_id);

drop policy if exists push_subs_insert_own on public.voca_push_subs;
create policy push_subs_insert_own on public.voca_push_subs
  for insert with check (auth.uid() = user_id);

drop policy if exists push_subs_update_own on public.voca_push_subs;
create policy push_subs_update_own on public.voca_push_subs
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists push_subs_delete_own on public.voca_push_subs;
create policy push_subs_delete_own on public.voca_push_subs
  for delete using (auth.uid() = user_id);


-- ── 2) '지금 기준 밀린/오늘자 복습' 사용자별 개수 ───────────────
-- 앱의 판정과 같은 규칙:
--   · completed = false 인 행만
--   · 현재 단계 = review_2d…review_60d 중 '첫 번째 null 이 아닌' 값
--     (단계를 끝내면 그 컬럼을 null 로 지우므로 coalesce 가 곧 현재 단계)
--   · 예정일은 로컬 자정으로 저장되므로, 현지 아침에 보낼 때 <= now() 면 오늘 것까지 포함
--   · 책이 삭제된 행은 제외 (join)
-- 주의: 앱은 여기에 더해 '페이지 없음/단어 0개' 유령 복습과 공식책 잠금까지 걸러내므로,
--       이 값이 앱 화면보다 아주 드물게 클 수 있다.
create or replace function public.due_review_counts()
returns table (uid uuid, due int)
language sql
stable
security definer
set search_path = public
as $$
  -- ⚠️ 앱 화면(checkReviews)과 '똑같은 기준'으로 세야 한다.
  --    앱은 내 책장에 없는 책의 복습을 숨기는데(findBook 이 없으면 skip), 여기서 그걸
  --    빼먹어서 "오늘 복습 13개" 알림을 받고 들어가면 2개만 있는 일이 있었다.
  --    공식 단어장을 책장에서 뺀 사람(11개)이 전부 여기 잡히고 있었다.
  select r.user_id, count(*)::int
  from public.voca_review r
  -- voca_review.book_id 와 voca_books.id 의 타입이 서로 다르다(uuid ↔ text).
  -- 어느 쪽이 무엇이든 안전하게 비교되도록 양쪽을 text 로 맞춘다.
  -- (book_id 에 uuid 가 아닌 값이 섞여 있어도 ::uuid 캐스팅처럼 에러가 나지 않는다)
  join public.voca_books b on b.id::text = r.book_id::text
  join public.members   m on m.id = r.user_id
  where r.completed = false
    and coalesce(r.review_2d, r.review_3d, r.review_6d,
                 r.review_15d, r.review_30d, r.review_60d) <= now()
    and (
      -- 내가 만든 책: 그대로 센다
      coalesce(b.is_official, false) = false
      or (
        -- 공식 단어장: ① 지금 내 책장에 담겨 있고
        exists (
          select 1
          from jsonb_array_elements_text(coalesce(m.shelf_official->'ids', '[]'::jsonb)) x
          where x = b.id::text
        )
        -- ② 볼 수 있는 자격이 있을 때만 (앱의 hasOfficialAccess 와 같은 기준).
        --    무료 사용자는 Day 1 체험만 열려 있으므로 그 페이지만 센다.
        and (
          m.plan = 'premium'
          or (m.org_role = 'owner' and m.org_status = 'approved')
          or (m.org_role = 'student' and m.org_status = 'approved')
          or r.page_num = 'Day 1'
        )
      )
    )
  group by r.user_id
$$;

revoke all on function public.due_review_counts() from public, anon, authenticated;
-- service_role(엣지 함수)만 호출한다.
grant execute on function public.due_review_counts() to service_role;


-- ── 3) 매시 정각 발송 잡 ────────────────────────────────────
-- 엣지 함수가 각 구독의 tz/send_hour 를 보고 "지금 현지 시각이 그 시간인 사람"에게만 보낸다.
-- 그래서 cron 은 매시간 돌리고, 누구에게 보낼지는 함수가 판단한다.
--
--   select cron.schedule('imvoca-review-push', '0 * * * *', $cron$
--     select net.http_post(
--       url     := 'https://<프로젝트>.supabase.co/functions/v1/send-review-push',
--       headers := jsonb_build_object('Authorization', 'Bearer <SB_SERVICE_ROLE_KEY>',
--                                     'Content-Type', 'application/json'),
--       body    := '{}'::jsonb
--     );
--   $cron$);
--
-- 수동 실행(테스트):  select public.due_review_counts();
