// ============================================================
// IM VOCA — 공지를 이메일로 보내기
//
// 앱 공지함에 올린 글을 회원 메일함으로도 보낸다. 관리자만 부를 수 있다.
//
// 안전장치:
//   · 수신거부(email_optout_at)한 회원은 SQL 단계에서 빠진다
//   · 같은 캠페인에서 이미 받은 사람은 notice_email_log 로 걸러진다 →
//     중간에 끊기거나 버튼을 두 번 눌러도 두 번 가지 않는다
//   · 한 번 호출에 최대 200명. 남으면 { remaining: true } 를 돌려주니
//     관리자 화면이 0이 될 때까지 이어서 부른다 (함수 실행 시간 제한 회피)
//   · CAN-SPAM: 우편 주소(MAIL_POSTAL_ADDRESS)가 없으면 아예 보내지 않는다
//   · 모든 메일에 1클릭 수신거부 링크와 List-Unsubscribe 헤더를 넣는다
//
// 본문 예:
//   { "campaign":"<공지 uuid 또는 새 uuid>", "subject":"...", "body":"...",
//     "audience":"all", "notice_id":"<선택>" }
//   테스트 1통:  { "test_to":"me@example.com", "subject":"...", "body":"..." }
//
// env: SUPABASE_URL, SB_SERVICE_ROLE_KEY, RESEND_API_KEY, MAIL_FROM,
//      MAIL_REPLY_TO(선택), MAIL_POSTAL_ADDRESS, PUBLIC_SITE_URL(선택),
//      ADMIN_EMAIL(선택, 기본 koreayjk@gmail.com)
// 배포: supabase functions deploy send-notice-email
// ============================================================
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SB_URL = Deno.env.get('SUPABASE_URL') ?? ''
const SB_KEY = Deno.env.get('SB_SERVICE_ROLE_KEY') ?? ''
const svc = createClient(SB_URL, SB_KEY)

const RESEND = Deno.env.get('RESEND_API_KEY') ?? ''
const FROM = Deno.env.get('MAIL_FROM') ?? ''
const POSTAL = Deno.env.get('MAIL_POSTAL_ADDRESS') ?? ''
const REPLY_TO = Deno.env.get('MAIL_REPLY_TO') ?? 'admin@imvoca.app'
const SITE = Deno.env.get('PUBLIC_SITE_URL') ?? 'https://imvoca.app'
const ADMIN_EMAIL = (Deno.env.get('ADMIN_EMAIL') ?? 'koreayjk@gmail.com').toLowerCase()

const PER_CALL = 200      // 한 번 호출에 보낼 최대 인원
const CHUNK = 100         // Resend 일괄 발송 한 묶음 (API 상한)

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...cors, 'Content-Type': 'application/json' } })

type Target = { id: string; email: string; name: string | null; lang: string; token: string }

const esc = (s: string) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

// 주소 시크릿에 회사명이 이미 들어 있으면 또 붙이지 않는다
// (전에 'IM AMERICA GROUP CORP · IM AMERICA GROUP CORP, 1608 …' 로 두 번 나왔다)
const BRAND = 'IM AMERICA GROUP CORP'
const brandLine = (postal: string) =>
  postal.toUpperCase().includes(BRAND) ? postal : `${BRAND} · ${postal}`

// 껍데기(인사·꼬리말·수신거부)만 회원 언어로 바꾼다.
// 공지 본문 자체는 관리자가 쓴 그대로 보낸다 — 기계번역해서 뜻이 틀어지는 것보다 낫다.
// (언어별로 다르게 쓰고 싶으면 '받는 사람' 에서 언어를 골라 따로 보내면 된다)
const WRAP: Record<string, { hi: (n: string) => string; open: string; cta: string; foot: string; unsub: string }> = {
  ko: { hi: (n) => `${n}님, 안녕하세요.`, open: 'IM VOCA 소식입니다.',
        cta: 'IM VOCA 열기', foot: 'IM VOCA 회원님께 보내드리는 안내 메일입니다.', unsub: '수신거부' },
  en: { hi: (n) => `Hi ${n},`, open: 'News from IM VOCA.',
        cta: 'Open IM VOCA', foot: 'You are receiving this because you have an IM VOCA account.', unsub: 'Unsubscribe' },
  zh: { hi: (n) => `${n}，您好：`, open: '来自 IM VOCA 的消息。',
        cta: '打开 IM VOCA', foot: '您收到这封邮件是因为您注册了 IM VOCA。', unsub: '退订' },
  es: { hi: (n) => `Hola ${n},`, open: 'Novedades de IM VOCA.',
        cta: 'Abrir IM VOCA', foot: 'Recibes este correo porque tienes una cuenta en IM VOCA.', unsub: 'Cancelar suscripción' },
}

