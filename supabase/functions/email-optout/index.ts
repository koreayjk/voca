// ============================================================
// IM VOCA — 메일 수신거부 (로그인 없이 링크 클릭 한 번)
//
// CAN-SPAM 은 상업성 메일에 '작동하는 수신거부 수단'을 요구한다. 메일에서
// 누르는 링크라 로그인 세션이 없으므로, 회원마다 가진 추측 불가능한 토큰
// (members.email_token)으로 본인을 확인한다.
//
// ⚠️ 배포할 때 반드시 --no-verify-jwt 를 붙여야 한다. 안 그러면 Supabase 가
//    Authorization 헤더를 요구해서, 메일에서 누른 링크가 401 로 막힌다:
//      supabase functions deploy email-optout --no-verify-jwt
//
// 지메일·야후의 원클릭 수신거부(List-Unsubscribe-Post)도 같은 주소로 POST 를
// 보내므로 GET/POST 를 둘 다 받는다.
//
// env: SUPABASE_URL, SB_SERVICE_ROLE_KEY
// ============================================================
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const svc = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SB_SERVICE_ROLE_KEY') ?? '',
)

const T: Record<string, { ok: string; okSub: string; bad: string; badSub: string }> = {
  ko: { ok: '수신거부 완료', okSub: '앞으로 안내 메일을 보내지 않습니다.',
        bad: '링크가 올바르지 않아요', badSub: '메일의 링크를 다시 눌러주세요.' },
  en: { ok: 'Unsubscribed', okSub: "You won't receive these emails anymore.",
        bad: 'Invalid link', badSub: 'Please use the link from the email.' },
  zh: { ok: '已退订', okSub: '今后不会再向您发送此类邮件。',
        bad: '链接无效', badSub: '请使用邮件中的链接。' },
  es: { ok: 'Suscripción cancelada', okSub: 'No volverás a recibir estos correos.',
        bad: 'Enlace no válido', badSub: 'Usa el enlace del correo.' },
}

const page = (lang: string, ok: boolean) => {
  const t = T[lang] ?? T.ko
  return `<!doctype html><html lang="${lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>IM VOCA</title></head>
<body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#f3ece0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
  <div style="background:#fff;border-radius:18px;padding:34px 30px;max-width:340px;text-align:center;box-shadow:0 8px 30px rgba(40,25,10,0.10);">
    <div style="font-size:34px;line-height:1;margin-bottom:12px;">${ok ? '✅' : '⚠️'}</div>
    <div style="font-size:17px;font-weight:700;color:#1e1b16;margin-bottom:8px;">${ok ? t.ok : t.bad}</div>
    <div style="font-size:13.5px;line-height:1.7;color:#6b6459;">${ok ? t.okSub : t.badSub}</div>
    <div style="margin-top:22px;font-size:11px;color:#a49c8e;">IM VOCA</div>
  </div>
</body></html>`
}

const htmlRes = (lang: string, ok: boolean, status = 200) =>
  new Response(page(lang, ok), { status, headers: { 'Content-Type': 'text/html; charset=utf-8' } })

Deno.serve(async (req) => {
  const url = new URL(req.url)
  const token = url.searchParams.get('t') ?? ''
  const lang = url.searchParams.get('lang') ?? 'ko'

  // uuid 형식이 아니면 조회조차 하지 않는다 (쓸데없는 질의·오류 로그 방지)
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(token)) {
    return htmlRes(lang, false, 400)
  }

  const { data, error } = await svc
    .from('members')
    .update({ email_optout_at: new Date().toISOString() })
    .eq('email_token', token)
    .select('id')

  if (error || !data?.length) return htmlRes(lang, false, 404)

  // 원클릭 수신거부(POST)는 화면을 보여줄 필요가 없다 — 200 만 돌려주면 된다.
  if (req.method === 'POST') return new Response('ok', { status: 200 })
  return htmlRes(lang, true)
})
