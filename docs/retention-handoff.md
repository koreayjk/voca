# IM VOCA 리텐션 조사 — 인수인계

작성 2026-11-01 · 기준 커밋 `c506ce8` · 조사 대상 Supabase 프로젝트 `ziatqkjlafucqtwshhla`

> 왜 가입자 325명 중 최근 7일 복습한 사람이 7~9명뿐인가. 그 조사를 하다가 중단된
> 지점과, 다음 세션이 바로 이어받을 수 있는 것들을 정리한다.

## ⚠️ 방침 (2026-11-01, 사용자 결정)

**기존 가입자는 되살리지 않는다. 앞으로 들어올 사람만 신경 쓴다.**
따라서 '복습 밀린 92명 되살리기 메일'은 **하지 않는다** (아래 4-② 는 보류).
기준선 숫자로서의 가치는 남아 있으니 지우지 않고 둔다.

작업 우선순위는 **신규 유입 경로** 하나다:
`랜딩 → 가입 → 레벨 테스트 → Day 1 암기카드 → 게이트 퀴즈 → 알림 → 복습 복귀`

---

## 1. 지금까지 확인된 숫자

쿼리 시점 2026-11-01. 모두 `mcp__Supabase__execute_sql` 로 직접 센 값이다.

### 퍼널

| 단계 | 인원 | 비율 |
|---|---|---|
| 가입 (`members`) | 325 | 100% |
| 2회 이상 방문 (`visit_count >= 2`) | 173 | 53% |
| **Day 1개 이상 암기 완료** (`voca_review` 행 존재) | **123** | **38%** |
| 복습을 1회 이상 해냄 (`last_reviewed_at` 있음) | 62 | 19% |
| 6단계 한 세트 완주 (`completed = true`) | 18 | 5.5% |
| **알림 켬** (`voca_push_subs.enabled`) | **9** | **2.8%** |
| 최근 7일 복습 | 7 | 2.2% |

최근 30일 신규 가입 48명, 최근 7일 19명.

### 복습 적체

- 복습 행 **1,260개** 중 미완료 **1,107개 (88%)**
- 첫 복습일(D+1)이 지났는데 **한 번도 안 건드린 행 561개**
- 미완료 행의 평균 경과일 **97일**

### 알림의 효과 (표본은 작지만 방향은 분명)

| | 인원 | 30일 내 복습 | 비율 |
|---|---|---|---|
| 복습일정 O + **알림 O** | 7 | 4 | **57%** |
| 복습일정 O + 알림 X | 117 | 13 | 11% |

약 5배. 알림이 이 앱의 재방문 엔진이라는 가설은 지지된다.
그래서 핵심 질문은 **"왜 켠 사람이 9명뿐인가"** 가 된다.

### 되살릴 명단

복습이 밀려 있고 + 알림을 못 켰고 + 이메일 수신거부 안 한 사람: **92명**
(1인 평균 밀린 세트 6개, 총 527세트. 36명은 최근 30일 내 접속, 42명은 60일 이상 미접속)

### 기기 구성

**알 수 없음.** `members` 에 UA/플랫폼 컬럼이 없고, `voca_errors.ua` 는 행이 너무 적어
(iOS 2명 / Android 1명) 추정이 불가능했다. 이게 2번 항목의 계측을 넣은 이유다.

---

## 2. 틀렸던 진단과, 그래서 지금 측정 중인 것

### 폐기한 가설

처음에 "알림 권유가 퀴즈 만점 뒤에 숨어 있는 것이 **가장 큰** 원인"이라고 진단했다.
**이건 틀렸다.** 만점 페이지를 한 번이라도 통과한 사용자가 105명 중 **98명**이다.
즉 대부분은 권유 화면을 볼 기회가 있었는데도 구독은 9명이었다. 게이트는 새는
구멍이긴 했지만(아래 3-A 에서 고쳤다) 주된 구멍은 아니다.

### 남은 갈림길 — DB에 흔적이 없어서 계측을 넣었다

알림 권유를 본 사람이 왜 안 켰는지, 셋 중 어느 것인지 구분이 안 됐다.

