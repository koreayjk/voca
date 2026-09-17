-- ============================================================
-- IM VOCA — 정합성 이상 '자동 보수'
--
-- 매일 점검(voca_integrity_check)이 잡는 11가지 중, **되돌릴 필요가 없을 만큼
-- 명백한 것만** 자동으로 고친다. 나머지는 손대지 않고 리포트로 올린다.
--
-- ⚠️ 자동 수리에서 제일 위험한 건 "조회 버그 때문에 멀쩡한 데이터가 갑자기
--    '고아'로 보이는 날" 이다. 그날 자동 삭제가 돌면 피해가 되돌릴 수 없다.
--    그래서 세 가지 안전장치를 건다:
--      ① 한도(blast radius) — 한 항목이 한도보다 많이 잡히면 **고치지 않고** 넘긴다.
--         평소 1~2건이던 게 갑자기 500건이면 그건 데이터 문제가 아니라 코드 문제다.
--      ② 나이 제한 — 방금 만들어진 행은 건드리지 않는다(저장 중인 것 보호).
--      ③ 전량 기록 — 무엇을 몇 건 고쳤는지 voca_autofix_log 에 남긴다.
--
-- 자동으로 고치는 것 (되돌릴 필요가 없는 것들):
--   · 빈 페이지 삭제              — 단어 0개, 하루 지난 것
--   · 빈 페이지 복습 삭제          — 학습 자체가 불가능한 유령 행
--   · 멈춘 복습 completed=true    — 플래그만 안 켜진 것
--   · 단체학생 활동 org_id 백필    — 값 채우기
--   · 고아 배정 비활성화           — 삭제가 아니라 active=false (이력 보존)
--   · 복습 first_studied_at 백필   — created_at 으로 채움
--
-- 사람이 봐야 하는 것 (자동으로 고치지 않음):
--   · 중복 페이지        — 단어를 옮기고 지우는 작업. 잘못되면 학습 내용이 사라진다
--   · 중복 복습 행        — 어느 행을 남길지 판단이 필요
--   · 순서 꼬인 복습      — 복습 일정을 새로 쓴다. 사용자가 보는 날짜가 바뀐다
--   · 고아 복습(책/페이지 없음) — 학습 기록이 든 행을 지우는 일.
--                          책이 잠깐 안 보이는 버그가 있던 날 돌면 진짜 기록이 날아간다
--   → 이것들은 supabase/cleanup-integrity.sql 로 눈으로 보고 처리한다.
--
-- 적용: Supabase SQL Editor 에 이 파일 전체 실행.
-- ============================================================

-- ── 1) 수리 기록 ────────────────────────────────────────────────
create table if not exists public.voca_autofix_log (
  id         bigserial primary key,
  ran_at     timestamptz not null default now(),
  action     text not null,      -- 무엇을
  affected   int  not null,      -- 몇 건 고쳤는지 (건너뛰었으면 0)
  skipped    text                -- 건너뛴 이유 (null 이면 실행됨)
);
create index if not exists idx_autofix_log_ran on public.voca_autofix_log(ran_at desc);

alter table public.voca_autofix_log enable row level security;
-- 일반 사용자는 읽을 이유가 없다. 관리 화면은 service_role 로 본다.
revoke all on table public.voca_autofix_log from anon, authenticated;


-- ── 2) 자동 보수 함수 ───────────────────────────────────────────
-- p_limit   : 한 항목이 이보다 많이 잡히면 고치지 않고 건너뛴다(기본 50)
-- p_dry_run : true 면 실제로 고치지 않고 '몇 건이 대상인지'만 돌려준다
create or replace function public.voca_integrity_autofix(
  p_limit   int     default 50,
  p_dry_run boolean default false
)
returns table(action text, affected int, skipped text)
language plpgsql security definer set search_path = public as $$
declare
  n int;
