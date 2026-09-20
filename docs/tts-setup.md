# 단어 발음 음성 만들기 (Google Cloud TTS)

아이폰은 웹에서 쓸 수 있는 음성이 시스템 기본 몇 개로 막혀 있다(애플 제한).
설정에서 고품질 음성을 받아도 웹에는 적용되지 않는다. 그래서 **서버에서 한 번
만들어 저장**해 두고 모두가 그 파일을 쓴다.

## 왜 비용이 안 늘어나는가

- 음성은 **단어당 한 번**만 만들고 Supabase Storage 에 영구 저장된다.
  1만 명이 1만 번 들어도 생성 비용은 0이다.
- **우리 사전(voca_words)에 있는 단어만** 만든다 → 평생 만들 수 있는 최대치가
  사전 크기(약 1만 5천 단어)로 묶인다. OCR 오인식도, 악용도 그 위를 못 넘는다.
- Google Cloud TTS Neural2 는 **매달 100만 자 무료**. 사전 전체가 약 10만 자라
  무료 한도의 1/10이다.
- 예문도 만들 수 있다(`kind:"s"`). 글자 수가 10배라 비용이 크므로 단어를 먼저
  끝내고, 실제 글자 수를 세어 무료 한도 안인지 확인한 뒤에 돌린다:

```sql
select count(*) as 만들_예문수, sum(length(sentence)) as 총_글자수,
       round(sum(length(sentence)) / 1000000.0, 2) as 백만자_대비
from (select distinct lower(en) as w, sentence from voca_words
      where sentence is not null and sentence <> ''
        and coalesce(analysis->>'_official','') <> 'true'
        and en ~ '^[A-Za-z][A-Za-z '' -]*$') t;
```

## 1) Google Cloud 키 발급

1. https://console.cloud.google.com 에서 프로젝트 생성
2. **Cloud Text-to-Speech API** 검색 → **사용 설정(Enable)**
   (결제 계정 연결이 필요하다. 무료 한도 안에서는 청구되지 않는다)
3. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 → API 키**
4. 만든 키를 눌러 **키 제한**을 반드시 걸어둔다:
   - 애플리케이션 제한: 없음 (서버에서 호출)
   - **API 제한: Cloud Text-to-Speech API 만 선택**

## 2) 시크릿 등록

```bash
supabase secrets set GOOGLE_TTS_KEY="<발급받은 키>" --project-ref ziatqkjlafucqtwshhla
```

목소리를 바꾸고 싶으면 (선택):
```bash
supabase secrets set TTS_VOICE="en-US-Neural2-C" --project-ref ziatqkjlafucqtwshhla
```
후보: `en-US-Neural2-C`(여성·기본) · `en-US-Neural2-D`(남성) ·
`en-US-Neural2-F`(여성) · `en-US-Chirp3-HD-Aoede`(더 자연스럽지만 $30/100만 자)

## 3) 배포

```bash
cd ~/voca && git pull
supabase functions deploy tts --project-ref ziatqkjlafucqtwshhla
```

## 4) 사전 단어 미리 채우기 (선택, 권장)

미리 채워두면 사용자가 처음 듣는 순간부터 서버 음성이 나온다.
채우지 않아도 동작한다 — 처음 한 번만 기기 음성으로 들리고, 그 사이 만들어진다.

한 번에 최대 300개씩. `next_offset` 을 넘겨가며 `done: true` 가 나올 때까지 반복:

```bash
OFF=0; N=0
while :; do
  R=$(curl -s -X POST "https://ziatqkjlafucqtwshhla.supabase.co/functions/v1/tts" \
      -H "Authorization: Bearer $SR" -H "Content-Type: application/json" \
      -d "{\"bulk\":true,\"kind\":\"w\",\"limit\":1000,\"max_new\":80,\"offset\":$OFF}")
  echo "$R" | head -c 160; echo
  M=$(echo "$R" | sed -n 's/.*"made":\([0-9]*\).*/\1/p'); N=$((N+${M:-0}))
  echo "$R" | grep -q '"done":true' && { echo "✅ 완료 — 만든 음성 $N 개"; break; }
  OFF=$(echo "$R" | sed -n 's/.*"next_offset":\([0-9]*\).*/\1/p')
  [ -z "$OFF" ] && break
done
```

예문은 `"kind":"w"` 를 `"kind":"s"` 로 바꾸면 된다.

응답: `{"ok":true,"made":80,"skipped":896,"next_offset":1000,"still_todo_here":24,"done":false}`
- `next_offset` 이 그대로면 그 구간에 만들 게 남은 것(`still_todo_here`) — 같은 구간을 한 번 더 돈다
- `done:true` 는 빈 구간이 나왔을 때만 (표 끝)

## 확인

앱에서 직접 스캔한 단어의 🔊 를 누른다.
- 처음: 기기 음성으로 들리고, 뒤에서 파일이 만들어진다
- 잠시 뒤 다시 누르면: 서버 음성(또렷한 미국 발음)

Storage → `audio` 버킷 → `w/` 폴더에 mp3 가 쌓이는지 보면 된다.

## 끄고 싶을 때

`GOOGLE_TTS_KEY` 시크릿을 지우면 생성이 멈춘다. 이미 만들어진 파일은 계속 쓰인다.
