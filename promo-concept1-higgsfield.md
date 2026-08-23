# 🎬 컨셉 1 「찰칵 한 장의 마법」 — Higgsfield 제작용 상세 프롬프트

- **포맷:** 세로 9:16 · 총 ~22초 · 6컷
- **제작 흐름(Higgsfield):** 컷별로 ① **Text-to-Image**(또는 실제 스크린샷 업로드)로 시작 프레임 → ② **Image-to-Video** + **모션/카메라 프리셋**으로 3~5초 클립 → ③ 편집기에서 트림·자막·음악.
- **UI 컷(3·5·6)은 AI 생성 대신 실제 스크린샷 업로드** 권장 → Image-to-Video로 미세 모션만. (신뢰도·정확도↑)
  - 소재: `wordbooks/promo/shots/08-ai-word-extract.png`(단어 저장 화면) · `09-flashcard-study.png`(암기카드) · 로고 `2.png`
- **인물은 손/POV만** 등장(얼굴 X) → 컷 간 인물 일관성 문제 회피.

---

## 🎨 전역 스타일 (모든 이미지 프롬프트 끝에 붙일 것)
```
Style: cinematic, premium ad, vertical 9:16, shot on 35mm, shallow depth of field f/1.8,
warm practical lamp key light with soft navy rim, color grade — deep navy shadows + warm gold highlights on cream,
fine film grain, high detail, no text, no watermark, natural realistic hands.
```
**Negative(피할 것):** `text, captions, watermark, logo, extra fingers, deformed hands, plastic skin, oversaturated, cluttered background, low-res`

**색/톤 기준:** 네이비 #1c3553 · 골드 #c98a3a · 크림 #f5f1e8

---

## 컷 1 · 0–2.5s — "문제 제시" (감성 몰입)
- **자막(번인):** 단어 정리, 아직도 **손으로** 하세요?
- **맨트(VO):** "단어 하나하나 찾아 적는 거… 이제 그만."
- **화면:** 늦은 밤 책상, 형광펜 가득한 영어 교재. 모르는 단어 위에 멈춘 손가락, 살짝 힘 빠진 정지.
- **Higgsfield 모션 프리셋:** `Slow Push In` (아주 느린 전진) · 강도 낮게
- **이미지 프롬프트(붙여넣기용):**
```
Cozy late-night study desk, an open English textbook densely covered with yellow highlighter,
a young person's fingertip pausing on one unknown word, faint tiredness, warm desk lamp glow,
navy darkness around the edges, extreme shallow focus on the word.
[전역 스타일 붙이기]
```
- **SFX:** 조용한 방 앰비언스 + 아주 작은 한숨.

## 컷 2 · 2.5–5.5s — "행동: 찰칵" (밝아지는 전환)
- **자막:** 교재를 **그냥 찍으세요**
- **맨트:** "그냥 교재를 찍기만 하면,"
- **화면:** 손이 스마트폰을 들어 교재 페이지를 촬영. 셔터 순간 화면 전체가 밝게 확 트임.
- **Higgsfield 모션 프리셋:** `Snap/Crash Zoom In` (셔터 순간 살짝 크래시 줌) → 밝기 상승과 싱크
- **이미지 프롬프트:**
```
A hand raising a smartphone to photograph the highlighted textbook page from above,
the phone screen showing the camera viewfinder over the book, a bright hopeful light blooming into the frame
at the moment of the shutter, hopeful mood shifting from dim to bright.
[전역 스타일 붙이기]
```
- **SFX:** 카메라 셔터 '찰칵' + 부드러운 whoosh.

## 컷 3 · 5.5–10s — "핵심 마법: 자동 정리" (실제 스크린샷)
- **자막:** AI가 **뜻·발음·예문**까지 자동
- **맨트:** "AI가 어려운 단어만 골라, 뜻과 발음, 예문까지 자동으로."
- **화면:** 앱 단어 화면 — 단어 카드가 뜻·🔊발음·예문·CEFR과 함께 정렬.
- **제작:** `08-ai-word-extract.png` **업로드** → Image-to-Video
- **Higgsfield 모션 프리셋:** `Slow Push In` + 목록이 위→아래로 살짝 채워지는 느낌(parallax/reveal)
- **Image-to-Video 모션 프롬프트:**
```
Subtle slow push-in on a clean vocabulary app screen; word cards gently settle into place one by one,
a soft speaker icon pulse on one card, premium navy & gold UI, smooth and satisfying, no camera shake.
```
- **SFX:** 부드러운 '팝·팝' UI 사운드 3~4개.