begin
  create temp table _fix(action text, affected int, skipped text) on commit drop;

  -- ① 빈 페이지 복습 삭제 ------------------------------------------------
  --    페이지는 있는데 단어가 0개 → 열어도 "0개 단어라 외울 수 없음".
  --    ⚠️ 페이지보다 **먼저** 지워야 한다. 페이지를 먼저 지우면 이 복습은
  --       '페이지 없는 고아'가 되어 여기서 더 못 찾는다.
  --    ⚠️ 같은 Day 에 중복 페이지가 있고 그중 하나에만 단어가 있으면 학습이
  --       가능하므로 이상이 아니다 — '단어 있는 페이지가 하나도 없을 때'만 센다.
  select count(*) into n from voca_review vr
   where exists (select 1 from voca_pages p
                 where p.book_id::text = vr.book_id and p.page_num = vr.page_num)
     and not exists (select 1 from voca_pages p2
                 where p2.book_id::text = vr.book_id and p2.page_num = vr.page_num
                   and exists (select 1 from voca_words w2 where w2.page_id = p2.id));
  if n = 0 then
    insert into _fix values ('빈 페이지 복습 삭제', 0, null);
  elsif n > p_limit then
    insert into _fix values ('빈 페이지 복습 삭제', 0, format('건수 초과(%s > 한도 %s) — 사람이 확인 필요', n, p_limit));
  elsif p_dry_run then
    insert into _fix values ('빈 페이지 복습 삭제', n, '미리보기');
  else
    delete from voca_review vr
     where exists (select 1 from voca_pages p
                   where p.book_id::text = vr.book_id and p.page_num = vr.page_num)
       and not exists (select 1 from voca_pages p2
                   where p2.book_id::text = vr.book_id and p2.page_num = vr.page_num
                     and exists (select 1 from voca_words w2 where w2.page_id = p2.id));
    get diagnostics n = row_count;
    insert into _fix values ('빈 페이지 복습 삭제', n, null);
  end if;

  -- ② 빈 페이지 삭제 -----------------------------------------------------
  --    하루가 지난 것만. 방금 만들어져 단어가 아직 안 올라온 페이지를 보호한다.
  select count(*) into n from voca_pages p
   where not exists (select 1 from voca_words w where w.page_id = p.id)
     and p.created_at < now() - interval '1 day';
  if n = 0 then
    insert into _fix values ('빈 페이지 삭제', 0, null);
  elsif n > p_limit then
    insert into _fix values ('빈 페이지 삭제', 0, format('건수 초과(%s > 한도 %s) — 사람이 확인 필요', n, p_limit));
  elsif p_dry_run then
    insert into _fix values ('빈 페이지 삭제', n, '미리보기');
  else
    delete from voca_pages p
     where not exists (select 1 from voca_words w where w.page_id = p.id)
       and p.created_at < now() - interval '1 day';
    get diagnostics n = row_count;
    insert into _fix values ('빈 페이지 삭제', n, null);
  end if;

  -- ③ 멈춘 복습 completed 켜기 ------------------------------------------
  --    6단계가 모두 끝났는데 플래그만 안 켜진 행. 값 하나만 바꾸므로 위험이 없다.
  select count(*) into n from voca_review
   where completed = false
     and review_2d is null and review_3d is null and review_6d is null
     and review_15d is null and review_30d is null and review_60d is null;
  if n = 0 then
    insert into _fix values ('멈춘 복습 완료 처리', 0, null);
  elsif p_dry_run then
    insert into _fix values ('멈춘 복습 완료 처리', n, '미리보기');
  else
    update voca_review set completed = true
     where completed = false
       and review_2d is null and review_3d is null and review_6d is null
       and review_15d is null and review_30d is null and review_60d is null;
    get diagnostics n = row_count;
    insert into _fix values ('멈춘 복습 완료 처리', n, null);
  end if;

  -- ④ 단체학생 활동 org_id 백필 -----------------------------------------
  --    비어 있는 값을 채우기만 한다(덮어쓰지 않는다).
  select count(*) into n from voca_activity a
   where a.org_id is null
     and exists (select 1 from members m where m.id = a.user_id and m.org_id is not null);
  if n = 0 then
    insert into _fix values ('활동 org_id 백필', 0, null);
  elsif p_dry_run then
    insert into _fix values ('활동 org_id 백필', n, '미리보기');
  else
    update voca_activity a set org_id = m.org_id
      from members m
     where a.user_id = m.id and a.org_id is null and m.org_id is not null;
    get diagnostics n = row_count;
    insert into _fix values ('활동 org_id 백필', n, null);
  end if;

  -- ⑤ 고아 배정 비활성화 -------------------------------------------------
  --    삭제하지 않고 active=false. 이력이 남아 되돌릴 수 있다.
  select count(*) into n from voca_assignments a
   where a.active and not exists (select 1 from voca_books b where b.id::text = a.book_id::text);
  if n = 0 then
    insert into _fix values ('고아 배정 비활성화', 0, null);
  elsif n > p_limit then
    insert into _fix values ('고아 배정 비활성화', 0, format('건수 초과(%s > 한도 %s) — 사람이 확인 필요', n, p_limit));
  elsif p_dry_run then
    insert into _fix values ('고아 배정 비활성화', n, '미리보기');
  else
    update voca_assignments a set active = false
     where a.active and not exists (select 1 from voca_books b where b.id::text = a.book_id::text);
    get diagnostics n = row_count;
    insert into _fix values ('고아 배정 비활성화', n, null);
  end if;

  -- ⑥ 복습 first_studied_at 백필 ----------------------------------------
  --    비어 있으면 행이 만들어진 시각으로 채운다. 첫 학습일은 그보다 앞설 수 없다.
  select count(*) into n from voca_review
   where first_studied_at is null and created_at is not null;
  if n = 0 then
    insert into _fix values ('first_studied_at 백필', 0, null);
  elsif p_dry_run then
    insert into _fix values ('first_studied_at 백필', n, '미리보기');
  else
    update voca_review set first_studied_at = created_at
     where first_studied_at is null and created_at is not null;
    get diagnostics n = row_count;
    insert into _fix values ('first_studied_at 백필', n, null);
  end if;

  -- 기록 (미리보기는 남기지 않는다)
  if not p_dry_run then
    insert into voca_autofix_log(action, affected, skipped)
    select f.action, f.affected, f.skipped from _fix f
    where f.affected > 0 or f.skipped is not null;
  end if;

  return query select f.action, f.affected, f.skipped from _fix f;
