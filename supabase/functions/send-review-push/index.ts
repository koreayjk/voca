// ============================================================
// IM VOCA — send-review-push
// 매시 정각 pg_cron 이 호출. 각 구독의 tz/send_hour 를 보고
// "지금 현지 시각이 그 사람이 정한 시간"인 사용자에게만 복습 알림을 보낸다.
//
// 안드로이드는 setAppBadge() 를 지원하지 않아서, 알림을 띄우는 것이
// 런처 아이콘 배지를 만드는 유일한 방법이다. (iOS/PC 는 서비스워커가
// 알림을 받을 때 setAppBadge 로 숫자까지 찍는다)
//
// 배포: supabase functions deploy send-review-push
// 웹(브라우저·안드로이드 TWA)은 VAPID 웹 푸시로, 앱스토어 iOS 앱은 APNs 로 보낸다.
// 보낼 대상을 고르는 규칙(시간대·시각·중복·밀린 개수)은 둘이 완전히 같다 — platform 으로만 갈린다.
//
// env:  SUPABASE_URL, SB_SERVICE_ROLE_KEY,
//       VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT(mailto:...)
//       APNS_KEY_ID, APNS_TEAM_ID, APNS_PRIVATE_KEY(.p8 내용), APNS_BUNDLE_ID
// 호출: POST (본문 없음). 테스트용으로 { "force": true } 를 주면 시간 조건을 무시.
// ============================================================
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import webpush from 'npm:web-push@3.6.7'
import { apnsConfigured, sendApns } from './apns.ts'

const svc = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SB_SERVICE_ROLE_KEY') ?? '',
)

const VAPID_PUBLIC  = Deno.env.get('VAPID_PUBLIC_KEY') ?? ''
const VAPID_PRIVATE = Deno.env.get('VAPID_PRIVATE_KEY') ?? ''
const VAPID_SUBJECT = Deno.env.get('VAPID_SUBJECT') ?? 'mailto:admin@imvoca.app'

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...cors, 'Content-Type': 'application/json' } })

type Sub = {
  id: string; user_id: string; endpoint: string; p256dh: string | null; auth: string | null
  platform: 'web' | 'ios'
  tz: string; send_hour: number; lang: string; fail_count: number; last_sent_on: string | null
}

// 그 시간대의 현재 '시(0~23)'와 'YYYY-MM-DD' — 앱과 같은 로컬 기준을 서버에서도 쓴다
function localParts(tz: string) {
  try {
    const p = new Intl.DateTimeFormat('en-CA', {
      timeZone: tz, hour12: false,
      year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit',
    }).formatToParts(new Date())
    const get = (t: string) => p.find((x) => x.type === t)?.value ?? ''
    return { hour: Number(get('hour')) % 24, day: `${get('year')}-${get('month')}-${get('day')}` }
  } catch {
    return null   // 잘못된 tz 문자열 → 건너뛴다
  }
}

