-- ============================================================
-- IM VOCA — 직접 입력 단어 즉시 조회용 인덱스
--
-- 공식 단어장(약 1만 5천 단어)을 사전처럼 쓴다. 사용자가 단어를 직접 입력하면
-- 저장 전에 여기서 먼저 찾아 뜻·발음기호·품사·예문을 바로 채운다.
-- 찾으면 Gemini 호출이 통째로 생략된다 — 즉시 표시되고 API 비용도 0이다.
--
-- 조회는 `en=ilike.<단어>` (와일드카드 없음 = 대소문자 무시 정확 일치) 라서
-- 일반 인덱스로는 안 걸린다. lower(en) 식(expression) 인덱스가 필요하다.
--
-- 적용: Supabase SQL Editor 에 실행 (여러 번 실행해도 안전)
-- ============================================================

create index if not exists idx_voca_words_en_lower
  on public.voca_words (lower(en));

-- 확인 — Index Scan 이 나와야 한다 (Seq Scan 이면 인덱스가 안 쓰인 것)
--   explain analyze
--   select en, base, ipa, sentence, level from voca_words where lower(en) = 'beneath';
