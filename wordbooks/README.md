# IM VOCA 자체 단어장 — 인수인계 문서

> 새 세션(웹/로컬 클로드)에서 이 폴더를 이어 작업할 땐 **이 문서를 먼저 읽어라.** repo가 곧 컨텍스트다(채팅 기록에 의존하지 말 것).
> python은 로컬에서 `/opt/homebrew/bin/python3`. 저작권 안전이 최우선(출판사 책 복제 금지, 기출 "사실"만 인용, 예문은 기출변형).

## 목표 · 7권 구성 (하루 40단어 = 앱 1 page, 권 간 단어 중복 없음)
- 중등 3권: 중1 기초(~600·A1~A2) / 중2 핵심(~700·A2~B1) / 중3 완성(~800·B1)
- 수능 4권: 기본(1,200·B1~B2) / 핵심(1,800·B2~C1) / 고난도(800·C1~C2) / 숙어(~500·구동사·관용구)

## 진행 상황 (2026-06)
| 책 | prefix | code | 단어 | 최종 JSON | DB(공식책) | 발음 |
|---|---|---|---|---|---|---|
| 수능 기본 | basic | SUN-BASIC | 1,200 (30일) | ✅ | ✅ | ✅ |
| 수능 핵심 | core | SUN-CORE | 1,800 (45일) | ✅ | ✅ | ✅ |
| 수능 고난도 | hard | SUN-HARD | 800 (20일) | ✅ | ✅ | ✅ |
| 수능 숙어 | idiom | SUN-IDIOM | 523 (14일) | ✅ | ✅* | ✅* |
| 중등 기초 | mid1 | MID-1 | 500 (13일·A1) | ✅ | ✅ | ✅ |
| 중등 핵심 | mid2 | MID-2 | 600 (15일·A1~A2) | ✅ | ✅ | ✅ |
| 중등 완성 | mid3 | MID-3 | 700 (18일·B1) | ✅ | ✅ | ✅ |
| 스페인어 기초 | esp1 | ESP-1 | 500 (13일·A1) | ✅ | ⬜ | ⬜ |
| 스페인어 중급 | esp2 | ESP-2 | 600 (15일·A1~A2) | ✅ | ⬜ | ⬜ |
| 스페인어 선교 | esp3 | ESP-3 | 400 (10일·주제별) | ✅ | ⬜ | ⬜ |
| 토익 기초 | toeic1 | TOEIC-1 | 493 (13일·600점대) | ✅ | ⬜ | ⬜ |
| 토익 핵심 | toeic2 | TOEIC-2 | 683 (18일·800점대) | ✅ | ⬜ | ⬜ |
| 토익 고득점 | toeic3 | TOEIC-3 | 874 (23일·900점대) | ✅ | ⬜ | ⬜ |

