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
// env:  SUPABASE_URL, SB_SERVICE_ROLE_KEY,
//       VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT(mailto:...)
// 호출: POST (본문 없음). 테스트용으로 { "force": true } 를 주면 시간 조건을 무시.
// ============================================================
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import webpush from 'npm:web-push@3.6.7'

const svc = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SB_SERVICE_ROLE_KEY') ?? '',
)

const VAPID_PUBLIC  = Deno.env.get('VAPID_PUBLIC_KEY') ?? ''
const VAPID_PRIVATE = Deno.env.get('VAPID_PRIVATE_KEY') ?? ''
const VAPID_SUBJECT = Deno.env.get('VAPID_SUBJECT') ?? 'mailto:support@imvoca.app'

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...cors, 'Content-Type': 'application/json' } })

type Sub = {
  id: string; user_id: string; endpoint: string; p256dh: string; auth: string
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

const TEXT: Record<string, (n: number) => { title: string; body: string }> = {
  ko: (n) => ({ title: `🔁 오늘 복습할 단어 ${n}개`,
                body: '지금 하면 오래 기억에 남아요. 5분이면 끝나요.' }),
  en: (n) => ({ title: `🔁 ${n} words to review today`,
                body: 'Review now while it still sticks — about 5 minutes.' }),
  zh: (n) => ({ title: `🔁 今天有 ${n} 个单词要复习`,
                body: '趁还记得的时候复习，大约 5 分钟。' }),
  es: (n) => ({ title: `🔁 ${n} palabras para repasar hoy`,
                body: 'Repasa ahora que aún las recuerdas — unos 5 minutos.' }),
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })
  if (req.method !== 'POST') return json({ error: 'method' }, 405)
  if (!VAPID_PUBLIC || !VAPID_PRIVATE) return json({ error: 'vapid_not_configured' }, 500)

  webpush.setVapidDetails(VAPID_SUBJECT, VAPID_PUBLIC, VAPID_PRIVATE)

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
    .select('id,user_id,endpoint,p256dh,auth,tz,send_hour,lang,fail_count,last_sent_on')
    .eq('enabled', true)
    .lt('fail_count', 5)
    .in('user_id', [...dueBy.keys()])
  if (sErr) return json({ error: 'subs_failed', detail: sErr.message }, 500)

  let sent = 0, skipped = 0, dropped = 0
  const failed: string[] = []

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
      await webpush.sendNotification(
        { endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } },
        payload,
        { TTL: 6 * 3600 },   // 6시간 안에 못 받으면 버린다 (다음날 또 보내므로)
      )
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
        failed.push(String(code ?? (e as Error).message))
      }
    }
  }

  return json({ ok: true, sent, skipped, dropped, failed })
})