1. 기기가 웹 푸시를 **아예 지원 안 함** — 아이폰 사파리는 '홈 화면에 추가' 전까지
   `PushManager` 가 없다. 한국 사용자 비중을 생각하면 이게 가장 유력한 후보다.
2. 권유 화면을 보고 **'나중에'**
3. **'네'를 눌렀는데** 브라우저 권한 팝업에서 거부

`_pushLog()` (index.html:15194) 가 각 단계를 `voca_errors` 에 `kind='push_funnel'` 로
남긴다. `voca_errors` 를 고른 이유는 **`ua` 가 자동으로 같이 박히기 때문**이다 —
아이폰 사파리인지 안드로이드 크롬인지가 바로 보인다. `logError` 가 세션당 같은
신호를 1회만 보내므로(`_errSeen` 중복 방지) 로그가 불지 않는다.

기록되는 단계:
`unsupported` / `offered_app` / `app_store_click` / `capped` / `cooldown` /
`perm_denied` / `perm_granted` / `already_subscribed` / `ios_state_*` /
`shown` / `later` / `accepted` / `enabled` / `enable_failed` / `threw`

### 며칠 뒤 이 쿼리 하나로 답이 나온다

```sql
select message, count(*) as n, count(distinct user_id) as users
from voca_errors
where kind = 'push_funnel' and created_at > now() - interval '7 days'
group by 1 order by 2 desc;
```

기기별로 쪼개서 보려면:

```sql
select
  case when ua ilike '%iphone%' or ua ilike '%ipad%' then 'iOS'
       when ua ilike '%android%' then 'Android'
       when ua ilike '%macintosh%' then 'Mac'
       when ua ilike '%windows%' then 'Windows'
       else 'other' end as dev,
  message, count(*) as n
from voca_errors
where kind = 'push_funnel' and created_at > now() - interval '14 days'
group by 1, 2 order by 1, 3 desc;
```

**읽는 법**: `unsupported` 가 iOS에 몰려 있으면 → 원인은 기기이고, 해법은 앱 설치 유도
(이미 3-B 로 넣었다). `shown` 은 많은데 `later` 가 대부분이면 → 문구·타이밍 문제.
`accepted` 는 많은데 `enable_failed` / `perm_denied` 가 많으면 → 브라우저 권한 단계 문제.

---

## 3. 이번에 배포한 수정 2건

배포는 `main` 까지 끝났다 (GitHub Pages → imvoca.app).

### A. `61c0806` — 알림 권유를 '퀴즈 만점' 뒤에서 떼어냄

**문제**: 첫 암기는 암기카드 → 게이트 퀴즈로 이어지고, 그 퀴즈를 **만점**으로
통과해야만 `study-done` 화면에 도달했다(index.html:13238). 알림 권유는 그 화면에서만
떴다. 한 단어라도 틀리고 그만둔 사람은 복습 일정(`voca_review`)은 이미 생겼는데
"알림 켤까요?"를 한 번도 못 들었다.

**수정**:
- 복습 일정이 생기는 순간 보류 표시를 남긴다 — `_notePushAsk()` (index.html:15160),
  `saveReviewSchedule()` 의 성공 경로 3곳에서 호출
- 카드·퀴즈가 아닌 조용한 화면에 도착하면 그때 묻는다 — `_flushPushAsk()`
  (index.html:15175). 호출 지점: `library`(책장), `review`(복습 탭), `page-words`(단어목록)
- 24시간 지난 보류는 버린다 ("방금 외운 N개" 문구가 거짓이 되므로)
- `study-done` 조건에서 `!route.isReview` 를 뺐다. 복습을 해낸 사람도 알림이 없으면
  다음 복습일을 놓친다. `maybeAskPush` 가 구독중·차단·3회초과를 스스로 걸러내므로
  같은 사람을 또 묻지는 않는다.

헤드리스 6케이스 검증: 기록/소비, 1회성, 24h 만료, 깨진 JSON 무시,
flush가 실제로 `maybeAskPush` 호출, 게스트는 묻지 않고 보류 유지.

### B. `232e69a` — 계측 + 웹 푸시가 없는 기기에 앱을 권한다

