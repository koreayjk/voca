// ============================================================
// IM VOCA — 단어 발음 음성 만들기 (Google Cloud TTS → Supabase Storage)
//
// 왜 필요한가:
//   아이폰은 웹에서 쓸 수 있는 음성이 시스템 기본 몇 개로 막혀 있다(애플 제한).
//   설정에서 고품질 음성을 받아도 웹에는 적용되지 않는다. 기기에 기대는 한
//   아이폰 사용자에게 좋은 발음을 들려줄 방법이 없다.
//   → 서버에서 한 번 만들어 저장해 두고 모두가 그 파일을 쓴다.
//
// 비용이 안 늘어나는 이유:
//   음성은 '단어당 한 번'만 만들고 영구 저장된다. 1만 명이 1만 번 들어도
//   생성 비용은 그대로 0이다. 게다가 ⭐우리 사전(voca_words)에 있는 단어만⭐
//   만들기 때문에, 평생 만들 수 있는 최대치가 사전 크기(약 1만 5천 단어)로
//   묶여 있다 — OCR 이 잘못 읽은 쓰레기 단어도, 누가 악용해도 그 위를 못 넘는다.
//
// 본문:
//   { "word": "apple" }                      → 한 단어 (로그인 사용자)
//   { "bulk": true, "limit": 200 }           → 사전 단어를 미리 채우기 (관리자만)
//
// env: SUPABASE_URL, SB_SERVICE_ROLE_KEY, GOOGLE_TTS_KEY,
//      TTS_VOICE(선택, 기본 en-US-Neural2-C), ADMIN_EMAIL(선택)
// 배포: supabase functions deploy tts
// ============================================================
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SB_URL = Deno.env.get('SUPABASE_URL') ?? ''
const SB_KEY = Deno.env.get('SB_SERVICE_ROLE_KEY') ?? ''
const svc = createClient(SB_URL, SB_KEY)

const GKEY = Deno.env.get('GOOGLE_TTS_KEY') ?? ''
// Neural2 = $16/100만 자, 매달 100만 자 무료. 학습용으로 또렷한 여성 미국 발음.
const VOICE = Deno.env.get('TTS_VOICE') ?? 'en-US-Neural2-C'
const ADMIN_EMAIL = (Deno.env.get('ADMIN_EMAIL') ?? 'koreayjk@gmail.com').toLowerCase()

const BUCKET = 'audio'
const PUBLIC = `${SB_URL}/storage/v1/object/public/${BUCKET}`

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...cors, 'Content-Type': 'application/json' } })

// 앱의 _safeAudio() 와 글자 하나까지 같아야 한다 — 다르면 앱이 찾는 파일명과 어긋난다
const safeName = (en: string) =>
  en.toLowerCase().replace(/[^a-z0-9 ]/g, '').trim().replace(/\s+/g, '-')

async function alreadyThere(path: string) {
  try {
    const r = await fetch(`${PUBLIC}/${path}`, { method: 'HEAD' })
    return r.ok
  } catch { return false }
}

