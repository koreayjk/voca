# '무료 스캔 소진' 안내 메일 — 설정

앱스토어 가이드라인 3.1.1 때문에 **iOS 앱 안에서는 가격도 결제 링크도 보여줄 수 없습니다.**
그러면 무료 10장을 다 쓴 사용자는 "어디서 결제하지?" 하고 그냥 이탈합니다.

**애플 규정은 앱 안만 규율하고, 이메일은 자유입니다.** 그래서 막힌 직후 메일로 안내합니다.
한 사람에게 **평생 1회만** 가고, 수신거부하면 영구히 제외됩니다.

---

## 1. Resend — 보내는 도메인 등록

> 💡 **서브도메인(`send.imvoca.app`)으로 하세요.** 그러면 지금 쓰시는
> **Namecheap 메일 포워딩(받기)을 건드리지 않고** 보내기만 추가됩니다.
> 루트 도메인으로 잡으면 MX 가 충돌해 `admin@imvoca.app` 수신이 끊길 수 있습니다.

1. https://resend.com/domains → **Add Domain** → `send.imvoca.app`
2. 화면에 뜨는 DNS 레코드(보통 3줄: MX 1, TXT 2)를 **Namecheap → Advanced DNS** 에 추가
3. Resend 에서 **Verified** 로 바뀔 때까지 대기 (보통 몇 분~1시간)

---

## 2. DB

Supabase SQL Editor 에 `supabase/limit-email.sql` 전체 실행.

추가되는 것: `members.limit_email_sent_at` / `email_optout_at` / `email_token` / `native_lang`
와 발송 대상 조회 함수 `limit_email_targets()`.

---

## 3. 시크릿 4개

Supabase → **Edge Functions → Secrets**

| 이름 | 값 |
|---|---|
| `RESEND_API_KEY` | Resend API 키 (`re_...`) |
| `MAIL_FROM` | `IM VOCA <noreply@send.imvoca.app>` — **2번에서 인증한 도메인이어야 합니다** |
| `MAIL_POSTAL_ADDRESS` | 공개해도 되는 우편 주소 (아래 ⚠️) |
| `PUBLIC_SITE_URL` | `https://imvoca.app` (선택, 기본값 동일) |

> ⚠️ **`MAIL_POSTAL_ADDRESS` 는 필수입니다.** CAN-SPAM 은 상업성 메일에 실제 우편
> 주소를 요구합니다. 이 값이 없으면 함수가 **일부러 발송을 거부**합니다.
>
> 그리고 이 주소는 **모든 사용자에게 공개**됩니다. 등록사무소가 자택이면 그 주소
> 대신 **사서함(PO Box)이나 메일박스 서비스 주소**를 쓰세요.

---

## 4. 배포

```bash
supabase functions deploy send-limit-email
supabase functions deploy email-optout --no-verify-jwt   # ← 반드시 이 옵션
```

> `--no-verify-jwt` 를 빠뜨리면 Supabase 가 Authorization 헤더를 요구해서,
> **메일에서 누른 수신거부 링크가 401 로 막힙니다.** CAN-SPAM 위반이 됩니다.

---

## 5. 테스트

본인 계정을 무료·스캔 10장 상태로 만든 뒤:

```bash
curl -X POST "https://ziatqkjlafucqtwshhla.supabase.co/functions/v1/send-limit-email" \
  -H "Authorization: Bearer <SB_SERVICE_ROLE_KEY>" \
  -H "Content-Type: application/json" -d '{}'
```

- `{"ok":true,"sent":1,...}` → 성공
- `{"ok":true,"sent":0,"note":"mail_not_configured"}` → 시크릿 미설정
- `{"error":"MAIL_POSTAL_ADDRESS_not_set"}` → 주소 미설정
- `{"ok":true,"sent":0,"note":"no_targets"}` → 대상 없음 (정상)

메일을 받으면 **수신거부 링크도 눌러보세요.** '수신거부 완료' 화면이 떠야 합니다.

---

## 6. 매시간 자동 발송

```sql
select cron.schedule('imvoca-limit-email', '10 * * * *', $cron$
  select net.http_post(
    url     := 'https://ziatqkjlafucqtwshhla.supabase.co/functions/v1/send-limit-email',
    headers := jsonb_build_object('Authorization', 'Bearer <SB_SERVICE_ROLE_KEY>',
                                  'Content-Type', 'application/json'),
    body    := '{}'::jsonb
  );
$cron$);
```

현황 보기:

```sql
select count(*) filter (where limit_email_sent_at is not null) as 보냄,
       count(*) filter (where email_optout_at    is not null) as 수신거부
from members;
```

---

## 발송 조건 (한 곳에 모아둠 — `limit_email_targets()`)

- 무료 플랜이고
- 무료 스캔 10장을 다 썼고
- 아직 안 보냈고, 수신거부도 안 했고
- 이메일이 있고
- **단체(학원) 소속 승인 학생이 아니다** — 학원이 결제하는 구조라 "프리미엄 사세요" 가 가면 안 됩니다

한 번에 최대 25명씩 보냅니다. 실패한 사람은 표시를 남기지 않아 다음 시간에 다시 시도됩니다.