**문제**: `pushSupported()` 가 false 면 전에는 **아무 일도 일어나지 않았다.**
그 사용자는 복습일을 알려줄 통로가 영구히 없는 채로 남았다.

**수정**: `_maybeOfferAppForPush()` (index.html:15243) — 아이폰이면 App Store,
안드로이드면 Play 스토어를 권한다. 평생 2번, 14일 간격. PC는 앱이 없으니 제외.
`localStorage['imvoca.appAsk']` 로 상한 관리.

헤드리스 검증 (UA 교체): iPhone Safari → App Store 버튼 + 상한/쿨다운 정상,
Android → Play 버튼, PC Mac → 시트 안 뜨고 저장도 안 함.

**⚠️ 중요**: 이 두 수정은 **앞으로 암기하는 사람에게만** 적용된다. 이미 복습 일정만
있고 알림을 못 켠 기존 92명에게는 효과가 없다 — 5번의 ② 참고.

---

## 3-C. `d727116` — 가입 직후 빈 책장 → 레벨 테스트 → Day 1 (202명 구멍)

### 파본 결과: 혼자 온 사람이 막힌다

**가입 월별 첫 Day 완주율**

| 코호트 | 가입 | 완주 | % | 1회방문 | 단체소속 |
|---|---|---|---|---|---|
| 2026-05 | 74 | 26 | 35% | 46 | 33 |
| 2026-06 | 109 | 44 | 40% | 36 | 57 |
| 2026-07 | 52 | 23 | 44% | 23 | 17 |
| 2026-08 | 21 | 15 | **71%** | 3 | 15 |
| 2026-09 | 21 | 6 | 29% | 9 | 9 |
| **2026-10** | **48** | **9** | **19%** | **35** | **8** |

**단체 소속 vs 개인** — 이게 가장 깨끗한 절단면이다

| | 가입 | 첫 Day 완주 | 1회 방문 후 이탈 |
|---|---|---|---|
| 단체소속 (10월 전) | 131 | **63%** | 23% |
| 개인 (10월 전) | 146 | **21%** | 60% |
| 단체소속 (10월~) | 8 | 25% | 50% |
| **개인 (10월~)** | **41** | **17%** | **78%** |

**3배 차이.** 8월이 71%였던 건 21명 중 15명이 단체 소속이라 선생님이 할 일을
정해줬기 때문이다. 콘텐츠 문제가 아니라 **"혼자 온 사람에게는 무엇을 할지
말해주는 사람이 없다"** 가 문제다. 10월은 스토어 출시·마케팅을 시작한 달이라
개인 유입이 늘었고, 그래서 전체 수치가 오히려 나빠졌다 — 깨진 깔때기에
트래픽을 붓고 있었다.

### 막히던 자리

가입 직후 첫 화면이 **텅 빈 책장**이었다. "책 추가를 눌러 첫 단어장을
만들어보세요 / 책 한 장이면 AI가 단어장을 만들어 드려요" — 즉 **지금 손에 교재가
있어야** 되는 일을 첫 과제로 줬다. 공짜로 풀어놓은 공식 단어장 4,800단어는
작은 회색 타일로 밀려 있었다. 첫 단어까지 모달 선택 + 6탭 이상.

그리고 **레벨 배치 테스트(16단어·1분, 이분 탐색)는 이미 만들어져 있었는데
게스트에게만 보여주고 있었다.** 정작 '어디서 시작하지'가 막막한 사람은 가입한
사람이다.

### 고친 것

- 빈 책장 + 개인 + 공식책을 볼 수 있는 사용자 → **레벨 테스트를 주인공으로**,
  '직접 고를게요'는 아래 작은 글씨로 (index.html:10603)
- `addOfficialToShelf(id, {startNow:true})` — 테스트가 끝나면 책장으로
  돌려보내지 않고 **첫 Day 암기카드로 바로** 넣는다. Day 는 번호로 정렬해서
  고른다(카탈로그의 페이지 배열은 순서를 보장하지 않는다)
- 게스트·단체 관리자·공식책 미노출 사용자는 기존 화면 그대로. 두 조건은
  **서로의 여집합**이라 빈 책장 안내가 사라지는 경우는 없다 (10603 / 10617)

