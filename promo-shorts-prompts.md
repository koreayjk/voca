# 🎬 IM VOCA 쇼츠·릴스 홍보 프롬프트 세트 (2026-08)

> 목적: 틱톡/릴스/유튜브 쇼츠용 세로 영상 3종. 각 컨셉마다 **맨트(나레이션 대본) · 온스크린 자막 · 컷별 연출 세팅 · AI 영상 생성 프롬프트(영문) · BGM/CTA** 를 바로 쓸 수 있게 정리.
> AI 영상 툴(Veo·Sora·Runway·Kling·Higgsfield 등) 어디에나 붙여넣기 가능. 실제 소재(`2.png` 로고, `wordbooks/promo/shots/*` 앱 화면) 를 UI 컷에 합성하면 신뢰도↑.

## 공통 세팅 (3종 모두 적용)
- **비율/길이:** 세로 9:16 · 20~30초
- **브랜드 톤:** 네이비(#1c3553)·골드(#c98a3a), 크림 배경, 따뜻하고 프리미엄
- **자막:** 한국어 번인(굵은 산세리프, 화면 하단 1/3), 핵심어만 골드 강조
- **훅 원칙:** 첫 1.5초 안에 문제/궁금증 제시 (스크롤 정지)
- **엔드카드:** IM VOCA 로고 + `imvoca.app` + "무료로 시작" (2~3초)
- **음성:** 편안한 20~30대 톤, 담백하게 (과장 X)
- **CTA 한 줄:** "교재만 찍어보세요. 나머진 AI가."

---

# 컨셉 1 · "찰칵 한 장의 마법" (핵심 기능 · 만족감형 훅)
가장 보편적이고 강한 훅. 촬영→단어장 자동생성의 '즉각적 마법'을 빠르고 만족스럽게.

**한 줄 메시지:** 교재를 찍으면, 단어장이 저절로 만들어진다.

| # | 시간 | 화면 | 자막(번인) | 맨트(VO) |
|---|------|------|-----------|----------|
| 1 | 0–2s | 형광펜 가득한 영어 교재, 모르는 단어에 멈춘 손 | **"단어 정리, 아직도 손으로 하세요?"** | "단어 하나하나 찾아 적는 거… 이제 그만." |
| 2 | 2–5s | 폰으로 교재 페이지 '찰칵' (셔터음·화면 밝아짐) | **"교재를 그냥 찍으세요"** | "그냥 교재를 찍기만 하면," |
| 3 | 5–10s | 앱: 단어가 스르륵 카드로 정리(뜻·발음·예문·CEFR) | **"AI가 뜻·발음·예문까지 자동"** | "AI가 어려운 단어만 골라, 뜻과 발음, 예문까지 자동으로." |
| 4 | 10–14s | 여러 장 넘기며 한 번에 추출되는 화면 | **"여러 장도 한 번에"** | "여러 페이지도 한 번에 끝나요." |
| 5 | 14–18s | 암기카드 플립 + 며칠 뒤 복습 알림 팝업 | **"잊을 때쯤 복습 알림까지"** | "그리고 잊을 때쯤, 복습 알림이 딱." |
| 6 | 18–22s | 로고 엔드카드 + CTA | **"IM VOCA · 무료 시작 · imvoca.app"** | "교재만 찍어보세요. IM VOCA." |

**AI 영상 생성 프롬프트 (컷별, 영문):**
1. `Vertical 9:16, cinematic close-up: a highlighted English textbook page, a young Korean student's hand pauses over an unknown word, warm desk lamp, cream & navy tones, shallow depth of field, slow push-in.`
2. `Vertical 9:16: same hand lifts a smartphone and photographs the textbook page, camera-shutter moment, a bright hopeful light blooms as the shot is taken, satisfying, crisp.`
3. `Vertical 9:16, screen-in-hand: clean premium mobile app UI where English words animate into neat vocabulary cards showing meaning, IPA pronunciation and an example sentence, navy & gold design, macro push-in.` *(실제 08-ai-word-extract.png 합성 권장)*
4. `Vertical 9:16: a thumb swiping through several textbook photos, each instantly turning into word cards, smooth fast motion, satisfying rhythm.`
5. `Vertical 9:16: person smiling while flipping study flashcards on a phone; a gentle review notification slides in from the top; warm cozy light.` *(09-flashcard-study.png 합성)*
6. `Vertical 9:16: minimal navy background with subtle paper-grain, centered gold "IM VOCA" logo, tagline and imvoca.app, soft fade-in.` *(로고 2.png)*

**BGM/페이싱:** 밝은 로파이 + 셔터/팝 사운드 이펙트, 3컷부터 리듬 상승.

---

# 컨셉 2 · "토플 5,000단어, 방금 나왔습니다" (신제품 · 뉴스형)
신규 토플 단어장 출시를 알리는 제품 훅. 규모감(5,000단어)과 자동 발음·복습을 강조.

**한 줄 메시지:** 토플 5,000단어, 예문·발음·복습까지 다 들어있는 단어장.

| # | 시간 | 화면 | 자막(번인) | 맨트(VO) |
|---|------|------|-----------|----------|
| 1 | 0–2s | 골드 텍스트 타이핑 "TOEFL" + 두근거리는 SFX | **"토플 단어장, 새로 나왔어요"** | "토플 준비하세요? 이거 보고 가세요." |
| 2 | 2–6s | 3권 표지(기본·핵심·고난도) 촤르륵 등장 | **"기본·핵심·고난도 3권 · 5,000단어"** | "기본, 핵심, 고난도. 5,000단어를 난이도별로." |
| 3 | 6–11s | 카드 뒤집기: 학술 예문+해석+🔊발음+어원 | **"예문·발음·유의어·어원까지"** | "토플 지문 톤 예문에, 원어민 발음, 어원까지 전부." |
| 4 | 11–15s | 복습 현황(에빙하우스 1·2·3·6·15·30일) | **"에빙하우스 복습으로 안 까먹게"** | "외운 단어는 망각곡선 복습으로 오래 남게." |
| 5 | 15–19s | "무료 체험 Day 1" 강조 | **"각 권 Day 1 무료 체험"** | "각 권 첫날은 무료. 지금 열어보세요." |
| 6 | 19–23s | 로고 엔드카드 + CTA | **"IM VOCA · imvoca.app"** | "IM VOCA에서 토플, 오늘 시작." |

**AI 영상 생성 프롬프트 (컷별, 영문):**
1. `Vertical 9:16: elegant gold serif letters "TOEFL" typing onto a dark navy background, subtle glow, premium title-card feel.`
2. `Vertical 9:16: three premium vocabulary book covers (labeled Basic, Core, Advanced) fanning into view over a cream backdrop, soft studio light, product-shot aesthetic.`
3. `Vertical 9:16, macro: a flashcard flips to reveal an academic example sentence with Korean translation, a speaker icon, synonyms and etymology, navy & gold UI, crisp push-in.`
4. `Vertical 9:16: a clean review-schedule screen showing spaced-repetition steps (1·2·3·6·15·30 days) filling in, calm satisfying motion.` *(10-ebbinghaus-review.png 합성)*
5. `Vertical 9:16: a glowing "Day 1 · Free" badge highlighted on a wordbook card, inviting tap animation.`
6. `Vertical 9:16: navy end-card, gold "IM VOCA" logo, imvoca.app, soft fade.`

**BGM/페이싱:** 세련된 미니멀 비트, 제품 등장(2컷)에서 임팩트 사운드.

---

# 컨셉 3 · UGC 토킹헤드 "나 이거 없었으면 큰일 날 뻔" (인스타 릴스 특화 · 공감형)
릴스에 잘 먹히는 리얼 톤. 인물이 직접 카메라 보고 말하는 셀피 앵글. 광고 티 덜 나게.

**한 줄 메시지:** 손으로 단어 적던 시간을, AI가 돌려줬다.

**맨트(전체 대본, 셀피로 말하듯):**
> "나 영어 단어 정리를 진짜 손으로 다 적었거든? (한숨)
> 근데 이 앱은… 교재를 그냥 찍어. (찰칵 제스처)
> 그럼 AI가 단어를 뜻이랑 예문까지 딱 정리해줘.
> 심지어 발음도 나오고, 며칠 뒤에 복습하라고 알림도 와.
> 수능·토익·토플 단어장도 그냥 들어있어. 나 진짜 이거 초반에 알았으면…
> 무료로 되니까 일단 교재 한 장만 찍어봐. — IM VOCA."

| # | 시간 | 화면 | 자막(번인) |
|---|------|------|-----------|
| 1 | 0–3s | 인물 셀피, 손으로 노트에 단어 적는 컷 인서트 | **"단어 손으로 적는 사람?"** |
| 2 | 3–7s | 교재 찍는 손 인서트 → 앱 추출 화면 | **"그냥 찍으면 AI가 정리"** |
| 3 | 7–12s | 카드 발음 듣기 + 복습 알림 인서트 | **"발음·예문·복습 알림까지"** |
| 4 | 12–16s | 공식 단어장(수능·토익·토플) 스크롤 | **"수능·토익·토플도 내장"** |
| 5 | 16–20s | 다시 인물, 웃으며 추천 + 엔드카드 | **"무료 · imvoca.app"** |

**AI 영상 생성 프롬프트 (인물/인서트, 영문):**
- 인물: `Vertical 9:16 selfie-style UGC: a friendly Korean woman in her 20s talking to camera in a cozy room, natural daylight, handheld, authentic influencer vibe, subtle smile.`
- 인서트 A: `Vertical 9:16 insert: hand tiredly writing English words into a notebook, then giving up.`
- 인서트 B: `Vertical 9:16 insert: hand photographing a textbook page; cut to phone app extracting words into cards.` *(08 합성)*
- 인서트 C: `Vertical 9:16 insert: finger tapping a speaker icon on a flashcard; a review reminder notification appears.`
- 엔드카드: `Vertical 9:16: gold IM VOCA logo on navy, imvoca.app, "무료 시작".`

**BGM/페이싱:** 트렌디한 릴스 감성 비트(가벼움), 컷 전환 빠르게, 자막은 말 속도에 맞춰 팝.

> 💡 인물 촬영이 어려우면: 실제 사람(사장님/지인/모델) 셀피 영상 + 인서트만 AI/스크린레코딩으로 제작하면 광고 냄새가 확 줄어듭니다.

---

## (보너스) 컨셉 4 · 학원 원장용 B2B 30초
- **훅:** "학생 단어 시험, 아직도 손으로 만드세요?"
- **강점 맨트:** 단어장 배정 → 자동채점 시험(온라인·종이 A/B형) → 학부모에게 학습 리포트 자동 전송 → 진도·복습 한눈에.
- **자막 순서:** 배정 한 번 → 자동채점 → 학부모 리포트 → "원장님은 관리만" → imvoca.app
- **생성 프롬프트 톤:** `clean LMS dashboard on tablet, teacher assigning wordbooks, auto-graded test results, a parent report card being sent via messenger, professional warm office light, vertical 9:16.` *(03-org-dashboard / 06-parent-card 합성)*

---

## 제작 팁 요약
- **첫 1.5초 훅**이 전부 — 질문/문제부터. 로고는 끝에만.
- **UI 컷은 실제 스크린샷 합성**이 AI 순수생성보다 신뢰도 높음 (`wordbooks/promo/shots/07~10`, `screenshot1~4.png`).
- 자막은 **핵심어만 골드 강조**, 나머지 흰색.
- 3종을 A/B로 돌려 반응 좋은 것에 예산 집중.
- 해시태그(예): #영어단어 #단어암기 #토플 #토익 #수능영어 #영어공부앱 #에빙하우스 #IMVOCA