function html(t: Target, subject: string, body: string, unsubUrl: string, postal: string) {
  const w = WRAP[t.lang] ?? WRAP.ko
  const name = (t.name || '').trim() || (t.lang === 'ko' ? '회원' : 'there')
  // 줄바꿈만 <br> 로 바꾼다 (HTML 태그는 그대로 이스케이프 — 관리자가 쓴 글에
  // 꺾쇠가 들어가도 레이아웃이 깨지지 않게)
  const bodyHtml = esc(body).replace(/\r?\n/g, '<br>')
  return `<!doctype html><html><body style="margin:0;padding:0;background:#f3ece0;">
<div style="max-width:560px;margin:0 auto;padding:34px 26px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;color:#2b2419;">
  <div style="font-size:20px;font-weight:800;letter-spacing:-0.02em;color:#1c3553;">IM VOCA</div>
  <div style="font-size:12px;color:#8a8275;margin-top:2px;">${esc(w.open)}</div>
  <div style="background:#fffdf8;border-radius:16px;padding:26px 24px;margin-top:18px;">
    <div style="font-size:13.5px;color:#6b6355;">${esc(w.hi(name))}</div>
    <div style="font-size:18px;font-weight:800;line-height:1.45;margin-top:10px;">${esc(subject)}</div>
    <div style="font-size:14px;line-height:1.85;margin-top:14px;">${bodyHtml}</div>
    <div style="margin-top:24px;">
      <a href="${SITE}" style="display:inline-block;background:#1c3553;color:#fff;text-decoration:none;border-radius:10px;padding:13px 26px;font-size:14px;font-weight:700;">${esc(w.cta)}</a>
    </div>
  </div>
  <div style="margin-top:22px;font-size:11.5px;line-height:1.7;color:#8a8275;">
    ${esc(w.foot)}<br>
    ${esc(brandLine(postal))}<br>
    <a href="${unsubUrl}" style="color:#8a8275;">${esc(w.unsub)}</a>
  </div>
</div></body></html>`
}

function mailFor(t: Target, subject: string, body: string) {
  const unsubUrl = `${SB_URL}/functions/v1/email-optout?t=${t.token}&lang=${t.lang}`
  return {
    from: FROM, to: [t.email], reply_to: REPLY_TO, subject,
    html: html(t, subject, body, unsubUrl, POSTAL),
    // 지메일·야후가 대량 발송자에게 요구하는 원클릭 수신거부
    headers: {
      'List-Unsubscribe': `<${unsubUrl}>`,
      'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
    },
  }
}

