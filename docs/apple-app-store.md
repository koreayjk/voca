# 애플 앱스토어 등록 — 맥북 작업 순서

구글 플레이(TWA)는 **웹사이트를 감싼 껍데기**였습니다. `git push` 하면 앱에도 바로 반영됐죠.
애플은 그게 안 됩니다. 가이드라인 **4.2 (Minimum Functionality)** 가 "웹사이트를 그대로 감싼 앱"을
반려하기 때문에, iOS 앱은 **화면을 앱 안에 담아서** 배포합니다.

| | 구글 플레이 | 애플 앱스토어 |
|---|---|---|
| 화면 코드 | 웹에서 실시간 | **앱 안에 고정** — 고칠 때마다 Xcode 빌드 + 재심사(1~2일) |
| 단어장·단어·복습·프리미엄 | Supabase 실시간 | Supabase 실시간 (**똑같음**) |
| 공식 단어장 추가 | 서버에서 | 서버에서 (**앱 업데이트 불필요**) |
| 알림 | 웹 푸시 | **APNs**(애플 푸시) |
| 결제 UI | 그대로 노출 | **숨김** (가이드라인 3.1.1) |

즉 **얼어붙는 것은 화면 코드뿐**입니다. 내용·데이터는 지금처럼 서버에서 바로 바뀝니다.

- Bundle ID: **`app.imvoca`** (한 번 정하면 영원히 못 바꿉니다)
- 안드로이드는 `app.imvoca.twa` — 스토어가 다르므로 별개로 존재해도 무방합니다.

---

## 0. 지금 당장 시작해야 하는 것 — Apple Developer 가입 ⏰

**여기가 유일하게 며칠씩 걸리는 구간입니다. 다른 작업보다 먼저 시작하세요.**

- https://developer.apple.com/programs/ → Enroll
- **연 $99, 계정(팀)당입니다.** 앱 개수 제한 없음 — TCS 등 나중 앱도 같은 $99 안에 들어갑니다.
- 법인(IM AMERICA GROUP CORP) 명의로 하려면 **D-U-N-S 번호**가 필요합니다.
  - 없으면 https://developer.apple.com/enroll/duns-lookup/ 에서 무료 발급 — **영업일 기준 5~14일**
  - 개인 명의로 하면 즉시 가능하지만, 스토어에 개인 이름이 노출되고 나중에 법인 이전이 번거롭습니다.
  - 👉 구글 플레이를 법인으로 올리셨으니 애플도 법인 권장. **오늘 D-U-N-S 부터 신청하세요.**

가입이 끝날 때까지 아래 1~3번은 미리 해둘 수 있습니다(무료 계정으로 시뮬레이터 실행까지 가능).

---

## 1. 맥북 준비

**① Xcode** — App Store 앱에서 설치 (약 10GB, 30분~1시간).
설치가 끝나면 **한 번 실행**해서 추가 구성요소 설치를 마치세요.

> `xcode-select --install` 은 **하지 마세요.** Xcode 본체에 커맨드라인 도구가 들어 있습니다.
> 따로 깔면 `xcode-select` 가 Xcode 대신 그쪽을 보게 돼서 나중에 빌드가 실패합니다.

```bash
xcode-select -p
# → /Applications/Xcode.app/Contents/Developer 여야 합니다.
#   /Library/Developer/CommandLineTools 가 나오면 아래로 고치세요:
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer

sudo xcodebuild -license accept   # 안 하면 빌드가 막힙니다
xcodebuild -version
```

**② Node.js** — 이미 깔려 있을 수 있으니 **먼저 확인**하세요.

```bash
node -v
```

- `v20` / `v22` / `v24` → 그대로 쓰면 됩니다.
- 없거나 `v18` 이하 → `brew install node` 후, PATH 에 옛 Node 가 남아 있으면:
  ```bash
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
  source ~/.zprofile && node -v
  ```

> `brew install node` 마지막에 `shadowed by /usr/local/bin/node` 경고가 나오면
> **옛 Node 가 PATH 상 앞에 있다**는 뜻입니다. 위 두 줄로 순서를 바꿔주세요.

> CocoaPods 는 필요 없습니다. Capacitor 8 은 Swift Package Manager 를 쓰므로
> Xcode 가 알아서 의존성을 받아옵니다.

---

## 2. 프로젝트 내려받고 iOS 프로젝트 만들기

