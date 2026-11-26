# 틱톡 제작 큐

예약 작업(화·금 아침)이 이 파일을 읽어 **다음 것 하나**를 만든다.
만들고 나면 그 줄의 상태를 `done` 으로 바꾸고 날짜·파일명을 적는다.

대본 전문은 `README.md` 4절에 있다. 번호는 거기 번호와 같다.

| # | 대본 | 상태 | 파일 | 날짜 | AI 영상 필요 |
|---|---|---|---|---|---|
| 1 | 내 레벨 몇일까 | **done** | `tiktok-01-leveltest-url.mp4` | 2026-11-25 | 예 (훅 5초) |
| 3 | 이 단어 알면 Lv.9 | todo | | | **아니오** |
| 4 | 왜 외워도 까먹나 (망각곡선) | todo | | | 아니오 |
| 8 | 교재 찍으면 단어장 (AI 스캔) | todo | | | 예 |
| 5 | 20단어 × 20일 = 400단어 | todo | | | 아니오 |
| 6 | 명예의 전당 | todo | | | 아니오 |
| 9 | 발음까지 | todo | | | 아니오 |
| 10 | 공짜인데 이정도 | todo | | | 아니오 |
| 7 | 연속 며칠 | todo | | | 아니오 |
| 2 | 친구랑 대결 | todo | | | 예 |

순서는 **전환이 잘 될 것 같은 것 → 양산이 쉬운 것** 기준으로 정렬했다.
3번(이 단어 알면 Lv.9)은 단어만 바꿔 무한 반복이 되므로, 큐가 바닥나면
3번을 다른 단어로 다시 만들면 된다.

## 규칙

- **한 번에 하나만** 만든다.
- `AI 영상 필요 = 아니오` 인 것은 **크레딧을 쓰지 않는다** (앱 화면 스틸만으로 만든다).
- AI 영상이 필요한 것은 80크레딧/5초다. 잔액이 400 미만이면 만들지 말고
  크레딧 없이 되는 다음 항목으로 건너뛴 뒤 사용자에게 알린다.
- AI 소재가 1초라도 들어가면 발행 폼에서 `is_aigc: true` 를 켠다.

## 영상 만드는 법 (이 세션에서 확립된 방법)

1. **앱 화면은 스틸로 찍는다.** Playwright `recordVideo` 는 뷰포트를 프레임
   크기로 키우지 않아서 1080×1920 프레임의 좌상단에만 그려진다.
   `deviceScaleFactor: 3` + `viewport 390×694` → 1170×2082 스틸을 찍어
   concat 으로 이어 붙이면 훨씬 선명하다.
2. 한국어로 띄우려면 `addInitScript` 로
   `localStorage.setItem('imvoca.nativeLang','ko')` 를 먼저 심는다.
   브라우저 로케일만으로는 영어로 뜬다.
3. 자막 폰트는 Noto Sans KR Bold 를 Google Fonts 에서 받는다
   (`curl -A "Mozilla/4.0" "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700"`
   → 구형 UA 에 woff2 가 아닌 ttf 를 준다. freetype 은 woff2 를 못 읽는다).
   컨테이너 기본 한글 폰트(WenQuanYi·Unifont)는 품질이 안 나온다.
4. 자막은 화면 위쪽(y 200~450)에 둔다. 틱톡 UI 가 아래 20%·오른쪽을 가린다.
5. 1080×1920 · H.264 · 30fps · 3초 이상.

## ⚠️ 영상 끝에 주소 카드를 반드시 넣는다

틱톡은 **캡션의 URL 을 링크로 만들지 않는다.** 바이오 링크도 클릭되려면
'인증된 비즈니스 계정'(서류 심사)이어야 한다. 지금 계정은 개인이라 둘 다 글자다.
그래서 캡션에 주소를 써도 사람들이 들어올 길이 사실상 없다 —
1번 영상을 그렇게 올렸다가 뒤늦게 알았다.

**사람들은 캡션을 안 읽고 화면을 본다.** 영상 마지막 2.8초에 주소 카드를 붙인다.

```bash
# 엔드카드 만들기 (네이비 배경 + 로고 + 주소)
convert -size 1080x1920 "xc:#1E3754" \
  \( icon/profile-navy-zoom-1024.png -resize 300x300 \) -gravity north -geometry +0+520 -composite base.png
convert base.png -font <NotoSansKR-Bold.ttf> -gravity north \
  -pointsize 62  -fill '#ffffff' -annotate +0+900  '<한 줄 카피>' \
  -pointsize 112 -fill '#E8C87A' -annotate +0+1030 'imvoca.app/tt' \
  -pointsize 46  -fill '#9fb3cc' -annotate +0+1200 '4,800단어 · Lv.1~12 · 무료' endcard.png
# 본편 뒤에 2.8초 붙이기 (fade 쓰지 말 것 — t=in 은 지정 시각 '이전'을 그 색으로 덮는다)
```

사업자 인증이 끝나 클릭되는 바이오 링크가 생기면, 그때는 엔드카드를
'프로필 링크' 로 바꿔도 된다. 그 전까지는 주소를 박는다.

## 발행

`media_upload` → curl PUT → `media_confirm` → `tiktok_prepare_publish`
(`mode: DIRECT_POST` — 음원은 드래프트에서 보존되지 않는다).

음원은 `tiktok_music_trending` (country_code KR) 에서 고르고, 미리듣기를
받아 1초 단위 LUFS 를 재서 **가장 꽉 찬 구간의 시작 초**를 알려준다.
인트로·아웃트로는 조용해서 숏폼 앞 2초를 죽인다.

⚠️ **마지막 제출은 사용자가 한다.** `tiktok_publish` 를 직접 부르지 않는다.
대화창의 답변을 동의로 바꾸지 않는다. 틱톡 정책이다.