// due 는 '단어 수'가 아니라 voca_review 행 수 = 복습 세트(책의 Day) 개수다.
// 앱 화면도 '복습 N개'로 부르므로 문구를 맞춘다.
//
// 또 하나: 이 값에는 밀린 것까지 다 들어간다. 실제 데이터에서 50~70개씩 밀린
// 사용자가 있는데, 그들에게 "오늘 복습 70개"라고 하면 질려서 알림을 꺼버린다.
// 많이 밀렸을 때는 숫자를 앞세우지 않고 '조금씩 따라잡자'로 톤을 바꾼다.
const BACKLOG = 20
const TEXT: Record<string, (n: number) => { title: string; body: string }> = {
  ko: (n) => n > BACKLOG
    ? { title: `🔁 복습이 ${n}개 쌓였어요`, body: '오늘 두세 개만 해도 따라잡기 시작해요.' }
    : { title: `🔁 오늘 복습 ${n}개`,       body: '지금 하면 오래 기억에 남아요. 5분이면 끝나요.' },
  en: (n) => n > BACKLOG
    ? { title: `🔁 ${n} reviews piled up`,   body: 'Even two or three today starts catching you up.' }
    : { title: `🔁 ${n} reviews due today`,  body: 'Review now while it still sticks — about 5 minutes.' },
  zh: (n) => n > BACKLOG
    ? { title: `🔁 积压了 ${n} 组复习`,      body: '今天做两三组就能开始追上。' }
    : { title: `🔁 今天有 ${n} 组复习`,      body: '趁还记得的时候复习，大约 5 分钟。' },
  es: (n) => n > BACKLOG
    ? { title: `🔁 Tienes ${n} repasos pendientes`, body: 'Con dos o tres hoy ya empiezas a ponerte al día.' }
    : { title: `🔁 ${n} repasos para hoy`,          body: 'Repasa ahora que aún los recuerdas — unos 5 minutos.' },
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })
  if (req.method !== 'POST') return json({ error: 'method' }, 405)
  // 둘 중 하나만 설정돼 있어도 그쪽 플랫폼으로는 보낸다 (iOS 준비 중에도 웹은 계속 나가야 한다)
  if (!VAPID_PUBLIC && !apnsConfigured()) return json({ error: 'no_push_configured' }, 500)

  // 호출자 검증 — 이 함수는 cron(서버)만 부르는 기계용이다.
  // 기본 verify_jwt 는 'anon 키로도 통과'라, 이게 없으면 누구나 {"force":true} 로
  // 전체 구독자에게 알림을 난사할 수 있다. service_role 키로만 부르게 막는다.
  const caller = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '')
  if (!caller || caller !== (Deno.env.get('SB_SERVICE_ROLE_KEY') ?? '')) {
    return json({ error: 'forbidden' }, 403)
  }

  if (VAPID_PUBLIC && VAPID_PRIVATE) webpush.setVapidDetails(VAPID_SUBJECT, VAPID_PUBLIC, VAPID_PRIVATE)

  const { force } = await req.json().catch(() => ({ force: false }))

  // 1) 사용자별 '오늘/밀린 복습' 개수
  const { data: counts, error: cErr } = await svc.rpc('due_review_counts')
  if (cErr) return json({ error: 'count_failed', detail: cErr.message }, 500)
  const dueBy = new Map<string, number>()
  for (const r of (counts ?? []) as { uid: string; due: number }[]) dueBy.set(r.uid, r.due)
  if (dueBy.size === 0) return json({ ok: true, sent: 0, note: 'no_due_reviews' })

  // 2) 복습이 있는 사용자의 활성 구독만 (fail_count 누적된 건 제외)
  const { data: subs, error: sErr } = await svc
    .from('voca_push_subs')
    .select('id,user_id,endpoint,p256dh,auth,platform,tz,send_hour,lang,fail_count,last_sent_on')
    .eq('enabled', true)
    .lt('fail_count', 5)
    .in('user_id', [...dueBy.keys()])
  if (sErr) return json({ error: 'subs_failed', detail: sErr.message }, 500)

  let sent = 0, skipped = 0, dropped = 0
  const failed: unknown[] = []

  for (const s of (subs ?? []) as Sub[]) {
    const lp = localParts(s.tz)
    if (!lp) { skipped++; continue }
    // 현지 시각이 사용자가 정한 시간이어야 하고, 오늘 이미 보냈으면 건너뛴다
    if (!force && (lp.hour !== s.send_hour || s.last_sent_on === lp.day)) { skipped++; continue }

    const due = dueBy.get(s.user_id) ?? 0
    if (due <= 0) { skipped++; continue }

    const t = (TEXT[s.lang] ?? TEXT.ko)(due)
    const payload = JSON.stringify({
      title: t.title, body: t.body, badge: due, url: '/?tab=review', tag: 'imvoca-review',
    })

    try {
      if (s.platform === 'ios') {
        // 앱스토어 iOS 앱 — endpoint 에 기기 토큰이 들어 있다
        if (!apnsConfigured()) { skipped++; continue }
        const r = await sendApns(s.endpoint, { title: t.title, body: t.body, badge: due, url: '/?tab=review' })
        if (!r.ok) {
          if (r.gone) { await svc.from('voca_push_subs').delete().eq('id', s.id); dropped++; continue }
          // webpush 와 같은 모양으로 아래 catch 에 넘긴다
          throw Object.assign(new Error(r.reason || 'apns_failed'), { statusCode: r.status, body: r.reason })
        }
      } else {
        if (!VAPID_PUBLIC || !VAPID_PRIVATE) { skipped++; continue }
        await webpush.sendNotification(
          { endpoint: s.endpoint, keys: { p256dh: s.p256dh!, auth: s.auth! } },
          payload,
          { TTL: 6 * 3600 },   // 6시간 안에 못 받으면 버린다 (다음날 또 보내므로)
        )
      }
      sent++
      await svc.from('voca_push_subs')
        .update({ last_sent_on: lp.day, fail_count: 0 }).eq('id', s.id)
    } catch (e) {
      const code = (e as { statusCode?: number })?.statusCode
      // 404/410 = 구독이 죽음(앱 삭제·권한 해제) → 바로 정리
      if (code === 404 || code === 410) {
        await svc.from('voca_push_subs').delete().eq('id', s.id)
        dropped++
      } else {
        await svc.from('voca_push_subs')
          .update({ fail_count: s.fail_count + 1 }).eq('id', s.id)
        // 상태 코드만으로는 원인을 알 수 없다(400 은 VAPID 서명 불일치·잘못된 subject·
        // 페이로드 문제 등 여러 경우에 나온다). 푸시 서버가 돌려준 본문을 그대로 올린다.
        const err = e as { statusCode?: number; body?: string; message?: string }
        failed.push({
          code: err.statusCode ?? null,
          platform: s.platform,
          host: (() => { try { return new URL(s.endpoint).host } catch { return 'apns' } })(),
          body: String(err.body ?? err.message ?? e).slice(0, 300),
        })
      }
    }
  }

  return json({
    ok: true, sent, skipped, dropped, failed,
    // 진단용 — 키 값은 노출하지 않고 '앞 8자 + 길이'만. 앱의 공개키와 대조하기 위함.
    vapid: { pub: VAPID_PUBLIC.slice(0, 8) + '…(' + VAPID_PUBLIC.length + ')', subject: VAPID_SUBJECT },
    apns: { configured: apnsConfigured(), topic: Deno.env.get('APNS_BUNDLE_ID') ?? 'app.imvoca', host: Deno.env.get('APNS_HOST') ?? 'production' },
  })
})
