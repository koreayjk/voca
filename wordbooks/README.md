# IM VOCA 자체 단어장 프로젝트 — 이어서 작업하는 법

> 새 세션에서 이 폴더를 보거나 "단어장 이어서 만들자"라고 하면 이 문서 + 메모리(MEMORY.md)를 참고해 이어갈 것.

## 목표
저작권 안전한 **자체 단어장 7권** 제작. 출판사 책 복제 금지. **기출 빈도 + CEFR + 자체 예문** 기반.

## 7권 구성 (하루 40단어 × Day 단위 = 앱 page, 권 간 중복 없음)
- 중등 3권: 중1 기초(~600·A1~A2) / 중2 핵심(~700·A2~B1) / 중3 완성(~800·B1) — 교육부 중학어휘+CEFR
- 수능 4권: 기본(~1,200·B1~B2) / 핵심(~1,800·B2~C1) / 고난도(~800·C1~C2) / 숙어(~500) — 기출 빈도 기반

## 데이터 (이미 생성됨)
- `suneung-frequency.json` — 기출 전체 빈도표(상위 3000, surface form). 코퍼스 57개 시험(2009~2027 수능+6·9월 모평).
- `suneung-selection.json` — 정제 선택 풀 1,925개(기능어·기초어 제외, 기출 빈도순, ★등급).
- `suneung-basic-day1.json` — 수능 기본 Day 1(40단어). **예문 교체 완료**: 각 단어 meanings[0]에 `ex`(기출변형 재작성)·`tr`·`src`("YYYY 회차 NN번"). 40단어 전부 서로 다른 시험(2009~2025) 배정.
- `suneung-core-day1.json` — 초기 핸드픽 샘플(참고용).
- 기출 원본 PDF: `../../test/` 폴더 (EBSi 다운로드, 67개·중복포함). `pdftotext`로 추출, python은 `/opt/homebrew/bin/python3`(3.14).
- ★ 기준: ★★★ ≥20개 시험 · ★★ 8~19 · ★ 1~7.

## 파서·생성 도구 (`tools/`, 재사용)
**핵심 발견: `pdftotext -raw`가 2단 편집을 읽기순서대로 뽑아 문항번호(18~45)가 단조증가** → 줄머리 `NN.` 앵커로 문항 분리하면 단어↔문항 매핑 정확. (-layout은 컬럼이 줄단위로 섞여 실패. README 우려 해소.)
- `extract_corpus.py` → `corpus/index.json`(48개 시험 라벨식별: 연도+회차) + `corpus/<label>.txt`. 나머지 9개는 헤더가 이미지라 자동 라벨 실패(빈 PDF 3개 포함). 48개로 충분.
- `stopwords.txt` — 기능어·기초어(A1~A2)·요일/월·고유명사·불규칙형 제외 목록. 빈도 최상위어=쉬운 어휘라 필수.
- `build_day.py <N>` / `build_all_scaffolds.py <START> <END>` — 선택풀을 (stars,exams,total)순 + 스톱필터 + 복수형 휴리스틱으로 정렬, 40단어씩 Day 청크 선정 → 회차 골고루 출처배정 + recentYear 계산 → `suneung-basic-day<N>.scaffold.json`(언어정보 빈칸, `_ref`=실제 기출문장).
- **content.json 작성**(유일한 수작업/LLM): scaffold의 단어별 ipa·뜻·동의어·파생·어원 + `_ref` 기반 기출변형 예문 → `day<N>.content.json`. → 워크플로우 `generate-wordbook-days`로 병렬 생성.
- `merge_day.py <N>` — scaffold + content → 최종 `suneung-basic-day<N>.json`(src/exam/recentYear는 scaffold 유지, 누락단어 검증).
- (구) `find_occurrences.py`/`assign_sources.py`/`merge_examples.py` — Day1 예문교체용 초기 스크립트.

