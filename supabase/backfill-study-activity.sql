-- ============================================================
-- IM VOCA — '새로 외움(study)' 활동 기록 백필
--
-- 증상: 학습 리포트의 '날짜별 학습 내용'에서 어떤 Day 가 [복습] 칸에는
--       나오는데 [새로 외움] 칸에는 한 번도 안 나온다. 진도표에서도 빠진다.
--       (예: Day 4·5·6·7 을 분명히 외웠는데 복습 기록만 있다)
--
-- 원인: 복습 일정(voca_review)은 만들어졌는데 활동 로그(voca_activity)의
--       'study' 한 줄이 남지 않은 경우다. 아래 상황에서 생긴다.
--         ① voca_activity 테이블을 만들기 전에 외운 페이지
--            (activity-log.sql 주석: "과거 기록은 없음 — 생성 이후부터 쌓임")
--         ② 예전 버전: 퀴즈를 통과해야만 study 가 기록되던 시절
--         ③ 기록 전송이 실패하고 재전송 큐가 살아남지 못한 경우
--            (앱을 지우거나 다른 기기로 갈아탄 경우)
--       복습은 일정만 있으면 계속 돌기 때문에 복습 기록만 남는다.
--
-- 복구 근거: voca_review 에는 그 페이지를 처음 외운 시각이 있다
--            (first_studied_at, 없으면 created_at). 이걸 날짜로 삼아
--            빠진 'study' 한 줄을 채워 넣는다. 단어 수는 실제 페이지의
--            단어 개수를 세어 넣는다.
--
-- 적용: Supabase SQL Editor 에서 ①②를 먼저 보고, ③을 실행.
-- ============================================================


-- ── ① 얼마나 빠져 있나 (전체) ───────────────────────────────
select count(*) as 빠진_study_기록
from public.voca_review r
join public.voca_books b on b.id::text = r.book_id::text
where coalesce(r.first_studied_at, r.created_at) is not null
  and not exists (
    select 1 from public.voca_activity a
    where a.user_id = r.user_id and a.kind = 'study'
      and a.book_id = b.id and a.page_num = r.page_num
  );


-- ── ② 학생별로 몇 개씩 빠졌나 (많은 순) ─────────────────────
select m.name as 이름, m.email as 이메일, count(*) as 빠진_개수,
       min(coalesce(r.first_studied_at, r.created_at))::date as 가장_오래된,
       max(coalesce(r.first_studied_at, r.created_at))::date as 가장_최근
from public.voca_review r
join public.voca_books b on b.id::text = r.book_id::text
left join public.members m on m.id = r.user_id
where coalesce(r.first_studied_at, r.created_at) is not null
  and not exists (
    select 1 from public.voca_activity a
    where a.user_id = r.user_id and a.kind = 'study'
      and a.book_id = b.id and a.page_num = r.page_num
  )
group by m.name, m.email
order by 빠진_개수 desc
limit 50;


-- ── ③ 백필 실행 ─────────────────────────────────────────────
-- 같은 (학생·책·페이지) 에 'study' 가 이미 있으면 건드리지 않는다.
-- 여러 번 실행해도 중복으로 들어가지 않는다.
insert into public.voca_activity (user_id, org_id, book_id, page_num, kind, words, day)
select r.user_id,
       m.org_id,
       b.id,
       r.page_num,
       'study',
       coalesce(w.n, 0),
       coalesce(r.first_studied_at, r.created_at)::date
from public.voca_review r
join public.voca_books b on b.id::text = r.book_id::text
left join public.members m on m.id = r.user_id
left join lateral (
  select count(*)::int as n
  from public.voca_pages p
  join public.voca_words wd on wd.page_id = p.id
  where p.book_id = b.id and p.page_num::text = r.page_num::text
) w on true
where coalesce(r.first_studied_at, r.created_at) is not null
  and not exists (
    select 1 from public.voca_activity a
    where a.user_id = r.user_id and a.kind = 'study'
      and a.book_id = b.id and a.page_num = r.page_num
  );


-- ── ④ 확인 — ① 을 다시 돌리면 0 이어야 한다 ─────────────────