헤드리스 4케이스 검증: 개인 한국어→히어로 / 게스트→기존+게스트 버튼 /
단체관리자→기존(배정 안내) / 비한국어→기존(중국어로 정상 표시).

### 측정 방법

11월 이후 가입 코호트의 완주율을 같은 쿼리로 다시 본다. 비교 기준선:
**개인 17~21%**. 레벨 테스트가 먹히면 단체(63%)에 가까워져야 한다.

```sql
select to_char(created_at,'YYYY-MM') as cohort,
       case when org_id is not null then 'org' else 'solo' end as who,
       count(*) as signups,
       count(*) filter (where exists (select 1 from voca_review r where r.user_id=m.id)) as studied,
       round(100.0*count(*) filter (where exists (select 1 from voca_review r where r.user_id=m.id))/count(*),0) as pct
from members m where created_at >= '2026-09-01' group by 1,2 order by 1,2;
```

### 세션 크기·게이트 퀴즈를 세본 결과 (2026-11-01)

**Day 당 단어 수 — '40단어라서 힘든 것' 가설은 기각.**

| 책 | Day 수 | Day당 단어 |
|---|---|---|
| **Lv.1 ~ Lv.12** | 20 | **20** |
| 수능·중등·토익·토플·스페인어 | 10~50 | 37~40 |

Lv 책은 20단어다. 40단어인 건 구버전 책들이고, 그중 수능·중등 6권은
`RETIRED_OFFICIAL` 로 이미 내렸다.

**세션 크기별 만점 통과율** (`voca_stats`, page 단위)

| 세션 크기 | 시도 | 만점률 | 평균 정답률 |
|---|---|---|---|
| 1~10단어 | 2,540 | 68% | 85% |
| 11~20 | 387 | 26% | 78% |
| 21~30 | 223 | 43% | 88% |
| 31~40 | 1,656 | 33% | 92% |
| 41+ | 47 | 17% | 86% |

평균 정답률은 어디서나 78~92%인데 **만점률만** 크기에 따라 무너진다. 이건
이항분포 그대로다 — 단어당 95%를 맞혀도 20단어 만점은 0.95²⁰ ≈ 36%,
40단어는 ≈ 13%. 즉 "만점이어야 통과"는 세션이 커질수록 수학적으로 불가능해진다.

**다만 막다른 길은 아니다.** `startWrongQuiz` (index.html:13209) 가 `_review`
플래그를 유지하므로 **틀린 것만 다시 맞혀도 게이트가 닫힌다.** 점수도 나온다.
여기는 버그가 아니다.

**게이트 퀴즈에서 실제로 빠지는 양**

```
암기카드 완료(voca_review 생성)        1,260
  그중 퀴즈까지 끝낸 것                  920
  카드만 끝내고 퀴즈 미완료              340  (27%, 55명)
```

카드를 끝낸 4건 중 1건은 퀴즈를 안 끝낸다. 이 340건은 복습 일정은 생겼으니
에빙하우스는 돌지만 점수를 못 받았고, **구 코드에서는 알림 권유도 못 들었다.**
`61c0806` 이 바로 이 구간을 메운다.

### ⚠️ 가장 날카로운 발견: Lv.1~12 가 거의 안 쓰인다

| | 만든 날 | 책장에 담긴 수 | 실제 공부한 Day | 공부한 사람 |
|---|---|---|---|---|
| Lv.1~12 (12권·4,800단어) | 2026-10-14 | **75** | **16** | **약 7명** |
| 수능 기본 | 2026-06-24 | 8 | 278 | 34명 |
| 수능 핵심 | 2026-06-24 | 4 | 169 | 20명 |

실제 학습량은 거의 전부 **이미 내린(retired) 수능·중등 책**에서 나온다 —
학원 학생들이 은퇴 전에 배정받아 쓰던 것들이다. 마케팅에서 앞세우는
**Lv.1~12 신규 4,800단어는 사실상 미채택 상태**다(만든 지 18일).