→ **7권 전부 완성 + DB등록·발음 완료(2026-06-26).** 7권 모두 is_official로 Supabase 등록·Storage 음원 업로드됨.
→ **TOEIC 3권 추가(2026-07-06, 최종 JSON):** 기초493·핵심683·고득점874=2,050. 40회 실전모의고사(`toeic/` PDF=이미지) **OCR(tesseract 170dpi)** → 88만단어 코퍼스(`toeic-corpus/`) → `build_toeic_pool.py`(빈도+사전대조 노이즈제거+문제형식어 제외, `toeic-pool-full.json` 3,662) → `build_toeic_scaffolds.py`(빈출 tier: 기초=최빈출/고득점=희귀, prefix toeic1/2/3) → 콘텐츠 워크플로우(비즈니스 예문) → 관대한 merge(OCR노이즈 단어 드롭)+수동 노이즈제거(chet/cist 등 OCR잘린어 26개). LC/RC 미구분(빈도 tier). 예문 자작(출처 없음). **DB등록·발음 남음**(발행 워크플로우 3회, 영어 음성 기본). corpus·PDF gitignore(저작권). merge는 인라인 관대버전 사용(scaffold/content stale 가능).
→ **스페인어 회화 3권 추가(2026-06-26, 최종 JSON):** 기초500·중급600·선교400=1,500. 회화 최빈출+구어체 예문(선교=전도·교회 대화), 명사 성(el/la) `gen` 필드. 기초↔중급 중복0/선교 중복허용. corpus 없이 풀생성(`spa-gen-pool.json` 1,818·`spa-mis-pool.json` 448)→`build_spanish_scaffolds.py`→콘텐츠 워크플로우→merge. **DB등록·발음 남음**: 발행 워크플로우 prefix별 3회, **음원은 스페인어 음성 지정**(tts_voice=`es-US-Neural2-A`, tts_lang=`es-US`). merge_day가 `gen` 보존, gen_audio 빈값 안전처리.
→ **고난도 단어 교체(2026-06-26):** 쉬운 350개(B2 336 + C1오분류 14: candy/joke/plumber 등) 삭제 → 진짜 C1~C2 350개(sagacious/insidious/ubiquitous 등) 신규. 유지 450(기출). 신규어는 자체집필 예문(src 없음). 최종 JSON 직접 조립(scaffold/merge 우회)이라 hard scaffold·content는 stale.
→ 중등은 corpus 없이 제작: 의미영역별 풀 생성(`mid-pool.json` 2,725개) → 수능 중복 **허용**(별개 단계, 겹치는 기초어=복습) + 1,800개로 축소 → CEFR 밴드별 영역 라운드로빈 선정 → `build_mid_scaffolds.py` → 콘텐츠 워크플로우(자작 예문) → merge.

### 2026-06 음원 정합성 수정 (⚠️ 재발행 필요)
- **음원 파일명 규칙 변경**: `_safeAudio`/`gen_audio.safe` = 영숫자+공백만 남기고 **공백→하이픈**. (구 규칙은 공백 제거라 `break down`↔`breakdown` 등 충돌) → **숙어(idiom) 음원 파일명 전부 변경** → idiom 음원 재생성 필요.
- **권 간 중복 단어 28개 제거(dedup)**: core↔hard·basic↔core에 같은 단어가 양쪽에 있어 같은 `s/<단어>.mp3`를 공유→예문 음성 불일치. 해결: hard↔core는 hard에서, basic↔core는 core에서 제거하고 같은 자리에 **레벨 맞는 새 단어**(exam.tested=false·자작예문, 기출ref없는 5% 패턴) 교체. hard 20개·core 8개 교체(7개 day파일 변경). **core·hard 재seed + basic·core·hard·idiom 음원 재생성 필요**(공유 음원이 owning book 예문으로 다시 써져야 정합).

## 중등 3권 만드는 법 (corpus 없이 — 웹 가능)
수능과 달리 기출 빈도풀이 없으므로 단어 소스가 다름:
1. 단어 선정: 교육부 지정 중학 기본 어휘(약 1,800) + CEFR A1~B1 기준으로 권 배분 — 중1 기초(~600·A1~A2)/중2 핵심(~700·A2~B1)/중3 완성(~800·B1). 수능 4권과 **중복 금지**(기존 suneung-*-day*.json 단어 제외).
2. 예문: 기출 출처 없음 → **CEFR 맞춘 자작 예문**(표제어 포함, 큰따옴표 금지). src 필드 공란.
3. 포맷·머지·검증·seed·발음은 수능과 동일(`merge_day.py N <prefix>` → `seed_official.py` BOOK_PREFIX=mid1 등 → 발행 워크플로우). 최종 파일명만 `suneung-` 대신 책 prefix 규칙 정하면 됨(merge_day/seed/gen_audio가 `suneung-<prefix>-day*.json` glob이므로 **prefix=mid1/mid2/mid3로 두고 파일명은 `suneung-mid1-day1.json` 형태 유지**가 도구 수정 없이 가장 간단).

