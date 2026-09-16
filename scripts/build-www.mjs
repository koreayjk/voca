// ============================================================
// IM VOCA — iOS 네이티브 셸용 www/ 빌드
//
// 왜 필요한가:
//   애플은 '웹사이트를 그대로 감싼 앱'(가이드라인 4.2)을 반려한다. 그래서 iOS 앱은
//   원격 URL 을 띄우지 않고 화면 자체를 앱 안에 담아서 배포한다.
//   → 웹(imvoca.app)은 지금처럼 git push 로 즉시 배포되고,
//     iOS 앱은 이 스크립트로 만든 www/ 를 Xcode 로 다시 빌드해야 반영된다.
//
//   단어장·단어·복습 일정·프리미엄 여부는 전부 Supabase 에서 실시간으로 오므로
//   '얼어붙는' 것은 화면 코드뿐이다.
//
// 실행: npm run build   (npm run ios 가 이걸 부르고 나서 cap sync 한다)
// ============================================================
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'www');

// 앱 안에 담을 파일. 여기 없는 것은 네트워크로 받는다(공식 단어장 내용·발음 mp3·프로모 이미지 등).
// 용량을 아끼려고 최소한만 담는다 — 오프라인에서도 '화면이 뜨는' 데 필요한 것들.
const ASSETS = [
  '2.png',
  'og-image.png',
  'icon-192.png',
  'icon-512.png',
  'icon-512-maskable.png',
  'cover-suneung-basic.jpg',
  'cover-suneung-core.jpg',
  'cover-suneung-hard.jpg',
  'cover-suneung-idiom.jpg',
  'wordbooks/_audio/conflict-words.json',
];

// 절대 URL → 번들 안의 상대 경로. (앱은 capacitor://localhost 에서 돌아가므로
// https://imvoca.app/... 로 남겨두면 오프라인에서 로고조차 안 뜬다)
const REWRITES = [
  [/https:\/\/imvoca\.app\/(2\.png|og-image\.png|icon-192\.png|icon-512\.png|icon-512-maskable\.png)/g, '$1'],
  [/(["'(])\/(2\.png|og-image\.png|icon-192\.png|icon-512(?:-maskable)?\.png|manifest\.json)/g, '$1$2'],
];

async function main() {
  await rm(OUT, { recursive: true, force: true });
  await mkdir(OUT, { recursive: true });

  let html = await readFile(join(ROOT, 'index.html'), 'utf8');
  for (const [re, to] of REWRITES) html = html.replace(re, to);

  // 네이티브임을 HTML 파싱 시점에 알려둔다. Capacitor 브리지는 나중에 주입되지만
  // 이 플래그는 첫 줄부터 살아 있어서, 초기 렌더에서도 결제 UI 가 깜빡이지 않는다.
  html = html.replace('<head>', '<head>\n<script>window.__IMVOCA_IOS_APP__ = true;</script>');
  if (!html.includes('__IMVOCA_IOS_APP__')) throw new Error('<head> 를 못 찾았습니다 — index.html 구조가 바뀌었는지 확인하세요');

  await writeFile(join(OUT, 'index.html'), html);

  const missing = [];
  for (const rel of ASSETS) {
    const src = join(ROOT, rel);
    if (!existsSync(src)) { missing.push(rel); continue; }
    await mkdir(dirname(join(OUT, rel)), { recursive: true });
    await cp(src, join(OUT, rel));
  }
  if (missing.length) throw new Error('번들할 파일이 없습니다: ' + missing.join(', '));

  // manifest 는 네이티브에서 안 쓰지만, 같은 HTML 이 <link rel=manifest> 를 참조하므로
  // 404 를 남기지 않도록 상대 경로판을 하나 넣어준다.
  const mf = JSON.parse(await readFile(join(ROOT, 'manifest.json'), 'utf8'));
  mf.start_url = './';
  mf.scope = './';
  delete mf.screenshots;
  delete mf.shortcuts;
  mf.icons = mf.icons.map((i) => ({ ...i, src: i.src.replace(/^https:\/\/imvoca\.app\//, '').replace(/\?v=\d+$/, '') }));
  await writeFile(join(OUT, 'manifest.json'), JSON.stringify(mf, null, 2));

  // sw.js 는 일부러 담지 않는다. 앱은 파일이 이미 로컬에 있어서 캐시가 필요 없고,
  // 서비스워커 캐시가 남으면 앱을 업데이트해도 옛 화면이 뜨는 사고가 난다.
  console.log(`www/ 빌드 완료 — index.html + ${ASSETS.length}개 자산`);
}

main().catch((e) => { console.error('빌드 실패:', e.message); process.exit(1); });
