#!/usr/bin/env node
// ============================================================
// IM VOCA — 시리즈별 예문 발음 MP3 생성·업로드
//
// 배경: 같은 단어라도 수능/중등/토익 예문이 서로 달라, 예문 발음을
//       s/{series}/{word}.mp3 로 시리즈별로 분리해야 화면 예문과 일치합니다.
//       (앱 코드는 이미 s/suneung, s/mid, s/toeic 폴더에서 읽도록 배포됨.
//        파일이 없으면 앱이 자동으로 기기 TTS 로 예문을 읽어 항상 일치)
//
// 이 스크립트: wordbooks/_audio/{series}.json 매니페스트를 읽어
//   1) 각 예문을 Google Cloud TTS(원어민 Neural 음성)로 합성
//   2) Supabase Storage 의 audio 버킷 s/{series}/{word}.mp3 로 업로드
//   이미 있는 파일은 건너뜀(중단 후 재실행 안전).
//
// 필요 env:
//   GOOGLE_TTS_KEY        Google Cloud Text-to-Speech API 키
//   SUPABASE_URL          예: https://xxxx.supabase.co
//   SUPABASE_SERVICE_KEY  service_role 키(스토리지 업로드용)
//
// 실행: node generate.mjs suneung        (한 시리즈)
//       node generate.mjs suneung mid toeic
//
// Node 18+ (fetch 내장). 다른 TTS(예: 기존 Gemini TTS)를 쓰려면 synth() 만 교체.
// ============================================================
import { readFile } from 'node:fs/promises';

const GOOGLE_TTS_KEY = process.env.GOOGLE_TTS_KEY;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const BUCKET = 'audio';
// 시리즈별 음성: 영어는 미국 원어민 Neural. (필요시 변경)
const VOICE = { languageCode: 'en-US', name: 'en-US-Neural2-D' };
const CONCURRENCY = 4;      // 동시 처리 수(레이트리밋 여유)
const OVERWRITE = false;    // true 면 기존 파일도 다시 만듦

if (!GOOGLE_TTS_KEY || !SUPABASE_URL || !SERVICE_KEY) {
  console.error('env 필요: GOOGLE_TTS_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY');
  process.exit(1);
}

// 예문 텍스트 → mp3 base64 (Google Cloud TTS)
async function synth(text) {
  const res = await fetch(`https://texttospeech.googleapis.com/v1/text:synthesize?key=${GOOGLE_TTS_KEY}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      input: { text },
      voice: VOICE,
      audioConfig: { audioEncoding: 'MP3', speakingRate: 0.98 },
    }),
  });
  if (!res.ok) throw new Error(`TTS ${res.status}: ${(await res.text()).slice(0, 200)}`);
  const j = await res.json();
  return Buffer.from(j.audioContent, 'base64');
}

async function exists(path) {
  const r = await fetch(`${SUPABASE_URL}/storage/v1/object/info/public/${BUCKET}/${path}`, {
    headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}` },
  });
  return r.ok;
}

async function upload(path, buf) {
  const r = await fetch(`${SUPABASE_URL}/storage/v1/object/${BUCKET}/${path}`, {
    method: 'POST',
    headers: {
      apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}`,
      'Content-Type': 'audio/mpeg', 'x-upsert': OVERWRITE ? 'true' : 'false',
    },
    body: buf,
  });
  if (!r.ok && r.status !== 409) throw new Error(`upload ${r.status}: ${(await r.text()).slice(0, 200)}`);
}

async function runSeries(series) {
  // gen-{series}.json = 시리즈별 예문이 갈리는 '중복 단어'만(생성 대상). 유니크 단어는 기존 원어민 s/{단어}.mp3 재사용.
  const manifest = JSON.parse(await readFile(new URL(`./gen-${series}.json`, import.meta.url)));
  console.log(`\n[${series}] ${manifest.length} 문장`);
  let done = 0, skip = 0, fail = 0;
  let i = 0;
  async function worker() {
    while (i < manifest.length) {
      const idx = i++; const { w, s } = manifest[idx];
      const path = `s/${series}/${w}.mp3`;
      try {
        if (!OVERWRITE && (await exists(path))) { skip++; }
        else { await upload(path, await synth(s)); done++; }
      } catch (e) { fail++; console.warn(`  ✗ ${w}: ${e.message}`); }
      if ((done + skip + fail) % 100 === 0) console.log(`  ${done + skip + fail}/${manifest.length} (생성 ${done} · 건너뜀 ${skip} · 실패 ${fail})`);
    }
  }
  await Promise.all(Array.from({ length: CONCURRENCY }, worker));
  console.log(`[${series}] 완료 — 생성 ${done} · 건너뜀 ${skip} · 실패 ${fail}`);
}

const series = process.argv.slice(2);
if (!series.length) { console.error('사용법: node generate.mjs suneung [mid toeic]'); process.exit(1); }
for (const s of series) await runSeries(s);
console.log('\n끝. 앱에서 예문 발음이 시리즈별 원어민 음성으로 재생됩니다.');
