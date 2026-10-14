-- ============================================================
-- IM VOCA — 레벨 12권 부제(author) 설정
--
-- 책 타일은 '제목 / 부제 / 단어 수' 세 줄로 그려진다. 지금 부제는 열두 권이
-- 전부 'IM VOCA' 라 한 줄이 통째로 버려지고 있다. 거기에 단계와 CEFR 을
-- 넣으면 학생이 책장에서 바로 자기 수준을 가늠할 수 있다.
--
--   Lv.5
--   기본 · B1 · 400 단어
--
-- 제목에 학년(중1·고2)을 넣지 않는 이유: 그걸 피하려고 레벨제로 바꿨다.
-- 고3이 Lv.2 를 하는 건 괜찮지만 '중1 과정' 을 하는 건 자존심이 상한다.
--
-- 실행: Supabase SQL Editor 에서 전체 실행. 진도·복습에 영향 없음(표시만 바뀜).
-- ============================================================

update public.voca_books b
set author = v.sub
from (values
  ('IMV-L1',  '입문 · A1'),
  ('IMV-L2',  '입문 · A1~A2'),
  ('IMV-L3',  '입문 · A2'),
  ('IMV-L4',  '기본 · B1'),
  ('IMV-L5',  '기본 · B1'),
  ('IMV-L6',  '기본 · B1'),
  ('IMV-L7',  '중급 · B1~B2'),
  ('IMV-L8',  '중급 · B2'),
  ('IMV-L9',  '중급 · B2'),
  ('IMV-L10', '상급 · B2~C1'),
  ('IMV-L11', '상급 · C1'),
  ('IMV-L12', '최상급 · C1~C2')
) as v(code, sub)
where b.is_official = true
  and btrim(upper(b.description)) = v.code;

-- 확인 — 12줄이 나와야 한다
select title, author, description as code
from public.voca_books
where is_official = true and description like 'IMV-L%'
order by (regexp_replace(description, '\D', '', 'g'))::int;
