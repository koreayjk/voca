// ============================================================
// IM VOCA — 예문 원어민 발음 재생성 (콘텐츠 해시 파일명)
// 목적: 앱이 s/{word}~{문장해시}.mp3 를 찾도록 바뀌었으니, '현재 DB 예문'으로
//       원어민 TTS mp3 를 다시 만들어 그 파일명으로 업로드 → 원어민 발음 복원.
//       (파일이 없으면 앱은 자동으로 예문을 TTS 로 읽어 불일치는 원래 안 남)
// 소스: Supabase DB 의 공식책 예문(= 앱이 실제로 보여주는 문장)에서 직접 읽음.
// 실행: 아래 환경변수를 넣고
//   SUPABASE_SERVICE_KEY=eyJ...(service_role) GOOGLE_TTS_KEY=AIza... node wordbooks/_audio/gen-sentences.mjs
//   (Node 18+ 필요. Google TTS Neural2 · 월 100만자 무료 범위 내 예상)
// 안전: 이미 있는 파일은 건너뜀(재실행해도 중복 과금 없음). 단어 발음(w/)은 안 건드림.
// ============================================================
const SB_URL = 'https://ziatqkjlafucqtwshhla.supabase.co';
const SVC  = process.env.SUPABASE_SERVICE_KEY;
const GKEY = process.env.GOOGLE_TTS_KEY;
if (!SVC || !GKEY) { console.error('❌ 환경변수 SUPABASE_SERVICE_KEY 와 GOOGLE_TTS_KEY 가 필요합니다.'); process.exit(1); }

// 앱과 동일한 파일명/해시 알고리즘 (index.html 의 _safeAudio / _sentHash 와 반드시 일치)
const safeAudio = en => (en||'').toLowerCase().replace(/[^a-z0-9 ]/g,'').trim().replace(/\s+/g,'-');
const sentHash  = str => { str=String(str||'').trim(); let h=5381; for(let i=0;i<str.length;i++){ h=((h*33) ^ str.charCodeAt(i))>>>0; } return h.toString(36); };
const sleep = ms => new Promise(r=>setTimeout(r,ms));

// 1) 공식책의 단어+예문 로드 (DB = 앱이 보여주는 소스)
console.log('공식 단어장 로드 중…');
const res = await fetch(`${SB_URL}/rest/v1/voca_books?is_official=eq.true&select=title,voca_pages(voca_words(en,sentence,analysis))`,
  { headers: { apikey: SVC, Authorization: 'Bearer ' + SVC } });
if (!res.ok) { console.error('DB 로드 실패', res.status, await res.text()); process.exit(1); }
const books = await res.json();

// 2) 대상 수집 (파일 경로 기준 중복 제거) — 앱의 _exOf: analysis.example || sentence
const jobs = new Map(); // path -> { text, lang }
for (const b of (books||[])) {
  for (const p of (b.voca_pages||[])) {
    for (const w of (p.voca_words||[])) {
      const a = w.analysis || {};
      const ex = String(a.example || w.sentence || '').trim();
      if (!ex) continue;
      const safe = safeAudio(w.en); if (!safe) continue;
      const lang = a._lang === 'es' ? 'es' : 'en';
      const path = (lang==='es' ? 'es/s/' : 's/') + safe + '_' + sentHash(ex) + '.mp3'; // '_' (Supabase 는 '~' 불가)
      if (!jobs.has(path)) jobs.set(path, { text: ex, lang });
    }
  }
}
console.log('생성 대상 예문(고유):', jobs.size);

// 3) TTS 생성 + Supabase Storage 업로드 (이미 있으면 스킵)
let done=0, skip=0, fail=0, i=0;
for (const [path, job] of jobs) {
  i++;
  try {
    const head = await fetch(`${SB_URL}/storage/v1/object/public/audio/${path}`, { method: 'HEAD' });
    if (head.status === 200) { skip++; continue; }

    const voice = job.lang==='es'
      ? { languageCode:'es-ES', name:'es-ES-Neural2-B' }
      : { languageCode:'en-US', name:'en-US-Neural2-D' };
    const tts = await fetch(`https://texttospeech.googleapis.com/v1/text:synthesize?key=${GKEY}`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ input:{ text: job.text }, voice, audioConfig:{ audioEncoding:'MP3' } })
    });
    const td = await tts.json();
    if (!td.audioContent) { fail++; console.warn('TTS 실패:', path, JSON.stringify(td).slice(0,140)); continue; }
    const buf = Buffer.from(td.audioContent, 'base64');

    const up = await fetch(`${SB_URL}/storage/v1/object/audio/${path}`, {
      method:'POST', headers:{ apikey:SVC, Authorization:'Bearer '+SVC, 'Content-Type':'audio/mpeg', 'x-upsert':'true' },
      body: buf
    });
    if (up.status>=200 && up.status<300) done++;
    else { fail++; console.warn('업로드 실패:', path, up.status, (await up.text()).slice(0,120)); }
    await sleep(40); // 과도한 요청 방지
  } catch(e) { fail++; console.warn('오류:', path, e.message); }
  if (i%50===0) console.log(`${i}/${jobs.size} · 생성 ${done} · 스킵 ${skip} · 실패 ${fail}`);
}
console.log(`\n✅ 완료 — 생성 ${done}, 스킵(이미있음) ${skip}, 실패 ${fail}`);
console.log('실패가 있으면 다시 실행하면 됩니다(이미 올라간 건 자동 스킵).');