**`ios/` 네이티브 프로젝트는 이미 저장소에 들어 있습니다.** 아이콘·스플래시·권한 문구·
URL 스킴·APNs 연결까지 미리 해뒀으니, 받아서 열기만 하면 됩니다.

```bash
git clone https://github.com/koreayjk/voca.git
cd voca
git checkout claude/charming-fermat-itzkkh

npm install                # Capacitor 설치
npm run ios:open           # www 빌드 → 앱에 복사 → Xcode 열기
```

> 앞으로 화면을 고친 뒤 앱에 반영할 때도 **`npm run ios:open` 한 줄**이면 됩니다.

---

## 3. Xcode 설정 (최초 1회)

Xcode 왼쪽 트리에서 **App** 타깃을 누르고:

### ① Signing & Capabilities
- **Team**: Apple Developer 계정 선택 (가입 완료 후)
- **Bundle Identifier**: `app.imvoca` 인지 확인
- `+ Capability` → **Push Notifications** 추가
- `+ Capability` → **Background Modes** → ☑︎ **Remote notifications**
- `+ Capability` → **Sign In with Apple** 추가  ← 4.8 대응(아래 5번)

**여기까지가 Xcode 에서 할 일의 전부입니다.** 아래는 이미 저장소에 들어 있으니
확인만 하고 넘어가세요.

### ② 이미 설정해 둔 것 (손댈 필요 없음)
| 항목 | 값 | 왜 |
|---|---|---|
| URL Scheme | `app.imvoca` | 구글 로그인이 끝나고 앱으로 돌아오는 통로. 없으면 **로그인이 영영 안 돌아옵니다** |
| 카메라 권한 문구 | "책 페이지를 촬영해…" | 없으면 카메라를 켜는 순간 앱이 죽습니다 |
| 사진 권한 문구 | "저장된 책 사진에서…" | 앨범에서 불러오기용 |
| `ITSAppUsesNonExemptEncryption` | `NO` | 빌드를 올릴 때마다 뜨는 수출규제 질문을 건너뜀 |
| 화면 방향 | 세로 고정 | |
| 앱 아이콘 | 1024×1024, 알파 없음 | 플레이 스토어 아이콘과 동일 디자인 |
| 스플래시 | 크림 배경 + 로고 | 첫 실행 때 흰 화면 깜빡임 방지 |
| APNs 연결 | `AppDelegate.swift` | 기기 토큰을 Capacitor 로 넘기는 코드 (없으면 알림 토큰이 안 옵니다) |

---

## 4. Supabase 설정 2가지

### ① Redirect URL 추가 (안 하면 소셜 로그인 실패)
Supabase → **Authentication → URL Configuration → Redirect URLs** 에 추가:

```
app.imvoca://auth
```

### ② DB 마이그레이션
SQL Editor 에 `supabase/push-ios-apns.sql` 내용을 붙여넣고 실행.
(웹 푸시 표에 `platform` 컬럼을 추가해 iOS 기기 토큰도 같은 표에 담습니다. 여러 번 실행해도 안전)

---

## 5. Apple로 로그인 — **없으면 무조건 반려됩니다** (가이드라인 4.8)

구글 로그인을 제공하는 앱은 **"Apple로 로그인"도 같은 자리에 제공해야 합니다.**

1. https://developer.apple.com/account → **Certificates, IDs & Profiles**
2. **Identifiers** → `app.imvoca` → ☑︎ **Sign In with Apple** → Save
3. **Identifiers → `+` → Services IDs** 생성
   - Description: `IM VOCA Web`
   - Identifier: `app.imvoca.web`
   - 만든 뒤 열어서 ☑︎ Sign In with Apple → **Configure**
     - Primary App ID: `app.imvoca`
     - Domains: `ziatqkjlafucqtwshhla.supabase.co`
     - Return URLs: `https://ziatqkjlafucqtwshhla.supabase.co/auth/v1/callback`
4. **Keys → `+`** → ☑︎ Sign In with Apple → 키 생성 → **`.p8` 파일 다운로드**
   - ⚠️ **한 번만 받을 수 있습니다.** Key ID 와 Team ID 를 함께 적어두세요.
5. Supabase → **Authentication → Providers → Apple** 켜기
   - Services ID: `app.imvoca.web`
   - Team ID / Key ID / `.p8` 내용 입력
6. `index.html` 에서 플래그를 켭니다:
   ```js
   const APPLE_LOGIN_ENABLED = true;
   ```
   그리고 `git push` (웹 반영) → `npm run ios:open` (앱 반영).

