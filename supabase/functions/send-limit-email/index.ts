// ============================================================
// IM VOCA — '무료 스캔 소진' 안내 메일
//
// 왜 이게 있는가:
//   앱스토어 가이드라인 3.1.1 때문에 iOS 앱 안에서는 가격도 결제 링크도 못 보여준다.
//   무료 10장을 다 쓴 사용자는 "어디서 결제하지?" 하고 그냥 이탈한다.
//   애플 규정은 **앱 안만** 규율한다 — 이메일은 자유다. 그래서 메일로 안내한다.
//
// 한 사람에게 평생 1회만. 매시간 도는 건 '막힌 뒤 한 시간 안에' 닿기 위해서다.
//
// env: SUPABASE_URL, SB_SERVICE_ROLE_KEY, RESEND_API_KEY,
//      MAIL_FROM              예: 'IM VOCA <noreply@send.imvoca.app>'
//      MAIL_POSTAL_ADDRESS    CAN-SPAM 필수. 없으면 아예 보내지 않는다.
//      PUBLIC_SITE_URL        (선택) 기본 https://imvoca.app
// 배포: supabase functions deploy send-limit-email
// ============================================================
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SB_URL = Deno.env.get('SUPABASE_URL') ?? ''
const SB_KEY = Deno.env.get('SB_SERVICE_ROLE_KEY') ?? ''
const svc = createClient(SB_URL, SB_KEY)

const RESEND = Deno.env.get('RESEND_API_KEY') ?? ''
const FROM = Deno.env.get('MAIL_FROM') ?? ''
const POSTAL = Deno.env.get('MAIL_POSTAL_ADDRESS') ?? ''
const SITE = Deno.env.get('PUBLIC_SITE_URL') ?? 'https://imvoca.app'

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...cors, 'Content-Type': 'application/json' } })

type Target = { id: string; email: string; name: string | null; lang: string; token: string }

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

// 문구는 '사실만' 적는다. 제목과 내용이 어긋나면 CAN-SPAM 위반이기도 하고,
// 무엇보다 막혀서 답답한 사람에게 광고처럼 들리면 역효과다.
const COPY: Record<string, {
  subject: string; hi: (n: string) => string; body: string; cta: string; foot: string; unsub: string
}> = {
  ko: {
    subject: '무료 스캔 10장을 모두 사용하셨어요',
    hi: (n) => `${n}님, 안녕하세요.`,
    body: `IM VOCA 무료 스캔 10장을 모두 사용하셨어요.<br><br>
지금까지 만드신 단어장과 복습 일정은 <b>그대로 남아 있습니다.</b> 계속 학습하실 수 있고,
새로 사진을 찍어 단어장을 만드는 것만 잠시 멈춘 상태예요.<br><br>
프리미엄으로 올리시면 스캔 제한 없이 이어서 쓰실 수 있습니다.`,
    cta: '프리미엄 알아보기',
    foot: '이 메일은 무료 스캔을 모두 사용하셨을 때 한 번만 보내드립니다.',
    unsub: '수신거부',
  },
  en: {
    subject: "You've used all 10 free scans",
    hi: (n) => `Hi ${n},`,
    body: `You've used all 10 free scans on IM VOCA.<br><br>
Everything you've built — your wordbooks and review schedule — <b>is still there.</b>
You can keep studying; only creating new wordbooks from photos is paused.<br><br>
Premium removes the scan limit so you can pick up where you left off.`,
    cta: 'See Premium',
    foot: 'We send this once, when you run out of free scans.',
    unsub: 'Unsubscribe',
  },
  zh: {
    subject: '您已用完 10 次免费扫描',
    hi: (n) => `${n}，您好：`,
    body: `您已用完 IM VOCA 的 10 次免费扫描。<br><br>
您已建立的单词本和复习计划<b>都还在</b>，可以继续学习，只是暂时无法拍照生成新的单词本。<br><br>
升级高级版即可取消扫描次数限制，继续使用。`,
    cta: '了解高级版',
    foot: '此邮件仅在您用完免费扫描时发送一次。',
    unsub: '退订',
  },
  es: {
    subject: 'Has usado tus 10 escaneos gratuitos',
    hi: (n) => `Hola ${n}:`,
    body: `Has usado los 10 escaneos gratuitos de IM VOCA.<br><br>
Todo lo que creaste — tus listas de vocabulario y tu plan de repaso — <b>sigue ahí.</b>
Puedes seguir estudiando; solo se pausó la creación de nuevas listas desde fotos.<br><br>
Con Premium se quita el límite de escaneos y puedes continuar donde lo dejaste.`,
    cta: 'Ver Premium',
    foot: 'Enviamos este correo una sola vez, cuando se acaban los escaneos gratuitos.',
    unsub: 'Cancelar suscripción',
  },
}