async function sendOne(mail: unknown) {
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${RESEND}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(mail),
  })
  return res.ok ? null : `${res.status} ${(await res.text()).slice(0, 200)}`
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })
  if (req.method !== 'POST') return json({ error: 'method' }, 405)

  // ── 관리자만 ────────────────────────────────────────────────
  // 기본 verify_jwt 는 anon 키로도 통과한다. 여기서 실제로 누구인지 확인한다.
  const bearer = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '')
  if (!bearer) return json({ error: 'forbidden' }, 403)
  if (bearer !== SB_KEY) {
    const { data, error } = await svc.auth.getUser(bearer)
    const who = (data?.user?.email || '').toLowerCase()
    if (error || who !== ADMIN_EMAIL) return json({ error: 'forbidden' }, 403)
  }

  if (!RESEND || !FROM) return json({ error: 'mail_not_configured' }, 500)

  const body = await req.json().catch(() => ({} as Record<string, unknown>))
  const subject = String(body.subject ?? '').trim()
  const text = String(body.body ?? '').trim()
  if (!subject || !text) return json({ error: 'subject_and_body_required' }, 400)

  // ── 테스트 1통 (회원 데이터·로그를 건드리지 않는다) ──────────
  const testTo = typeof body.test_to === 'string' ? body.test_to.trim() : ''
  if (testTo) {
    const lang = (typeof body.lang === 'string' && WRAP[body.lang]) ? body.lang : 'ko'
    // 진짜 토큰을 쓰면 링크를 눌러보는 순간 실제로 수신거부 처리된다 → 가짜를 넣는다
    const t: Target = { id: 'test', email: testTo, name: '테스트', lang,
                        token: '00000000-0000-0000-0000-000000000000' }
    const err = await sendOne({ ...mailFor(t, '[테스트] ' + subject, text) })
    return json({ ok: !err, test_to: testTo, postal_set: !!POSTAL, detail: err }, err ? 502 : 200)
  }

  // ⚠️ CAN-SPAM: 상업성 메일에는 실제 우편 주소가 반드시 들어가야 한다
  if (!POSTAL) return json({ error: 'MAIL_POSTAL_ADDRESS_not_set' }, 500)

  const campaign = String(body.campaign ?? '').trim()
  if (!/^[0-9a-f-]{36}$/i.test(campaign)) return json({ error: 'campaign_uuid_required' }, 400)
  const audience = String(body.audience ?? 'all')

  const { data: targets, error } = await svc.rpc('notice_email_targets', {
    p_campaign: campaign, p_audience: audience, p_limit: PER_CALL,
  })
  if (error) return json({ error: 'targets_failed', detail: error.message }, 500)
  if (!targets?.length) return json({ ok: true, sent: 0, remaining: false })

  const list = targets as Target[]
  let sent = 0
  const failed: unknown[] = []

  for (let i = 0; i < list.length; i += CHUNK) {
    const chunk = list.slice(i, i + CHUNK)
    const mails = chunk.map(t => mailFor(t, subject, text))
    let ok: Target[] = []

    // 한 묶음씩 보낸다. 200명을 한 통씩 보내면 Resend 속도 제한(초당 2건)에 걸린다.
    const res = await fetch('https://api.resend.com/emails/batch', {
      method: 'POST',
      headers: { Authorization: `Bearer ${RESEND}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(mails),
    })
    if (res.ok) {
      ok = chunk
    } else if (res.status === 429) {
      // Resend 하루/초당 한도. 한 통씩 다시 시도해도 똑같이 막히니 여기서 멈춘다.
      // 보낸 사람은 로그에 남아 있으니, 내일 다시 누르면 못 받은 사람부터 이어간다.
      failed.push({ rate_limited: (await res.text()).slice(0, 200) })
      return json({ ok: true, sent, remaining: true, rate_limited: true,
                    note: 'resend_rate_limit — 남은 회원은 한도가 풀린 뒤 다시 보내면 이어집니다', failed })
    } else {
      // 일괄 발송이 거부되면(형식 문제 등) 한 통씩 보내 최대한 건진다
      const why = `${res.status} ${(await res.text()).slice(0, 200)}`
      failed.push({ batch: why })
      for (let k = 0; k < chunk.length; k++) {
        const err = await sendOne(mails[k])
        if (err) failed.push({ id: chunk[k].id, detail: err })
        else ok.push(chunk[k])
        await new Promise(r => setTimeout(r, 550))   // 초당 2건 제한
      }
    }

    if (ok.length) {
      // 보낸 뒤에만 기록한다. 실패한 사람은 다음 회차에 다시 대상이 된다.
      await svc.from('notice_email_log')
        .upsert(ok.map(t => ({ campaign, member_id: t.id })), { onConflict: 'campaign,member_id' })
      sent += ok.length
    }
  }

  // 공지 목록에 '메일 보냄' 표시
  const noticeId = String(body.notice_id ?? '').trim()
  if (sent && /^[0-9a-f-]{36}$/i.test(noticeId)) {
    const { count } = await svc.from('notice_email_log')
      .select('member_id', { count: 'exact', head: true }).eq('campaign', campaign)
    await svc.from('voca_notices')
      .update({ email_sent_at: new Date().toISOString(), email_sent_count: count ?? sent })
      .eq('id', noticeId)
  }

  return json({ ok: true, sent, targets: list.length, remaining: list.length >= PER_CALL, failed })
})