> 5번까지 끝나기 전에 플래그를 켜면 버튼을 눌렀을 때 오류가 납니다. **순서를 지키세요.**

---

## 6. 알림(APNs) 서버 설정

웹 푸시(VAPID)는 iOS 앱 안에서 **동작하지 않습니다.** WKWebView 에는 ServiceWorker/PushManager 가
없어서, 애플 서버(APNs)가 직접 기기로 보내야 합니다. 보낼 대상을 고르는 규칙(시간대·시각·중복 방지·
밀린 개수)은 웹과 **완전히 같은 코드**를 씁니다 — 전송 방식만 갈립니다.

1. developer.apple.com → **Keys → `+`** → ☑︎ **Apple Push Notifications service (APNs)**
   → 키 생성 → **`.p8` 다운로드** (역시 한 번만!)
2. Supabase → **Edge Functions → Secrets** 에 4개 추가:

| 이름 | 값 |
|---|---|
| `APNS_KEY_ID` | 키 ID (예: `ABC123DEFG`) |
| `APNS_TEAM_ID` | 개발자 계정 Team ID (우측 상단 멤버십에서 확인) |
| `APNS_PRIVATE_KEY` | `.p8` 파일을 텍스트 편집기로 열어 **`-----BEGIN` 부터 `END PRIVATE KEY-----` 까지 통째로** 붙여넣기 |
| `APNS_BUNDLE_ID` | `app.imvoca` |

3. 함수 재배포:
   ```bash
   supabase functions deploy send-review-push
   ```
4. 테스트 (실기기에서 알림을 켜둔 뒤):
   ```bash
   curl -X POST "https://ziatqkjlafucqtwshhla.supabase.co/functions/v1/send-review-push" \
     -H "Authorization: Bearer <SB_SERVICE_ROLE_KEY>" \
     -H "Content-Type: application/json" -d '{"force":true}'
   ```
   응답의 `apns.configured` 가 `true` 인지, `failed` 가 비어 있는지 보세요.

> 🔐 `.p8` 두 개(로그인용·알림용)와 service_role 키는 **비밀번호 관리자**에 보관하세요.
> 채팅·깃허브·앱 코드에 절대 넣지 않습니다.
>
> 💡 Xcode 에서 케이블로 직접 설치한 빌드는 **sandbox** APNs, TestFlight·앱스토어 빌드는
> **production** APNs 를 씁니다. 코드가 한 번 실패하면 반대쪽으로 자동 재시도하므로
> 보통은 신경 쓸 필요 없습니다.

---

## 7. 실기기 테스트 체크리스트

아이폰을 케이블로 연결하고 Xcode 상단에서 기기를 고른 뒤 ▶︎ 실행. 아래를 **전부** 확인하세요.

- [ ] 비행기 모드에서도 앱이 열리고 화면이 뜬다 (오프라인 = 4.2 방어의 핵심)
- [ ] 구글 로그인 → 사파리 창이 떴다가 **앱으로 돌아와 로그인된다**
- [ ] Apple로 로그인이 보이고 동작한다
- [ ] 카메라로 책 페이지 촬영 → 단어 추출까지 된다
- [ ] 사진 앨범에서 불러오기도 된다
- [ ] **가격·`✨ Premium` 버튼·구독 관리가 어디에도 안 보인다** (3.1.1 — 보이면 즉시 반려)
- [ ] 무료 스캔 소진 팝업에 가격·외부 링크가 없다
- [ ] 암기 카드를 끝내면 알림 권한 요청 화면이 뜬다 → 켜면 위 `curl` 로 알림이 온다
- [ ] 알림을 누르면 앱이 열리고 복습 탭으로 간다
- [ ] 앱을 열면 아이콘 배지 숫자가 실제 복습 개수와 맞는다
- [ ] My → 회원 탈퇴가 동작한다 (5.1.1(v) — 앱 내 계정 삭제 필수)
- [ ] 약관·사용법을 누르면 앱 안 사파리로 열리고 **닫으면 앱으로 돌아온다**

---

## 8. App Store Connect 등록

https://appstoreconnect.apple.com → **나의 앱 → `+` → 신규 앱**

- 플랫폼: iOS / 이름: **IM VOCA** / 기본 언어: 한국어
- 번들 ID: `app.imvoca` / SKU: `imvoca-ios-001`

