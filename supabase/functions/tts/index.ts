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

// 앱의 _sentHash() 와 동일 (djb2-xor). 예문 파일명은 '단어_해시.mp3' 라서,
// 예문 글자가 하나라도 바뀌면 해시가 달라져 옛 파일을 찾지 않는다 = 불일치 원천 차단.
function sentHash(str: string) {
  const t = String(str || '').trim()
  let h = 5381
  for (let i = 0; i < t.length; i++) h = ((h * 33) ^ t.charCodeAt(i)) >>> 0
  return h.toString(36)
}
// 예문은 단어보다 10배 길다. 지나치게 긴 것은 비용·품질 모두 손해라 자른다.
const SENT_MAX = 220

async function alreadyThere(path: string) {
  try {
    const r = await fetch(`${PUBLIC}/${path}`, { method: 'HEAD' })
    return r.ok
  } catch { return false }
}

async function makeAudio(text: string, path: string) {
  const r = await fetch(`https://texttospeech.googleapis.com/v1/text:synthesize?key=${GKEY}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      input: { text },
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
    const limit = Math.min(Math.max(Number(body.limit) || 1000, 1), 3000)
    const offset = Math.max(Number(body.offset) || 0, 0)
    const genCap = Math.min(Math.max(Number(body.max_new) || 80, 1), 150)  // 이번 호출에서 새로 만들 최대 개수

    // ⚠️ 단어마다 파일 존재를 HTTP 로 확인하면(HEAD) 3만 개를 훑는 데 몇 시간이 걸린다.
    //    저장소 목록을 한 번에 받아 집합으로 만들어 두고 비교한다 (1,000개씩 ~17번).
    const kind = String(body.kind ?? 'w') === 's' ? 's' : 'w'   // 'w' 단어 · 's' 예문
    const have = new Set<string>()
    for (let off = 0; off < 200000; off += 1000) {
      const { data, error } = await svc.storage.from(BUCKET).list(kind, { limit: 1000, offset: off })
      if (error) return json({ error: 'list_failed', detail: error.message }, 500)
      for (const f of data ?? []) have.add(String(f.name || '').replace(/\.mp3$/i, ''))
      if (!data || data.length < 1000) break
    }

    const { data: rows, error } = await svc
      .from('voca_words').select(kind === 's' ? 'en,sentence' : 'en').not('en', 'is', null)
      .order('en').range(offset, offset + limit - 1)
    if (error) return json({ error: 'query_failed', detail: error.message }, 500)

    let made = 0, skipped = 0, pending = 0
    const failed: unknown[] = []
    const seen = new Set<string>()
    for (const row of rows ?? []) {
      const w = String(row.en || '').trim().toLowerCase()
      // 영어만. 스페인어 단어장('¿cómo está?' 등)에 영어 음성을 입히면 안 되고,
      // 악센트를 떼면 파일명도 엉뚱해진다. (스페인어 음성은 /es/w/ 로 따로 있다)
      if (!/^[a-z][a-z' -]{0,30}$/.test(w)) { skipped++; continue }
      const base = safeName(w)
      if (!base) { skipped++; continue }

      const sent = kind === 's' ? String((row as { sentence?: string }).sentence || '').trim() : ''
      if (kind === 's' && (!sent || sent.length > SENT_MAX)) { skipped++; continue }
      const key = kind === 's' ? `${base}_${sentHash(sent)}` : base

      if (seen.has(key) || have.has(key)) { skipped++; continue }
      seen.add(key)
      if (made >= genCap) { pending++; continue }     // 시간 제한에 걸리지 않게 나눠 만든다
      const res = await makeAudio(kind === 's' ? sent : w, `${kind}/${key}.mp3`)
      if (res.ok) { made++; have.add(key) } else failed.push({ word: w, detail: res.detail })
    }
    const scanned = rows?.length ?? 0
    return json({
      ok: true, made, skipped, scanned,
      // 이번 회차에 다 못 만든 게 있으면 같은 구간을 한 번 더 돌려야 한다
      next_offset: pending > 0 ? offset : offset + scanned,
      still_todo_here: pending,
      // ⚠️ Supabase 는 한 번에 최대 1,000행만 돌려준다. limit 을 2,000 으로 줘도
      //    scanned 는 1,000 에서 멈추므로 'scanned < limit' 를 끝으로 보면 안 된다
      //    (3만 행이 남았는데도 끝났다고 답하게 된다). 빈 구간이 나와야 진짜 끝이다.
      done: pending === 0 && scanned === 0,
      failed,
    })
  }

  // ── 예문 하나 ────────────────────────────────────────────────
  // { "word": "candle", "sentence": "She lit a candle." }
  const sentence = String(body.sentence ?? '').trim()
  if (sentence) {
    const w0 = String(body.word ?? '').trim().toLowerCase()
    const k0 = safeName(w0)
    if (!k0 || sentence.length > SENT_MAX) return json({ ok: false, reason: 'bad_sentence' })
    const path = `s/${k0}_${sentHash(sentence)}.mp3`
    const url = `${PUBLIC}/${path}`
    if (await alreadyThere(path)) return json({ ok: true, cached: true, url })

    const isAdmin0 = (bearer === SB_KEY) || (who === ADMIN_EMAIL)
    if (!isAdmin0) {
      // 저장된 예문만 만든다 — 아무 문장이나 보내 저장소를 불리지 못하게
      const { data: hit, error } = await svc
        .from('voca_words').select('id').eq('sentence', sentence).limit(1)
      if (error) return json({ ok: false, reason: 'lookup_failed' })
      if (!hit || !hit.length) return json({ ok: false, reason: 'not_in_dictionary' })
    }
    const r0 = await makeAudio(sentence, path)
    if (!r0.ok) return json({ ok: false, reason: 'tts_failed', detail: r0.detail }, 502)
    return json({ ok: true, url })
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
