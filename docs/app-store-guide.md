# IM VOCA 앱스토어 등록 가이드 (2026-09)

## 현재 준비 상태

| 항목 | 상태 |
|---|---|
| PWA manifest (아이콘·maskable·스크린샷) | ✅ 완비 |
| 서비스워커 (오프라인·즉시 시작) | ✅ v5 |
| `.well-known/assetlinks.json` (패키지 `app.imvoca.twa`) | ✅ 있음 — Play 서명키 지문과 일치 여부만 확인 |
| 개인정보처리방침 | ✅ https://imvoca.app/terms.html |
| 회원 탈퇴(계정 삭제) — 애플 필수 | ✅ 앱 내 My → 회원 탈퇴 (delete-account 함수 배포 필요) |
| 심사용 데모 계정 | ✅ 데모 링크 기능 활용 |

## 사전 작업 (1회)

Supabase CLI 또는 대시보드에서 탈퇴 함수 배포:
```bash
supabase functions deploy delete-account
```
(env 는 기존 함수와 동일: SUPABASE_URL, SB_SERVICE_ROLE_KEY, STRIPE_SECRET_KEY)

## 1단계 — Google Play (TWA)

1. **개발자 계정**: https://play.google.com/console 가입 ($25, 1회)
2. **패키지 생성**: https://www.pwabuilder.com 에 `https://imvoca.app` 입력
   → Android 패키지 다운로드 (Package ID: `app.imvoca.twa` — assetlinks 와 동일하게!)
3. **Play Console** → 앱 만들기 → 프로덕션 → PWABuilder가 준 `.aab` 업로드
4. **서명키 지문 확인**: Play Console → 설정 → 앱 무결성 → "앱 서명 키 인증서"의
   SHA-256 지문이 `.well-known/assetlinks.json` 의 값과 다르면 그 값으로 교체 후 배포
   (다르면 앱 상단에 브라우저 주소창이 떠 버림)
5. **스토어 등록정보** 입력 (아래 문구 사용) + 스크린샷(폰 스샷 2장 이상, manifest 의
   screenshot1.png 재활용 가능) + 개인정보처리방침 URL
6. **데이터 보안 설문**: 수집 항목 = 이메일·이름(계정), 앱 활동(학습 기록) /
   암호화 전송 ✓ / 삭제 요청 가능 ✓ (앱 내 회원 탈퇴)
7. 심사 제출 → 보통 1~3일

### 스토어 문구 (한국어)
- **앱 이름**: IM VOCA — AI 원서 단어장
- **간단한 설명** (80자): 책을 찍으면 AI가 단어장을 만들어줘요. 문맥 뜻·발음·예문에 에빙하우스 복습까지.
- **자세한 설명**:
```
📷 책 한 페이지를 찍으면 끝.
AI가 어려운 단어만 골라 뜻·발음·예문과 함께 단어장을 만들어 드립니다.

• 문맥 뜻 — 사전 뜻이 아니라 "이 책에서의" 의미
• CEFR 난이도 자동 분류 (A2~C2)
• 암기 카드 + 퀴즈로 빠르게 암기
• 에빙하우스 망각곡선 복습 (1·2·3·6·15·30·60일 자동 알림)
• 명예의 전당 — 친구와 점수 경쟁
• 수능·토익·토플·스페인어 공식 단어장 제공
• 학원용: 단어장 배정·학습 리포트·시험 출제

특허출원 기술 (제10-2026-0127089호)
무료로 시작하세요 — 스캔 10장 무료 제공.
```
(영어/중국어/스페인어 버전은 같은 구조로 번역해 등록정보 번역에 추가)

## 2단계 — Apple App Store (추후)

1. Apple Developer Program 가입 ($99/년) + Mac 필요
2. **Capacitor** 로 래핑 + **복습 푸시 알림** 추가 (심사지침 4.2 대응 — 웹뷰만으로는 반려 위험)
3. **결제**: iOS 빌드에서는 Premium 구매 버튼 숨김 (리더 앱 모델) —
   웹에서 결제한 구독은 로그인만 하면 앱에 자동 반영됨
4. 심사 노트에 데모 계정 + "계정 삭제는 My → 회원 탈퇴" 명시

## 업데이트는?

TWA/Capacitor 는 imvoca.app 을 그대로 보여주므로 **지금처럼 배포하면 앱에도 즉시 반영**.
스토어 재심사는 아이콘/이름/네이티브 기능을 바꿀 때만 필요.
