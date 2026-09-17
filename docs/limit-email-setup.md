# '무료 스캔 소진' 안내 메일 — 설정

앱스토어 가이드라인 3.1.1 때문에 **iOS 앱 안에서는 가격도 결제 링크도 보여줄 수 없습니다.**
그러면 무료 10장을 다 쓴 사용자는 "어디서 결제하지?" 하고 그냥 이탈합니다.

**애플 규정은 앱 안만 규율하고, 이메일은 자유입니다.** 그래서 막힌 직후 메일로 안내합니다.
한 사람에게 **평생 1회만** 가고, 수신거부하면 영구히 제외됩니다.

---

## 1. Resend — 보내는 도메인  ✅ 이미 완료

`imvoca.app` 이 Resend 에 **Verified** 로 등록돼 있습니다(2026-05 경 설정, Supabase
인증 메일이 이미 이 경로로 나가는 중). **DNS 를 새로 넣을 필요가 없습니다.**

확인된 상태:

| 용도 | 레코드 | 값 |
|---|---|---|
| 받기 | `imvoca.app` MX | `eforward1~5.registrar-servers.com` (Namecheap 포워딩) |
| 보내기 SPF | `send.imvoca.app` TXT | `v=spf1 include:amazonses.com ~all` |
| 보내기 DKIM | `resend._domainkey.imvoca.app` TXT | 설정됨 |
| 정책 | `_dmarc.imvoca.app` TXT | `v=DMARC1; p=none;` |

받기(루트 MX)와 보내기(`send` 서브도메인 + DKIM)가 서로 다른 이름에 있어 **충돌하지
않습니다.** `admin@imvoca.app` 수신은 그대로 유지됩니다.

> 선택: `send.imvoca.app` 의 MX(반송 처리용)가 비어 있습니다. 없어도 발송은 되지만,
> 넣어두면 반송·스팸신고 처리가 정확해집니다. Resend 도메인 화면의 **Records** 탭에
> 있는 MX 한 줄을 Namecheap 에 `Host = send` 로 추가하면 됩니다.

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
| `MAIL_FROM` | `IM VOCA <noreply@imvoca.app>` |
| `MAIL_REPLY_TO` | `admin@imvoca.app` (선택 — 기본값 동일) |
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
