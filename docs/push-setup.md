# 복습 알림(웹 푸시) 설정 — 1회 작업

앱 아이콘에 배지 숫자를 띄우려면 알림을 보내야 합니다.
**안드로이드는 `setAppBadge()` 를 지원하지 않고**, "읽지 않은 알림이 있으면 OS 가 배지를 붙이는" 구조이기 때문입니다.
(iOS 16.4+ / PC 설치형은 `setAppBadge()` 로 숫자까지 직접 찍습니다.)

코드는 전부 들어가 있고, 아래 4단계만 하시면 켜집니다.

---

## 1. VAPID 키 만들기 (1분)

푸시 서버에 "이 알림이 IM VOCA 가 보낸 게 맞다"고 증명하는 키 쌍입니다.

```bash
npx web-push generate-vapid-keys
```

출력 예시:

```
Public Key:   BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkFbx6...
Private Key:  8eDyX_uCN0XRhSbY5hs7Hg9Nw1a84ndDvWq...
```

> 🔐 **Private Key 는 절대 git 에 올리지 마세요.** Supabase 시크릿에만 넣습니다.
> Public Key 는 앱에 들어가는 값이라 공개돼도 괜찮습니다.

---

## 2. 공개키를 앱에 넣기

`index.html` 에서 이 줄을 찾아 Public Key 를 채웁니다.

```js
const VAPID_PUBLIC_KEY = '';   // ← 여기에 Public Key
```

**비어 있으면 알림 기능이 My 메뉴에서 아예 안 보입니다.** (설정 전에 사용자가 눌러서 실패하는 걸 막으려고 그렇게 해뒀습니다.)

채운 뒤 평소처럼 배포하면 웹·PC·아이폰(홈 화면 추가)에서 바로 작동합니다.

---

## 3. DB + 엣지 함수 배포

**① 테이블·집계 함수** — Supabase SQL Editor 에 `supabase/push-subscriptions.sql` 내용을 붙여넣고 실행.

**② 시크릿 등록**

```bash
supabase secrets set VAPID_PUBLIC_KEY="BEl62iUY..." \
                     VAPID_PRIVATE_KEY="8eDyX_uC..." \
                     VAPID_SUBJECT="mailto:support@imvoca.app"
```

**③ 함수 배포**

```bash
supabase functions deploy send-review-push
```

**④ 잘 되는지 바로 확인** (시간 조건을 무시하고 즉시 발송)

```bash
curl -X POST "https://<프로젝트>.supabase.co/functions/v1/send-review-push" \
  -H "Authorization: Bearer <SB_SERVICE_ROLE_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"force":true}'
```

응답 예: `{"ok":true,"sent":1,"skipped":0,"dropped":0,"failed":[]}`

> 본인 계정으로 먼저 My → 🔔 복습 알림 → 켜기 를 해두고 테스트하세요.
> 복습할 단어가 하나도 없으면 `no_due_reviews` 가 나옵니다 — 정상입니다.

---

## 4. 매시간 자동 발송 걸기

Supabase SQL Editor 에서 실행합니다. `<프로젝트>` 와 `<SB_SERVICE_ROLE_KEY>` 를 채우세요.

```sql
select cron.schedule('imvoca-review-push', '0 * * * *', $cron$
  select net.http_post(
    url     := 'https://<프로젝트>.supabase.co/functions/v1/send-review-push',
    headers := jsonb_build_object('Authorization', 'Bearer <SB_SERVICE_ROLE_KEY>',
                                  'Content-Type', 'application/json'),
    body    := '{}'::jsonb
  );
$cron$);
```

**왜 매시간인가** — 사용자마다 시간대와 원하는 시각이 다릅니다. cron 은 매시간 깨우고,
누구에게 보낼지는 함수가 각 구독의 `tz` / `send_hour` 를 보고 판단합니다.
텍사스 사용자가 아침 9시를 골랐으면 텍사스 시각 9시에만 갑니다.

잡 확인·삭제:

```sql
select * from cron.job;
select cron.unschedule('imvoca-review-push');
```

---

## 5. 안드로이드 앱에서 켜려면 — `.aab` 재빌드 필요

TWA 가 웹 알림을 안드로이드 알림으로 넘기려면 **알림 위임(notification delegation)** 이 켜져 있어야 합니다.

1. [PWABuilder](https://www.pwabuilder.com) 에서 `https://imvoca.app` 재패키징
2. 옵션에서 **"Enable notifications"** 체크 (Android 13+ `POST_NOTIFICATIONS` 권한이 같이 들어갑니다)
3. **Package ID 는 반드시 `app.imvoca.twa`** — 바뀌면 기존 사용자가 업데이트를 못 받습니다
4. 새 `.aab` 를 Play Console 프로덕션에 업로드 → 앱 심사 (1~3일)

> 이 단계 전까지는 **웹·PC·아이폰(홈 화면 추가)** 에서만 알림이 옵니다.
> Play 스토어에서 받은 안드로이드 앱은 재빌드 후부터 작동합니다.

---

## 동작 정리

| 플랫폼 | 알림 | 아이콘 배지 |
|---|---|---|
| 안드로이드 (Play 앱, 재빌드 후) | ✅ | OS 자동 — 런처에 따라 숫자 또는 점 |
| 아이폰 (Safari → 홈 화면에 추가, iOS 16.4+) | ✅ | ✅ 숫자 |
| PC (Chrome·Edge 설치형) | ✅ | ✅ 숫자 |
| 그냥 브라우저로 접속 | ✅ | ❌ (아이콘이 없으니 배지도 없음) |

**보내는 조건**: 복습할 단어가 1개 이상 있고, 현지 시각이 사용자가 고른 시각이며, 오늘 아직 안 보냈을 때.
하루 최대 1번만 갑니다. 구독이 죽으면(앱 삭제·권한 해제) 자동으로 정리됩니다.