## 새 책 만드는 전체 파이프라인 (예: 다음 책)
**⚠️ 1~3은 corpus/ 가 필요 → 로컬(맥)에서만. corpus/·*.scaffold.json 은 저작권 원문이라 gitignore(GitHub에 없음).**
1. **빈도풀** (한 번만, 이미 `suneung-pool-full.json` 있으면 생략): `python3 tools/build_corpus_pool.py` → corpus/*.txt 에서 필터링된 단어풀 생성.
   - corpus/ 가 없으면 먼저 `python3 tools/extract_corpus.py` (원본 PDF는 `../../test/`).
2. **스캐폴드**: `python3 tools/build_book_scaffolds.py "<책이름>" <CODE> <prefix> suneung-pool-full.json <START> <END>`
   - 이미 만든 모든 책 단어 자동 제외. 회차 골고루 기출 출처+recentYear 배정. → `suneung-<prefix>-day<N>.scaffold.json`.
3. **콘텐츠 생성** (워크플로우, 병렬): 각 scaffold를 읽어 ipa·뜻·동의어·파생·어원 + `_ref` 기반 **기출변형 예문**을 만들어 `<prefix>-day<N>.content.json` 으로 저장.
   - 기본=`generate-wordbook-days`, 핵심=`generate-core-days`, 고난도=`generate-hard-days` 워크플로우 참고(프롬프트의 책명·CEFR만 교체).
4. **머지**: `for n in $(seq 1 END); do python3 tools/merge_day.py $n <prefix>; done` → `suneung-<prefix>-day<N>.json` (최종).
5. **검증**: 40단어·중복0·기본외책 겹침0·필드(ipa/pos/level/ko/ex/tr)·예문에 표제어 포함.
6. **DB 등록 + 발음** → 로컬 터미널 OR **GitHub Actions(폰)**:
   - 로컬: `BOOK_PREFIX=<p> BOOK_TITLE="<이름>" BOOK_CODE=<CODE> OFFICIAL_OWNER=… SB_URL=… SB_SERVICE_KEY=… python3 tools/seed_official.py --go`
     그리고 `GOOGLE_API_KEY=… python3 tools/gen_audio.py --go --book <p>` → `SB_SERVICE_KEY=… python3 tools/upload_audio.py --go`
   - **폰/웹**: GitHub → Actions → **"단어장 발행"** → prefix·이름·코드 입력 → Run (`.github/workflows/publish-wordbook.yml`). Secrets: `SB_SERVICE_KEY`, `GOOGLE_API_KEY`.
     - ⚠️ **반드시 "Run workflow" 버튼(workflow_dispatch)으로 입력값을 직접 넣어 실행.** PR/자동 트리거로 돌면 입력이 비어 기본값(core)으로 엉뚱한 책을 등록함. 그리고 **해당 책 최종 JSON이 먼저 push 돼 있어야** 함(GitHub Desktop Push → 그 다음 Run).

## 도구 맵 (`tools/`)
- `extract_corpus.py` — 기출 PDF(`../../test/`) → `corpus/<연도_회차>.txt` + `corpus/index.json`(48시험 식별). **핵심: `pdftotext -raw`가 2단 편집을 읽기순서로 뽑아 문항번호 18~45 단조증가** → 줄머리 `NN.` 앵커로 단어↔문항 매핑.
- `build_corpus_pool.py` — corpus → `suneung-pool-full.json`(필터: 스톱워드·복수형·부사·고유명사 자동감지).
- `stopwords.txt` — 기능어·기초어·중상급 제외어·고유명사·축약형·비교급/숫자.
- `build_book_scaffolds.py` — 풀 → Day별 scaffold(+기출 출처). `build_all_scaffolds.py`/`build_day.py` 는 기본 전용(구).
- `build_idiom_scaffolds.py` — 숙어 전용. `suneung-idiom-pool.json`([{idiom,ko,pos}]) → 코퍼스에서 구(句) 매칭(one's/sb/sth 와일드카드+동사굴절 허용) → `suneung-idiom-day<N>.scaffold.json`(40개씩). 매칭된 것만 기출 출처. (숙어 검증: 분리형·불규칙동사 때문에 "예문에 표제어 포함" 단순체크는 오탐 많음 — 굴절·삽입 감안해 직접 확인.)
- `merge_day.py <N> [prefix]` — scaffold + content → 최종 Day JSON.
- `seed_official.py` — 최종 JSON → Supabase voca_books/pages/words 등록(`is_official=true`). env: `BOOK_PREFIX/TITLE/CODE`, `SB_URL`, `SB_SERVICE_KEY`, `OFFICIAL_OWNER`. `--reset`(재등록), `--update`(analysis만 갱신, uuid 유지).
- `gen_audio.py` — Google Cloud TTS(Neural2)로 단어·예문 mp3 생성(`--book <prefix>`로 한 책만). `upload_audio.py` — mp3를 Supabase Storage `audio` 버킷 업로드.
- `find_occurrences.py` — 코퍼스 문항 분리/검색 헬퍼(스캐폴드 빌더가 import).

## 단어 1개 포맷 (최종 JSON)
`en · ipa · pos · meanings[]{pos,ko,ex,tr(+첫째에 src)} · syn[] · deriv[] · roots[]/etymHint(어근분해, 스토리 금지) · level(CEFR) · exam{tested,count,exams,recentYear,stars}`

## 예문 규칙 (핵심)
- 예문 = 그 단어가 **실제 출제된 기출 지문의 "기출변형"**(복제 금지, CEFR 맞춰 재작성), 표제어 포함.
- 출처 `meanings[0].src` = "2017 수능 40번" 형식. 한 책 안에서 회차 골고루.
- `_ref` 없는 단어(희소/듣기어, 약 5%)는 대표 뜻에 맞는 자연 예문 신규 작성 → 카드는 출처배지 폴백.
- 예문에 큰따옴표(") 금지(작은따옴표) — JSON 깨짐 방지.

## 앱 통합 현황 (index.html — 코드 수정 불필요)
- `appendOfficialBooks()` 가 `is_official=true` 책을 **자동 로드** → seed만 하면 앱 책장에 등장.
- **잠금**: 무료=Day1만 / 프리미엄·단체결제=전체 (`hasOfficialAccess`/`isPageLocked`).
- **카드**: 공식책은 풍부한 카드(앞:기출★·CEFR / 뒤:뜻·🎯출처 기출변형·예문+해석·동의어·파생·어원, 밝은 크림 배경 `card--official`).
- **발음**: `_audioUrl`이 Supabase Storage URL(`/audio/w|s/<safe-en>.mp3`) 재생, 없으면 기기 TTS 폴백. **자동읽기 토글**(`toggleAutoRead`, 앞=단어/뒤=예문 반복).
- **Day 테스트**: 4지선다 퀴즈, 점수 `voca_stats`(page_num 포함) 저장. 학원 리포트·학부모 카드는 별도.
- 프리뷰: `wordbook-preview.html?day=N` (basic 전용 뷰어).

## DB / 키 (참고값)
- Supabase URL: `https://ziatqkjlafucqtwshhla.supabase.co` · 공식책 owner uuid: `fcfaf79d-0a27-41ac-93e2-9498b6716aba`
- 선행 SQL(1회): `supabase/official-books.sql`(is_official+RLS), `supabase/day-tests.sql`(voca_stats.page_num+RLS).
- 비공개 키(service_role, Google TTS)는 절대 커밋 금지 — 로컬 env 또는 GitHub Secrets.

## 가격 (확정)
개인 $3.99 / 단체 $2.99. 공식 단어장 = 프리미엄·단체결제 포함, 무료는 Day1 체험만.
