#!/usr/bin/env node
// ============================================================
// IM VOCA — 시리즈별 '중복 단어' 예문 발음 MP3 생성
//
// 배경: 같은 단어라도 수능/중등/토익 예문이 달라, 중복 단어(conflict-words.json)만
//       시리즈별로 예문 오디오를 만들어 s/{series}/{word}.mp3 로 저장.
//       유니크 단어는 기존 원어민 오디오 재사용(생성 안 함).
//       앱은 중복 단어만 이 폴더에서 읽고, 없으면 기기 TTS 로 예문을 읽음.
//
// 저장 위치: 저장소 /audio/s/{series}/  (GitHub Pages → imvoca.app/audio/... 로 서빙)
// 필요 env:  GOOGLE_TTS_KEY  (Google Cloud Text-to-Speech API 키; 무료 한도 안)
// 실행:      GOOGLE_TTS_KEY=... node generate.mjs suneung mid toeic
//            생성 후 git add audio/ && commit && push
//
// 새 카테고리 추가 시: 1) 해당 wordbooks JSON 추가  2) analyze.py 로 conflict/gen 재생성
//   3) index.html 의 _audioSeriesFromTitle 에 제목→시리즈 매핑 한 줄 추가  4) 이 스크립트 실행
// ============================================================
import { readFile, writeFile, access, mkdir } from 'node:fs/promises';

const KEY = process.env.GOOGLE_TTS_KEY;
if (!KEY) { console.error('env GOOGLE_TTS_KEY 필요'); process.exit(1); }
const VOICE = { languageCode: 'en-US', name: 'en-US-Neural2-D' }; // 원어민 Neural 음성
const CONC = 6, TRIES = 4;
const REPO = new URL('../../', import.meta.url); // 저장소 루트

async function synth(text) {
  for (let t = 0; t < TRIES; t++) {
    try {
      const r = await fetch(`https://texttospeech.googleapis.com/v1/text:synthesize?key=${KEY}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: { text }, voice: VOICE, audioConfig: { audioEncoding: 'MP3', speakingRate: 0.98 } }),
      });
      if (r.status === 200) return Buffer.from((await r.json()).audioContent, 'base64');
      if (r.status === 429 || r.status >= 500) { await new Promise(s => setTimeout(s, 800 * (t + 1))); continue; }
      throw new Error(`http ${r.status}`);
    } catch (e) { if (t === TRIES - 1) throw e; await new Promise(s => setTimeout(s, 700 * (t + 1))); }
  }
  throw new Error('retries exhausted');
}

async function runSeries(series) {
  const man = JSON.parse(await readFile(new URL(`./gen-${series}.json`, import.meta.url)));
  const outDir = new URL(`audio/s/${series}/`, REPO);
  await mkdir(outDir, { recursive: true });
  console.log(`[${series}] ${man.length} 문장`);
  let done = 0, skip = 0, fail = 0, i = 0;
  async function worker() {
    while (i < man.length) {
      const { w, s } = man[i++];
      const path = new URL(`${w}.mp3`, outDir);
      try {
        try { await access(path); skip++; }
        catch { await writeFile(path, await synth(s)); done++; }
      } catch (e) { fail++; if (fail <= 8) console.warn(`  ✗ ${w}: ${e.message}`); }
      const n = done + skip + fail; if (n % 200 === 0) console.log(`  ${n}/${man.length} (생성 ${done}·건너뜀 ${skip}·실패 ${fail})`);
    }
  }
  await Promise.all(Array.from({ length: CONC }, worker));
  console.log(`[${series}] 완료 — 생성 ${done}·건너뜀 ${skip}·실패 ${fail}`);
  if (fail) console.log('  (실패분은 다시 실행하면 채워짐 — 기존 파일은 건너뜀)');
}

const list = process.argv.slice(2);
if (!list.length) { console.error('사용법: node generate.mjs suneung [mid toeic]'); process.exit(1); }
for (const s of list) await runSeries(s);