function html(t: Target): string {
  const c = COPY[t.lang] ?? COPY.ko
  const name = esc((t.name || '').trim()) || (t.lang === 'ko' ? '회원' : 'there')
  const unsubUrl = `${SB_URL}/functions/v1/email-optout?t=${t.token}&lang=${t.lang}`
  return `<!doctype html><html><body style="margin:0;padding:0;background:#f3ece0;">
<div style="max-width:520px;margin:0 auto;padding:28px 22px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;color:#1e1b16;">
  <div style="font-size:20px;font-weight:800;letter-spacing:-0.02em;color:#1c3553;margin-bottom:20px;">IM VOCA</div>
  <div style="background:#fff;border-radius:16px;padding:26px 24px;">
    <div style="font-size:15px;font-weight:700;margin-bottom:14px;">${esc(c.hi(name))}</div>
    <div style="font-size:14px;line-height:1.75;color:#3a352c;">${c.body}</div>
    <div style="margin-top:24px;">
      <a href="${SITE}/pricing.html" style="display:inline-block;background:#1c3553;color:#fff;text-decoration:none;border-radius:10px;padding:13px 26px;font-size:14px;font-weight:700;">${esc(c.cta)}</a>
    </div>
  </div>
  <div style="margin-top:22px;font-size:11.5px;line-height:1.7;color:#8a8275;">
    ${esc(c.foot)}<br>
    IM AMERICA GROUP CORP · ${esc(POSTAL)}<br>
    <a href="${unsubUrl}" style="color:#8a8275;">${esc(c.unsub)}</a>
  </div>
</div></body></html>`
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })
  if (req.method !== 'POST') return json({ error: 'method' }, 405)

  // cron(서버)만 부르는 기계용. 기본 verify_jwt 는 anon 키로도 통과하므로
  // 이게 없으면 누구나 발송을 트리거할 수 있다.
  const caller = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '')
  if (!caller || caller !== SB_KEY) return json({ error: 'forbidden' }, 403)

  // 키가 없으면 조용히 아무것도 안 한다 (설정 전에 cron 이 돌아도 에러가 쌓이지 않게)
  if (!RESEND || !FROM) return json({ ok: true, sent: 0, note: 'mail_not_configured' })

  // ⚠️ CAN-SPAM: 상업성 메일에는 실제 우편 주소가 반드시 들어가야 한다.
  //    주소 없이 보내면 위반이므로, 설정 전에는 보내지 않는다.
  if (!POSTAL) return json({ error: 'MAIL_POSTAL_ADDRESS_not_set' }, 500)

  const { data: targets, error } = await svc.rpc('limit_email_targets', { p_limit: 25 })
  if (error) return json({ error: 'targets_failed', detail: error.message }, 500)
  if (!targets?.length) return json({ ok: true, sent: 0, note: 'no_targets' })

  let sent = 0
  const failed: unknown[] = []

  for (const t of targets as Target[]) {
    const c = COPY[t.lang] ?? COPY.ko
    const unsubUrl = `${SB_URL}/functions/v1/email-optout?t=${t.token}&lang=${t.lang}`
    try {
      const res = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { Authorization: `Bearer ${RESEND}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from: FROM, to: [t.email], subject: c.subject, html: html(t),
          // 지메일·야후가 대량 발송자에게 요구하는 원클릭 수신거부.
          // 없으면 스팸함으로 갈 확률이 크게 올라간다.
          headers: {
            'List-Unsubscribe': `<${unsubUrl}>`,
            'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
          },
        }),
      })
      if (!res.ok) { failed.push({ id: t.id, code: res.status, body: (await res.text()).slice(0, 200) }); continue }
      // 보낸 뒤에만 표시한다. 실패한 사람은 다음 시간에 다시 시도된다.
      await svc.from('members').update({ limit_email_sent_at: new Date().toISOString() }).eq('id', t.id)
      sent++
    } catch (e) {
      failed.push({ id: t.id, body: String(e).slice(0, 200) })
    }
  }

  return json({ ok: true, sent, targets: targets.length, failed })
})