## 진행 상황
- **수능 기본 1권 완성: Day1~30 = 1,200단어**(중복 0, 전 필드 검증 통과). 각 단어 풀포맷 + 기출변형 예문 + 출처.
  - Day3~30은 워크플로우 `generate-wordbook-days`로 content.json 병렬 생성 후 merge_day로 완성.
  - 예외: jealous(D16)·envious(D27)는 듣기 '심정' 어휘라 독해(18~45)에 없어 출처/recentYear 공란 → 카드가 "🎯 기출 N개 시험"으로 폴백(정상).
  - 선택풀 잔여 ~256단어(+frequency 상위어)는 다음 권(수능 핵심 등)으로.
- 중간 산출물: `suneung-basic-day<N>.scaffold.json`(재생성 가능), `day<N>.content.json`(콘텐츠 소스, 편집 시 merge_day 재실행).
- 프리뷰: `wordbook-preview.html?day=N`으로 Day 전환(book/day 라벨 자동).

## 다음 권 만들 때
1. (필요시) 권 경계용 CEFR/난이도 필터 보강 — 현재는 빈도·★ 순. 수능 핵심/고난도는 더 희소·고급 어휘 위주.
2. `build_all_scaffolds.py <START> <END>` (이미 쓴 단어 자동 제외) → 워크플로우 재실행(프롬프트의 book명/레벨만 교체) → merge_day → 검증 스크립트.
3. 검증: 단어수 40·중복 0·필수필드·예문 표제어 포함(위 1회용 검증 코드 재사용).

## 단어 1개 포맷 (JSON)
`en · ipa · pos · meanings[]{pos,ko,ex,tr}(다의어는 빈출 뜻 2~3개) · syn[] · deriv[] · roots[]/etymHint(어근분해만, 스토리형 금지) · level(CEFR) · exam{count,exams,recentYear,stars}`

## ⚠️ 예문 규칙 (사용자 핵심 요청)
- 예문은 **그 단어가 실제 출제된 기출 문장의 "기출변형"** (그대로 복제 금지, CEFR에 맞춰 비슷하게 재작성).
- 출처를 **"2025 수능 35번 / 2023 6월모평 20번"**(연도+회차+문항번호)으로 표기.
- 한 단어장 내 **회차를 골고루** 분산.
- → 이를 위해 **각 시험 PDF를 문항(18~45번) 단위로 분리하는 파서**를 먼저 만들어야 함(2단 편집이라 컬럼 분리 필요). 연도·회차는 이미 정확, 문항번호만 파서로 보강.
- 생성은 **Gemini API(gemini-proxy 재활용) 자동 파이프라인** 권장 + 사람 검수 1회.

## 가격 (확정)
개인 $3.99 / 단체 $2.99 유지. 단어장은 **개인 프리미엄 + 단체(결제중) 모두 포함, 무료는 잠금**(맛보기 1 Day).

## 앱 카드 디자인 (확정)
`wordbook-preview.html` 참고. 앞면(단어·발음·품사·기출★배지·CEFR·발음듣기) / 뒷면(뜻①②·기출출처+예문+해석·동의어·파생·어원). 전체화면, 하단 버튼 고정.

## 다음 단계 순서
1. ✅ 시험 문항단위 파서 제작 (tools/, `-raw` 방식). 단어별 기출 occurrence + 문항번호 매핑 완료.
2. ✅ 회차 골고루 기출변형 예문 + 출처 생성 → 수능 기본 Day1 재생성 완료(품질 기준 확정). 카드 출처배지 "🎯 YYYY 회차 NN번 기출변형" 표시(wordbook-preview.html).
3. ⬜ Day 단위 대량 생성(7권): suneung-selection.json을 Day(40단어)로 분할 → tools 파이프라인 돌려 예문 생성(EX dict를 API 생성으로 대체) → 검수. 수능 기본 Day2부터.
4. ⬜ 앱 통합: 공식 단어장 등록(유료 잠금) + 학습카드 풀포맷 UI.

## 품질 기준 (Day1에서 확정)
- 예문: 실제 기출 지문을 CEFR(B1~B2)로 재작성(복제 X). 출처는 `meanings[0].src` = "2017 수능 40번".
- 한 Day 40단어 = 40개 서로 다른 시험(회차 골고루). 정확단어 등장 문항 우선, 빈칸/슬래시선택지 문장 회피.