end $$;

revoke all on function public.voca_integrity_autofix(int, boolean) from public, anon, authenticated;
grant execute on function public.voca_integrity_autofix(int, boolean) to service_role;


-- ── 3) 매일 자동 실행 ───────────────────────────────────────────
-- 점검 리포트(voca-integrity-daily, 03:30 KST)보다 10분 먼저 돌려서,
-- 리포트에는 '자동으로 못 고친 것'만 남게 한다.
do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    if exists (select 1 from cron.job where jobname = 'voca-integrity-autofix') then
      perform cron.unschedule('voca-integrity-autofix');
    end if;
    -- 매일 03:20 KST (18:20 UTC)
    perform cron.schedule('voca-integrity-autofix', '20 18 * * *',
      $cron$ select public.voca_integrity_autofix(); $cron$);
  end if;
end $$;


-- ============================================================
-- ▶ 먼저 미리보기 (아무것도 고치지 않음):
--     select * from public.voca_integrity_autofix(50, true);
--
-- ▶ 실제로 한 번 돌리기:
--     select * from public.voca_integrity_autofix();
--
-- ▶ 무엇을 고쳤는지 이력 보기:
--     select * from voca_autofix_log order by ran_at desc limit 30;
--
-- ▶ 한도에 걸려 건너뛴 게 있는지 (이게 뜨면 사람이 봐야 한다):
--     select * from voca_autofix_log where skipped is not null order by ran_at desc;
--
-- 되돌리기:
--     select cron.unschedule('voca-integrity-autofix');
--     drop function if exists public.voca_integrity_autofix(int, boolean);
-- ============================================================