### 필요한 자료 (플레이 스토어 것을 대부분 재사용)

| 항목 | 내용 |
|---|---|
| 스크린샷 | **6.9"(1320×2868) 필수**, 6.5"(1242×2688) 권장. 저장소의 `screenshot1~5.png` 를 리사이즈해서 사용 |
| 홍보 텍스트 | 170자 — 플레이의 짧은 설명 재사용 |
| 설명 | 플레이의 자세한 설명 재사용 (**단, 가격·결제 안내 문구는 빼세요**) |
| 키워드 | `단어장,영어단어,원서,수능영어,토익,암기,복습,망각곡선,AI,어휘` |
| 지원 URL | `https://imvoca.app/guide.html` |
| 개인정보처리방침 URL | `https://imvoca.app/terms.html` |
| 연령 등급 | 4+ (IARC 와 별개로 애플에서 다시 설문합니다) |
| 카테고리 | 교육 / 두 번째: 참고 |

### 앱 개인정보 (App Privacy) — 반드시 정확히
수집 항목으로 아래를 선언하세요. 빠뜨리면 심사가 멈춥니다.

- **연락처 정보**: 이메일 주소, 이름 → 앱 기능용, 사용자에 연결됨
- **사용자 콘텐츠**: 사진 (책 페이지) → 앱 기능용, 사용자에 연결됨
- **사용 데이터**: 제품 상호작용 (GA4) → 분석용
- 추적(App Tracking Transparency) 용도로는 **사용하지 않음**

### 심사 메모 (App Review Information)
심사관이 막히면 바로 반려됩니다. **테스트 계정을 꼭 주세요.**

```
테스트 계정: (심사용 계정 이메일 / 비밀번호)

이 앱은 책 페이지를 촬영하면 AI가 어려운 단어를 뽑아 뜻과 예문을 정리하고,
망각곡선에 맞춰 복습을 예약해주는 단어장 앱입니다.

· 앱 내 구매는 제공하지 않습니다. 앱 안에서 가격 안내나 외부 결제 유도를 하지 않습니다.
· 무료로 스캔 10회를 사용할 수 있으며, 공식 단어장은 Day 1을 무료로 체험할 수 있습니다.
· 카메라 권한: 책 페이지 촬영. 사진 권한: 저장된 책 사진 불러오기.
· 계정 삭제는 앱 안 My → 회원 탈퇴에서 가능합니다.
· 특허출원 제10-2026-0127089호
```

### 업로드
Xcode → **Product → Archive** → Distribute App → App Store Connect → Upload
(처리에 10~30분 걸린 뒤 App Store Connect 의 빌드 목록에 나타납니다)

---

## 9. 반려 나기 쉬운 지점 4가지

| 조항 | 내용 | 우리 대응 |
|---|---|---|
| **4.2** 최소 기능 | 웹사이트를 감싼 앱 반려 | 화면을 앱에 번들(오프라인 동작) + 카메라 + 네이티브 알림 + 배지 |
| **3.1.1** 외부 결제 유도 | 앱에서 가격·결제 링크 노출 금지 | `canShowBilling()` 이 iOS 앱에서만 전부 숨김 |
| **4.8** Apple로 로그인 | 구글 로그인이 있으면 필수 | 위 5번 — **가장 자주 빠뜨리는 항목** |
| **5.1.1(v)** 계정 삭제 | 앱 안에서 탈퇴 가능해야 함 | My → 회원 탈퇴 (이미 있음) |

> ⚠️ "심사 때만 가리고 통과되면 되살리기"는 **가이드라인 2.3.1(숨겨진 기능)** 위반이라
> 개발자 계정 자체가 정지될 수 있습니다. 절대 하지 마세요.

---

## 10. 앞으로 화면을 고칠 때

```bash
# 1) 평소처럼 코드 수정 후 웹 배포 (웹·안드로이드는 즉시 반영)
git push -u origin claude/charming-fermat-itzkkh
git push origin claude/charming-fermat-itzkkh:main

# 2) iOS 앱에도 반영하려면
npm run ios:open
#   → Xcode 에서 빌드 번호(Build) 를 +1
#   → Product → Archive → Upload
#   → App Store Connect 에서 새 버전 제출 (심사 1~2일)
```

**단어장·단어·공식책·프리미엄 여부는 이 과정이 필요 없습니다.** 서버에서 바로 반영됩니다.
