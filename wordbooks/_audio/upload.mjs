#!/usr/bin/env node
// ============================================================
// IM VOCA — 시리즈별 예문 오디오를 Supabase Storage 로 업로드
//
// 저장소 audio/s/{series}/*.mp3  →  Supabase 'audio' 버킷 s/{series}/*.mp3
// (GitHub Pages 에 있던 걸 기존 음원과 같은 Supabase 로 통합)
//
// 필요 env:
//   SUPABASE_URL          예: https://ziatqkjlafucqtwshhla.supabase.co
//   SUPABASE_SERVICE_KEY  service_role 키 (스토리지 쓰기용)
//   ⚠️ service_role 키는 DB 전체 권한 → 안전한 로컬 환경에서만, 절대 공유 금지.
//
// 실행(저장소 루트에서 git pull 후):
//   SUPABASE_URL=... SUPABASE_SERVICE_KEY=... node wordbooks/_audio/upload.mjs suneung mid toeic
// ============================================================
import { readdir, readFile } from 'node:fs/promises';

const URL_ = process.env.SUPABASE_URL, KEY = process.env.SUPABASE_SERVICE_KEY;
if (!URL_ || !KEY) { console.error('env 필요: SUPABASE_URL, SUPABASE_SERVICE_KEY'); process.exit(1); }
const BUCKET = 'audio';
const CONC = 8;
const OVERWRITE = false;             // true 면 기존 파일 덮어씀
const REPO = new URL('../../', import.meta.url);

async function put(path, buf) {
  const r = await fetch(`${URL_}/storage/v1/object/${BUCKET}/${path}`, {
    method: 'POST',
    headers: { apikey: KEY, Authorization: `Bearer ${KEY}`, 'Content-Type': 'audio/mpeg', 'x-upsert': OVERWRITE ? 'true' : 'false' },
    body: buf,
  });
  if (r.ok) return 'ok';
  if (r.status === 409) return 'skip';                 // 이미 있음
  throw new Error(`${r.status} ${(await r.text()).slice(0, 120)}`);
}

async function upSeries(series) {
  const dir = new URL(`audio/s/${series}/`, REPO);
  const files = (await readdir(dir)).filter(f => f.endsWith('.mp3'));
  console.log(`[${series}] ${files.length} 파일`);
  let ok = 0, skip = 0, fail = 0, i = 0;
  async function worker() {
    while (i < files.length) {
      const f = files[i++];
      try {
        const buf = await readFile(new URL(f, dir));
        const res = await put(`s/${series}/${f}`, buf);
        res === 'ok' ? ok++ : skip++;
      } catch (e) { fail++; if (fail <= 8) console.warn(`  ✗ ${f}: ${e.message}`); }
      const n = ok + skip + fail; if (n % 200 === 0) console.log(`  ${n}/${files.length} (올림 ${ok}·건너뜀 ${skip}·실패 ${fail})`);
    }
  }
  await Promise.all(Array.from({ length: CONC }, worker));
  console.log(`[${series}] 완료 — 올림 ${ok}·건너뜀 ${skip}·실패 ${fail}`);
  if (fail) console.log('  (실패분은 다시 실행하면 재시도 — 기존은 409 로 건너뜀)');
}

const list = process.argv.slice(2);
if (!list.length) { console.error('사용법: node upload.mjs suneung [mid toeic]'); process.exit(1); }
for (const s of list) await upSeries(s);
console.log('\n끝. Supabase audio 버킷 s/{series}/ 에 올라갔습니다.');
