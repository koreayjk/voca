-- 공식 단어장 뜻·어원의 다국어 번역.
--
-- 왜 책을 새로 만들지 않았나:
--   Lv.1~12 를 언어마다 복제하면 12권 × 언어수 만큼 책이 늘어난다.
--   영어 단어·발음기호·예문은 언어와 무관하게 똑같으므로 복제가 낭비고,
--   나중에 언어를 더할 때마다 책 12권씩 또 생긴다.
--   그래서 '바뀌는 두세 줄'만 따로 담고 읽을 때 합친다.
--
-- 번역 대상(voca_words 기준):
--   base  뜻          '기간, 시기'
--   ctx   문맥 뜻      (비어 있을 때가 많다)
--   etym  어원         'peri(둘레)+hod(길) → 한 바퀴 도는 길 → 기간'
-- 그대로 두는 것: en, ipa, sentence, level, analysis.pos
-- 빼는 것:       analysis.src('2014 수능 25번'), analysis.exam — 한국 수험생 전용

create table if not exists voca_word_i18n (
  word_id    uuid not null references voca_words(id) on delete cascade,
  lang       text not null,              -- 'zh' | 'es' | 'ja' | …
  base       text not null,
  ctx        text,
  etym       text,
  updated_at timestamptz not null default now(),
  primary key (word_id, lang)
);
create index if not exists voca_word_i18n_lang_idx on voca_word_i18n (lang);

alter table voca_word_i18n enable row level security;

-- 공식 단어장의 번역이므로 누구나 읽을 수 있어야 한다(공식책 정책과 동일).
-- 쓰기 정책은 두지 않는다 — 번역 스크립트가 service_role 로만 넣는다.
drop policy if exists "word_i18n read official" on voca_word_i18n;
create policy "word_i18n read official" on voca_word_i18n
  for select using (
    exists (
      select 1 from voca_words w
        join voca_pages p on p.id = w.page_id
        join voca_books b on b.id = p.book_id
       where w.id = voca_word_i18n.word_id and b.is_official = true
    )
  );