## 컷 4 · 10–13.5s — "여러 장 한 번에" (속도감)
- **자막:** 여러 장도 **한 번에**
- **맨트:** "여러 페이지도 한 번에 끝나요."
- **화면:** 엄지가 여러 장의 교재 사진을 빠르게 넘기고, 각 장이 단어 카드로 촥촥 변환.
- **Higgsfield 모션 프리셋:** `Whip Pan` 또는 `Fast Swipe` (좌→우 빠른 전환)
- **이미지 프롬프트:**
```
A thumb quickly swiping through a stack of several textbook photos on a phone,
each photo instantly transforming into neat vocabulary cards, dynamic motion trails, energetic rhythm,
navy & gold app aesthetic.
[전역 스타일 붙이기]
```
- **SFX:** 빠른 스와이프 whoosh ×3, 리듬 상승.

## 컷 5 · 13.5–17.5s — "복습 알림" (안심·미소) (실제 스크린샷)
- **자막:** 잊을 때쯤 **복습 알림**까지
- **맨트:** "그리고 잊을 때쯤, 복습 알림이 딱."
- **화면:** 암기카드 넘기는 화면 위로 상단에서 복습 알림 배너가 슬라이드 인.
- **제작:** `09-flashcard-study.png` **업로드** → Image-to-Video (상단에 알림 배너 합성은 편집기에서 추가해도 OK)
- **Higgsfield 모션 프리셋:** `Slow Push In` + 상단 배너 slide-down
- **Image-to-Video 모션 프롬프트:**
```
Gentle push-in on a flashcard study screen; a small review reminder notification slides down from the top
and rests briefly, calm reassuring mood, warm light, no shake.
```
- **SFX:** 알림 '딩' 한 번(부드럽게).

## 컷 6 · 17.5–22s — "엔드카드 · CTA" (실제 로고)
- **자막:** IM VOCA · **무료 시작** · imvoca.app
- **맨트:** "교재만 찍어보세요. IM VOCA."
- **화면:** 네이비 배경, 골드 IM VOCA 로고, imvoca.app, "무료로 시작".
- **제작:** 로고 `2.png` 업로드 → 배경만 생성/합성
- **Higgsfield 모션 프리셋:** `Subtle Zoom In` + 로고 fade-in (아주 느리게)
- **배경 이미지 프롬프트(로고 제외):**
```
Minimal deep-navy background with subtle paper-grain and a faint soft gold light from top,
empty center reserved for a logo, elegant premium end-card, vertical 9:16.
[전역 스타일 붙이기 — 단, 'no text' 유지: 로고/문구는 편집기에서 얹기]
```
- **SFX:** 짧은 골드 chime + 여운.

---

## 🎵 음악 · 페이싱
- **BGM:** 밝고 따뜻한 로파이 (첫 60~70 BPM → 컷3부터 살짝 상승). 컷2 셔터에서 살짝 밝아지는 전환점.
- **컷 길이:** 대사·자막에 맞춰 위 타이밍대로 트림. 각 힉스필드 클립은 넉넉히 3~5초 뽑고 편집에서 컷.
- **전환:** 컷1→2 밝기 컷, 컷3·4는 빠른 컷, 컷5→6 부드러운 디졸브.

## 🔤 자막(캡션) 스타일
- 위치: 하단 1/3, 굵은 산세리프(예: Pretendard/노토 산스 Bold)
- 색: 흰색 + **핵심어만 골드(#c98a3a)** — "손으로 / 그냥 찍으세요 / 뜻·발음·예문 / 한 번에 / 복습 알림 / 무료 시작"
- 등장: 대사에 맞춰 단어 단위 팝(0.1~0.2s)

## 📤 내보내기
- 해상도 1080×1920, 24 또는 30fps, mp4(H.264)
- 유튜브 쇼츠/릴스/틱톡 동일 업로드
- 해시태그: #영어단어 #단어암기 #영어공부앱 #토플 #토익 #수능영어 #에빙하우스 #IMVOCA

## 붙여넣기용 자막 리스트
1. 단어 정리, 아직도 손으로 하세요?
2. 교재를 그냥 찍으세요
3. AI가 뜻·발음·예문까지 자동
4. 여러 장도 한 번에
5. 잊을 때쯤 복습 알림까지
6. IM VOCA · 무료 시작 · imvoca.app

## 붙여넣기용 맨트(나레이션) 스크립트
"단어 하나하나 찾아 적는 거… 이제 그만.
그냥 교재를 찍기만 하면,
AI가 어려운 단어만 골라, 뜻과 발음, 예문까지 자동으로.
여러 페이지도 한 번에 끝나요.
그리고 잊을 때쯤, 복습 알림이 딱.
교재만 찍어보세요. IM VOCA."