더 중요한 건 **75 → 16** 이다. 책장에 담는 것과 공부를 시작하는 것은 다른
행동이고, 사람들은 담고 나서 멈춘다. (앞서 본 '첫 Day 미완주 203명 중 47명이
공식책을 담았다'와 같은 현상이다.) `d727116` 이 책장 단계를 건너뛰고 Day 1
암기카드로 직접 넣는 이유가 이것이다.

### 아직 안 본 것

- ~~레벨 테스트 완료율 계측~~ → `62566b1` 로 넣었다. 아래 3-D 참고.
- 암기카드가 **모든 단어를 '알아요'로 처리할 때까지 라운드를 반복**한다
  (index.html:11300 부근). 중간 이탈 시 아무 기록이 안 남아 측정 불가.
  20단어면 그라인드가 심하지 않을 테니 우선순위는 낮춰도 된다.
- 게이트 퀴즈를 '만점' 대신 '80% 이상'으로 완화하는 안. 위 340건(27%)을
  줄일 수 있지만, 점수 파밍과 학습 품질 쪽 trade-off가 있어 판단이 필요하다.

---

## 3-D. `62566b1` — 레벨 테스트 퍼널 계측

`d727116` 의 효과를 판정할 수단이 없었다. 테스트를 아예 안 누르는 건지, 누르고
중간에 닫는 건지, 추천 레벨까지 보고 '직접 고를게요'로 빠지는 건지 구분이
안 됐다. 알림 퍼널과 같은 방식으로 `voca_errors(kind='lt_funnel')` 에 남긴다.
`context` 에 출처가 들어가서 자리별로 비교된다.

```
started ──┬─ catalog_not_ready        (버튼은 눌렀는데 카탈로그가 안 떠서 못 함)
          ├─ abandoned_mid            (문제 풀다 닫음, detail.asked = 몇 번째)
          └─ finished (detail.lv)  ─┬─ declined_result   ('직접 고를게요')
                                    └─ add_click ─ started_day1 (detail.day)
```

출처(`context`): `empty_shelf` (빈 책장 히어로 — d727116) / `guest` (게스트 배너) /
`picker` (공식책 고르기 모달)

### 읽는 쿼리

```sql
select context as source, message as stage,
       count(*) as n, count(distinct user_id) as users
from voca_errors
where kind = 'lt_funnel' and created_at > now() - interval '14 days'
group by 1, 2 order by 1, 3 desc;
```

중간 이탈이 몇 번째 단어에서 일어나는지:

```sql
select (detail->>'asked')::int as answered_before_quitting, count(*)
from voca_errors
where kind = 'lt_funnel' and message = 'abandoned_mid'
group by 1 order by 1;
```

### 읽는 법

- `started` 자체가 거의 없다 → 빈 책장 히어로를 안 누른다. 문구·배치 문제.
- `started` 는 있는데 `abandoned_mid` 가 대부분 → 16문제가 길다. `LT_PER_ROUND`
  (index.html, 현재 4)를 줄이거나 진행률 표시를 강화한다.
- `finished` 는 많은데 `declined_result` 가 많다 → 추천 레벨을 못 믿는다.
  근거를 더 보여줘야 한다.
- `started_day1` 까지 잘 오는데 그래도 복습이 안 생긴다 → 암기카드 안에서
  빠지는 것이다. 그때는 카드 내부 계측이 다음 차례다.
- `catalog_not_ready` 가 보이면 그건 버그다 — 버튼을 눌렀는데 안 되는 상태를
  사용자가 본 것이다. `appendOfficialBooks` 가 끝나기 전에 히어로가 그려진
  경우이므로, 로딩 중에는 버튼을 비활성화하거나 자동 재시도를 넣어야 한다.

같이 고친 것: 결과 화면 버튼 문구가 아직 'Lv.N 책장에 담기'였다. `d727116`
이후로는 담고 끝나지 않고 Day 1 로 바로 들어가므로 동작과 어긋났다
→ 'Lv.N Day 1 바로 시작'.

헤드리스 5케이스 검증: 즉시닫기 / 2문제후닫기(asked:2) / 완주후거절 /
완주후 Day 1 진입(day:"1") / 카탈로그 미준비.

---

## 3-E. `c506ce8` — 신규 사용자 첫 방문의 경합 제거

3-D 의 '읽는 법'에서 `catalog_not_ready` 가 보이면 버그라고 적어놨는데,
그 버그가 실재하는 것을 코드로 확인하고 먼저 막았다.

공식 카탈로그(~6천 단어)는 첫 화면을 막지 않으려고 **렌더 뒤에 비동기로**
붙는다 (index.html:7777, `window._officialPending`). 그런데 빈 책장 히어로는
그보다 먼저 그려진다. 즉 **가입 직후 바로 누르면 카탈로그가 아직 없고**,
전에는 "잠시 뒤 다시 눌러주세요" 토스트로 끝났다.

신규 사용자에게 주는 단 하나의 행동 유도가 '안 되는 버튼'이 되는 것이고,
하필 그 사람들은 되돌아오지 않는다 (10월 개인 가입자 78%가 한 번 보고 안 옴).

**고친 방식**: 되라고 말하지 말고 기다린다. `openLevelTest` 가 레벨이 3개
미만이면 로딩 화면을 띄우고 `ensureOfficialCatalog()` 를 await 한 뒤 그대로
이어서 테스트를 시작한다. 기다려도 못 받으면(네트워크·RLS) 로딩 화면을 켜둔
채 두지 않고 닫고, 문구를 "불러오지 못했어요"로 바꿔 알리고
`catalog_not_ready` 로 기록한다.

헤드리스 3케이스: 늦게 도착(400ms) → 로딩 뒤 자동 진행 / 실패 → 오버레이 닫고
토스트+기록 / 기다리는 중 사용자가 닫음 → 조용히 끝(잔여 로그·토스트 없음).

---

## 4. 다음 할 일 (우선순위)

### ① ~~가입 → 첫 Day 완주 사이의 구멍~~ → 3-C 로 착수함, 측정 대기

남은 단서 (아직 안 쓴 것):

```sql
select
  count(*) as never_finished_a_day,
  count(*) filter (where exists (select 1 from voca_stats s where s.user_id=m.id))  as but_has_stats,
  count(*) filter (where exists (select 1 from voca_books b where b.user_id=m.id))  as but_has_own_book,
  count(*) filter (where visit_count >= 2)  as but_visited_2plus,
  count(*) filter (where visit_count = 1)   as visited_once
from members m
where not exists (select 1 from voca_review r where r.user_id = m.id);
```

→ 203명 중 **47명은 공식 단어장을 책장에 담았고**, 23명은 스캔까지 했고,
22명은 퀴즈 기록이 있는데 완주를 못 했다. 59명은 2회 이상 방문했다. 즉
"관심 없어서 떠난 사람"이 아니라 **중간에 막힌 사람**이 상당수다. 책을 담은
47명이 그래도 Day 를 못 끝낸 건 암기카드/퀴즈 쪽에 또 벽이 있다는 뜻이다
(3-C 의 '아직 안 본 것' 참고).

**주의**: `native_lang` 은 204명이 NULL 이다(컬럼을 나중에 추가하고 백필을
안 했다). `native_lang is distinct from 'ko'` 로 세면 NULL 이 섞여 "비한국인
155명" 같은 허수가 나온다. 모국어별로 볼 때는 NULL 을 따로 분리할 것.

### ② ~~92명 되살리기 메일~~ — 보류 (방침: 기존 가입자 무시)

아래 쿼리와 계획은 방침이 바뀔 때를 위해 남겨둔다. 지금은 실행하지 않는다.

명단 뽑는 쿼리:

```sql
with od as (
  select user_id, count(*) as overdue
  from voca_review
  where completed = false and review_2d < now()
  group by user_id
)
select m.email, m.name, od.overdue, m.last_seen_at::date
from od join members m on m.id = od.user_id
where m.email is not null
  and m.email_optout_at is null
  and not exists (select 1 from voca_push_subs s where s.user_id = m.id and s.enabled)
order by od.overdue desc;
```

메일 내용은 "밀린 복습 N개가 있어요" + **알림 켜는 법**(아이폰은 앱 설치 또는
홈 화면에 추가가 필요하다는 설명)이 핵심. 발송은 `send-notice-email` 엣지 함수.
절차는 `docs/notice-email-setup.md` 참고.

### ③ 계측 결과 확인 (2번의 쿼리) — 며칠 뒤

---

## 5. 코드 지도 (index.html, 단일 파일 ~977KB)

### 복습 일정이 생기는 흐름

```
책장 → 책 → Day → 단어목록 → [📚 암기카드]      (index.html:10905 부근)
  → initStudy(bookId, 'page', pageNum)
  → 모든 단어 '알아요' 처리까지 라운드 반복
  → _registerFirstStudy()  →  saveReviewSchedule()   [voca_review 행 생성]
      └ 여기서 _notePushAsk() 로 알림 권유 보류 표시
  → startReviewQuiz()  (같은 단어 다시)
  → 만점?  ─ 예 → study-done
            └ 아니오 → 퀴즈 결과 화면에서 멈춤 (study-done 도달 안 함)
```

### 주요 함수 위치

| 함수 | 줄 | 역할 |
|---|---|---|
| `logError` | 917 | `voca_errors` 기록. `ua`·`app_version` 자동 포함, 세션당 중복 방지 |
| `saveReviewSchedule` | 13040 | `voca_review` 행 생성. 간격은 첫 학습 +1/+2/+3/+6/+15/+30일 |
| `_registerFirstStudy` | 13107 | 위 + `voca_activity` 기록 |
| `startReviewQuiz` | 13190 | 게이트 퀴즈 |
| `pushSupported` | 14933 | 여기서 iOS 사파리가 걸러진다 |
| `_notePushAsk` | 15160 | 알림 권유 보류 표시 |
| `_takePushPend` | 15163 | 읽고 지운다 (1회성, 24h 만료) |
| `_flushPushAsk` | 15175 | 조용한 화면에서 보류 소비 |
| `_pushLog` | 15194 | 퍼널 계측 |
| `maybeAskPush` | 15208 | 권유 조건 판정 |
| `_maybeOfferAppForPush` | 15243 | 푸시 미지원 기기에 스토어 권유 |
| `_showPushPrePrompt` | 15293 | 권유 바텀시트 |

### 알아둘 것

- **`study-setup` 화면(index.html:10917)은 사실상 죽은 코드다.** `scope: 'all'` 이
  기본값이고 `scope === 'all'` 로 공부하면 **복습 일정이 안 생긴다.** 다행히
  `goTab('study')` 를 호출하는 곳이 한 군데도 없어서 현재는 도달 불가.
  나중에 하단 탭에 되살린다면 이 함정을 먼저 고쳐야 한다.
- `voca_review` 컬럼명 `review_2d`~`review_60d` 는 **레거시라 실제 간격과 안 맞는다.**
  값이 정답이고 컬럼명은 라벨일 뿐이다 (실제: +1/+2/+3/+6/+15/+30일, 6회).
- `voca_review` 에 `updated_at` 은 **없다.** 최근 복습 시각은 `last_reviewed_at`.
- 알림 발송은 `supabase/functions/send-review-push`. 매시 정각 pg_cron 이 호출하고,
  구독마다 `tz`/`send_hour` 를 보고 그 사람의 현지 시각에만 보낸다. 웹은 VAPID,
  iOS 앱은 APNs. 20세트 이상 밀리면 숫자를 앞세우지 않고 톤을 바꾼다.

---

## 6. 작업 절차 (반드시 지킬 것)

### 배포

```bash
cd /home/user/voca
git push -u origin <작업브랜치>
git push origin <작업브랜치>:main        # GitHub Pages → imvoca.app
```

### index.html 을 고친 **모든** 경우, 문법 게이트를 통과시킬 것

```bash
cd /home/user/voca && node -e '
const fs=require("fs");const h=fs.readFileSync("index.html","utf8");
const re=/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g;let m,n=0;
while((m=re.exec(h))){n++;try{new Function(m[1]);}catch(e){console.log("BLOCK "+n+" FAIL: "+e.message);process.exit(1);}}
console.log("ok "+n+" script blocks");'
```

단일 파일 1MB짜리를 문법 깨진 채로 배포하면 앱 전체가 백지가 된다. 예외 없이 돌린다.

### 헤드리스 검증

```bash
cd /home/user/voca
(fuser -k 8899/tcp 2>/dev/null; true)
(python3 -m http.server 8899 >/dev/null 2>&1 &)
# playwright-core + /opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
# URL 은 반드시 index.html?probe=1  ← 쿼리스트링이 없으면 랜딩으로 리다이렉트된다
```

- **`pkill -f` 를 쓰지 말 것.** 자기 셸을 죽인다. 포트 정리는 `fuser -k 8899/tcp`.
- `let`/`const` 전역은 `page.evaluate` 안에서 `eval('currentUser = {...}')` 로 접근.
  `function` 선언은 `window` 에 있다.
- UA별 분기를 테스트할 때는 `browser.newContext({ userAgent })`.

### 승인 프롬프트 줄이기

클라우드 세션에는 "항상 허용" 버튼이 없다. 레포의 `.claude/settings.json` 에
`permissions.allow` 를 넣고 커밋해야 **다음 세션부터** 적용된다. 세션이 자기 권한
설정을 고치는 건 차단돼 있으니 사용자가 직접 커밋해야 한다. 넣을 항목:

```json
"permissions": {
  "allow": [
    "mcp__Supabase__execute_sql",
    "mcp__Supabase__list_tables",
    "mcp__Supabase__get_advisors",
    "mcp__Supabase__query_logs"
  ]
}
```

기존 `enabledPlugins` 를 날리지 말고 **합쳐서** 쓸 것.
(`--dangerously-skip-permissions` 류 플래그는 클라우드 세션에서 효과 없다.)

---

## 7. 보안 — 넘겨도 되는 선

- **키를 대화창에 붙여넣지 않는다.** 터미널에만 넣는다.
- 레거시 Supabase anon/service_role JWT 는 2026-10-24 키 유출 후 **비활성화했다.
  다시 켜지 않는다.** 새 키는 `sb_secret_…` 형식이고, JWT가 아니므로
  `Authorization: Bearer` 가 아니라 **`apikey` 헤더**로 보내야 한다.
- publishable key(`sb_publishable_…`)는 클라이언트용. 이걸로는 `members`,
  `voca_review`, `voca_push_subs` 가 RLS에 막혀 **0행**만 나온다. 조사에는
  Supabase 커넥터(MCP)가 필요하다.
- `CRON_SECRET` 은 과거 대화창에 붙여넣어진 적이 있고 **아직 교체 안 했다.** 교체 권장.
- service-role / Google API 키를 레포에 커밋하지 않는다.
- `academy_leads` 에 SELECT 정책이 **없는 건 의도된 것이다.** 영업 명단이라
  사용자끼리 서로 못 봐야 한다.
- `scripts/seed_official.py` 에 `--reset` / `--replace` 를 절대 넘기지 않는다.
- SSN·EIN 을 대화창에 쓰지 않는다.

---

## 8. 조사와 무관하게 남아 있는 미결 항목

- App Store Connect + Play Console 에 5개 언어 메타데이터 입력 (전부 입력 가능 상태)
- 언어별 스크린샷
- Search Console 에 `sitemap.xml` 제출, `lp-en.html` 색인 요청
- ~~중국어/일본어 랜딩 페이지~~ → `7140ba4` 완료 (lp-zh.html / lp-ja.html).
  루트 라우팅 ko→lp / zh→lp-zh / ja→lp-ja / 그 외→lp-en. **스페인어 랜딩은 아직
  없다** — 뜻은 번역해 놨는데(4,800행) 입구가 없으므로 다음 후보다.
- Play Console 설명·스크린샷이 아직 구버전
- `CRON_SECRET` 교체
- 학원 리드 수집 경과 확인 (기준선: `academy_name` 2건 / `academy_leads` 0건,
  2026-11-01 기준. `993c305` 로 질문 위치를 학습 완료 직후로 옮긴 뒤 1주일 관찰)
- 기출 예문 주장을 lp/pricing/스토어 설명에 넣는 건 **보류 중** — 정확한 연도 범위,
  시험 범위, 레벨 커버리지 3가지가 미확인이라 문구를 못 썼다.
- 보류: Supabase 이메일 확인, fr/de/pt/vi/id UI 언어, D&B 케이스 34922413,
  사업장 주소를 집 주소에서 분리
