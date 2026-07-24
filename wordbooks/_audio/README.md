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

## 재사용 전략 (중복만 생성)
- **유니크 단어 4,957개(75%)**: 시리즈 간 예문이 안 갈림 → **기존 원어민 `s/{단어}.mp3` 그대로 사용**(앱이 자동으로). 생성 불필요.
- **중복 단어 1,624개**: 시리즈마다 예문이 다름 → 시리즈별로 새로 생성해야 함.
- 앱은 `conflict-words.json`(중복 단어 목록)을 읽어, 중복 단어만 `s/{series}/` 에서, 나머지는 기존 `s/{단어}.mp3` 에서 재생.

## 매니페스트
- `conflict-words.json` — 중복 단어(safeword) 목록. 앱이 로드.
- `gen-suneung.json` (1531), `gen-mid.json` (945), `gen-toeic.json` (1123) — **생성 대상**(중복 단어 예문). `{ "w", "s" }`
- (참고 전체본: `suneung.json`/`mid.json`/`toeic.json`/`es.json`)

## 원어민 MP3 생성 (저장소 호스팅)
중복 단어 예문 오디오는 **저장소 `/audio/s/{series}/`** 에 저장 → GitHub Pages 가
`imvoca.app/audio/s/{series}/{word}.mp3` 로 서빙. 앱은 `_REPO_AUDIO_BASE` 로 여기서 읽음.
```bash
export GOOGLE_TTS_KEY=...           # Google Cloud Text-to-Speech (무료 한도 안)
node generate.mjs suneung mid toeic # 생성 → /audio/s/{series}/ 에 저장
git add audio/ && git commit -m "add series audio" && git push
```
- 이미 있는 파일은 건너뜀(중단 후 재실행 안전). Supabase 키 불필요.
- **완료 현황**: 수능 1531 · 중등 945 · 토익 1123 생성 완료(2026-07). 유니크 단어는 기존 원어민 재사용.
- 다른 TTS 를 쓰려면 `generate.mjs` 의 `synth()` 만 교체.