async function makeAudio(word: string, path: string) {
  const r = await fetch(`https://texttospeech.googleapis.com/v1/text:synthesize?key=${GKEY}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      input: { text: word },
      voice: { languageCode: VOICE.slice(0, 5), name: VOICE },
      // 학습자가 따라 하기 좋게 아주 살짝 느리게. 0.85 아래로 내리면 어색해진다.
      audioConfig: { audioEncoding: 'MP3', speakingRate: 0.92, pitch: 0 },
    }),
  })
  if (!r.ok) return { ok: false, detail: `${r.status} ${(await r.text()).slice(0, 200)}` }
  const { audioContent } = await r.json()
  if (!audioContent) return { ok: false, detail: 'no_audio' }
  const bytes = Uint8Array.from(atob(audioContent), (c) => c.charCodeAt(0))
  const up = await svc.storage.from(BUCKET).upload(path, bytes, {
    contentType: 'audio/mpeg',
    upsert: true,
    // 한 번 만들면 바뀌지 않는 파일이라 길게 캐시한다 → 전송량(egress)을 아낀다
    cacheControl: '31536000',
  })
  if (up.error) return { ok: false, detail: 'upload: ' + up.error.message }
  return { ok: true }
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })
  if (req.method !== 'POST') return json({ error: 'method' }, 405)
  if (!GKEY) return json({ error: 'tts_not_configured' }, 500)

  const bearer = (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '')
  if (!bearer) return json({ error: 'forbidden' }, 403)

  let who = ''
  if (bearer !== SB_KEY) {
    const { data, error } = await svc.auth.getUser(bearer)
    if (error || !data?.user) return json({ error: 'forbidden' }, 403)   // 로그인한 사용자만
    who = (data.user.email || '').toLowerCase()
  }

  const body = await req.json().catch(() => ({} as Record<string, unknown>))

  // ── 사전 단어 미리 채우기 (관리자 전용) ────────────────────────
  // 한 번에 다 하면 함수 시간 제한에 걸린다. limit 만큼 하고 남은 수를 알려준다.
  if (body.bulk === true) {
    if (bearer !== SB_KEY && who !== ADMIN_EMAIL) return json({ error: 'forbidden' }, 403)
    const limit = Math.min(Math.max(Number(body.limit) || 100, 1), 300)
    const offset = Math.max(Number(body.offset) || 0, 0)
    const { data: rows, error } = await svc
      .from('voca_words').select('en').not('en', 'is', null)
      .order('en').range(offset, offset + limit - 1)
    if (error) return json({ error: 'query_failed', detail: error.message }, 500)

    let made = 0, skipped = 0
    const failed: unknown[] = []
    const seen = new Set<string>()
    for (const row of rows ?? []) {
      const w = String(row.en || '').trim().toLowerCase()
      const key = safeName(w)
      if (!key || seen.has(key)) { skipped++; continue }
      seen.add(key)
      const path = `w/${key}.mp3`
      if (await alreadyThere(path)) { skipped++; continue }
      const res = await makeAudio(w, path)
      if (res.ok) made++; else failed.push({ word: w, detail: res.detail })
    }
    return json({ ok: true, made, skipped, scanned: rows?.length ?? 0,
                  next_offset: offset + (rows?.length ?? 0),
                  done: (rows?.length ?? 0) < limit, failed })
  }

  // ── 단어 하나 ────────────────────────────────────────────────
  const word = String(body.word ?? '').trim().toLowerCase()
  // 영문 단어(또는 짧은 구)만. 이걸로 OCR 이 뱉은 이상한 문자열을 먼저 거른다.
  if (!/^[a-z][a-z' -]{0,30}$/.test(word)) return json({ ok: false, reason: 'bad_word' })
  const key = safeName(word)
  if (!key) return json({ ok: false, reason: 'bad_word' })
  const path = `w/${key}.mp3`
  const url = `${PUBLIC}/${path}`

  if (await alreadyThere(path)) return json({ ok: true, cached: true, url })

  // ⭐ 누군가의 단어장에 실제로 저장된 단어만 만든다.
  //    (voca_words 에는 공식 단어장 + 모든 사용자가 저장한 단어가 들어 있다)
  //    사람이 스캔해서 '저장' 까지 한 단어만 통과하므로, 엔드포인트를 두드려
  //    아무 문자열이나 음성으로 만들어 저장소를 불리는 일을 막는다.
  //    관리자·서버(service_role)는 이 검사를 건너뛴다 — 테스트와 일괄 생성용.
  const isAdmin = (bearer === SB_KEY) || (who === ADMIN_EMAIL)
  if (!isAdmin) {
    // ⚠️ count:'exact' 는 전체를 세느라 표를 끝까지 훑는다. 존재 여부만 알면 되므로
    //    첫 한 줄만 찾고 멈춘다 (표가 커져도 느려지지 않게).
    const { data: hit, error } = await svc
      .from('voca_words').select('id').ilike('en', word).limit(1)
    if (error) return json({ ok: false, reason: 'lookup_failed' })
    if (!hit || !hit.length) return json({ ok: false, reason: 'not_in_dictionary' })
  }

  const res = await makeAudio(word, path)
  if (!res.ok) return json({ ok: false, reason: 'tts_failed', detail: res.detail }, 502)
  return json({ ok: true, url })
})
