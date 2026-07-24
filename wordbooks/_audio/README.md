# 예문 발음 오디오 — 시리즈별 분리

## 문제
같은 단어(예: `study`)가 **수능·중등·토익에 서로 다른 예문**으로 들어 있는데,
예문 발음 MP3는 단어명 하나(`s/study.mp3`)로만 저장돼 **한 시리즈 예문에만 맞고
나머지는 화면 예문과 어긋났음.** (수능 4권 내부끼리는 안 겹침 — 겹침은 중등/토익과 발생)

## 해결 구조 (앱은 이미 배포됨)
예문 발음을 **시리즈별 폴더**로 분리해서 읽습니다:
- `audio/s/suneung/{word}.mp3` (수능 4권 공통 — 내부 충돌 0)
- `audio/s/mid/{word}.mp3` (중등 — 내부 충돌 0)
- `audio/s/toeic/{word}.mp3` (토익)
- 스페인어는 기존 `audio/es/s/{word}.mp3` 유지
- 단어 자체 발음 `audio/w/{word}.mp3` 는 어느 책이든 동일하므로 그대로.

**파일이 아직 없으면** 앱이 자동으로 그 예문 텍스트를 **기기 TTS**로 읽어
**항상 화면과 일치**합니다. 아래로 원어민 MP3를 채우면 자동으로 원어민 음성으로 전환됩니다.

## 매니페스트
- `suneung.json` (4313), `mid.json` (1800), `toeic.json` (2443), `es.json` (1437)
- 각 항목: `{ "w": 파일명(safe), "en": 단어, "s": 예문 }`
- 시리즈 내부 충돌: 수능 0 · 중등 0 · 토익 32 · es 63 (충돌분은 대표 예문 1개만 녹음, 나머지는 TTS)

## 원어민 MP3 생성·업로드
```bash
export GOOGLE_TTS_KEY=...          # Google Cloud Text-to-Speech
export SUPABASE_URL=https://xxxx.supabase.co
export SUPABASE_SERVICE_KEY=...    # service_role
node generate.mjs suneung          # 수능부터
node generate.mjs mid toeic        # 이어서
```
- 이미 있는 파일은 건너뜀(중단 후 재실행 안전).
- 다른 TTS(기존 Gemini TTS 등)를 쓰려면 `generate.mjs` 의 `synth()` 만 교체.
