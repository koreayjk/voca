-- ============================================================
-- IM VOCA — '내 책장에 담은 공식 단어장' 을 서버에 저장
--
-- 왜 필요한가:
--   이 목록은 그동안 브라우저 localStorage 에만 있었다. 그래서 기기를 바꾸거나
--   앱을 새로 설치하면 목록이 비어 있고, 앱이 '복습 진도가 있는 공식책은 자동으로
--   담아준다'는 최초 시딩을 다시 돌려서 **사용자가 일부러 뺀 책이 되살아났다.**
--   (웹으로 쓰던 사람이 Play/App Store 앱을 설치하면 반드시 겪는다)
--
--   표를 새로 만들지 않고 members 에 jsonb 한 칸만 더한다. members 는 이미
--   '본인 행만 수정' RLS 가 걸려 있어서 정책을 새로 만들 필요가 없다.
--
--   { "ids": ["<book_id>", ...],            -- 책장에 담은 공식책
--     "at":  { "<book_id>": "2026-09-16T..." } }  -- 담은 시각(최신순 정렬용)
--
-- 적용: Supabase SQL Editor 에 붙여넣고 실행 (여러 번 실행해도 안전)
-- ============================================================

alter table public.members
  add column if not exists shelf_official jsonb;

comment on column public.members.shelf_official is
  '내 책장에 담은 공식 단어장 { ids: [book_id], at: { book_id: ISO } }. 앱이 직접 갱신한다.';
