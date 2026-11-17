# tts-he-oneshot — 히브리어 음원 일회용 생성기 (역할 끝)

2026-11-17 에 한 번 돌려 알레프벳 22자의 음원 44개를 만들었다.
글자 이름 22 + 예시 단어 22 → `audio/he/w/*.mp3` · `audio/he/s/*.mp3`

**지금은 사용 중지 상태다(410 반환).** 배포된 코드는 `index.ts`,
실제로 생성을 수행했던 코드는 `generator.ts` 에 남겨 뒀다.
Supabase 대시보드에서 삭제해도 상관없다 — 삭제하는 것이 맞다.

## 왜 별도 함수였나

`tts` 함수는 영어 전용이다. `VOICE` 가 `en-US` 로 고정돼 있고, 파일명을
만드는 `safeName()` 이 ASCII 밖을 전부 버린다(`א` → 빈 문자열). 거기를
손대면 전체 영어 음원 경로가 위험해지는데, 히브리어는 22자뿐이고 한 번
만들면 끝이라 따로 올려 한 번 돌리는 쪽이 안전했다.

## 왜 인증 없이 열어도 괜찮았나

- 쓸 수 있는 경로가 DB 의 `analysis._lang='he'` 단어에서 유도된 44개로 고정
- 이미 있는 파일은 건너뛴다 → 한 번 돌고 나면 누가 불러도 아무 일도 안 한다
- 읽어서 돌려주는 민감 정보가 없다

## 다시 만들 일이 생기면

글자 이름(`AUDIO` 표)이나 예시 단어를 고친 경우다. 이 함수를 되살리지 말고
레포의 스크립트를 터미널에서 돌린다 — 키가 대화나 서버에 남지 않는다:

```bash
cd wordbooks/hebrew && python3 build-alefbet.py
cd ../tools
export SB_URL="https://ziatqkjlafucqtwshhla.supabase.co"
export SB_SERVICE_KEY="..."     # 터미널에만
export GOOGLE_TTS_KEY="..."     # 터미널에만
python3 tts_hebrew.py --go --force
```

예문을 고쳤으면 파일명 해시가 바뀌므로 옛 파일은 고아가 된다(앱은 새 해시를
찾으니 동작엔 문제없다). 스토리지를 정리하려면 `audio/he/s/` 를 비우고 다시 올린다.
