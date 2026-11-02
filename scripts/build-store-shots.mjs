#!/usr/bin/env node
/**
 * 언어별 스토어 스크린샷 만들기.
 *
 * 왜 이 스크립트가 필요한가: scripts/build-appstore-shots.py 는 이미 찍어둔
 * 한국어 screenshot*.png 를 6.9인치로 늘리기만 한다. 언어별은 늘려서 만들 수
 * 없고 실제로 그 언어로 띄워 찍어야 한다.
 *
 * 방식: 로컬 서버로 index.html 을 띄우고 둘러보기(게스트)로 들어간다.
 *   - 로그인이 필요 없다 → 테스트 계정도, 가짜 데이터도 없다
 *   - 공식 단어장을 실제 DB 에서 받아온다 → 화면에 보이는 단어와 뜻이 다 진짜다
 *   - localStorage['imvoca.nativeLang'] 를 미리 심어 그 언어로 시작시킨다
 *
 * ⚠️ 영어(en)는 뺐다. 공식 단어장의 뜻은 ko 원본 + zh/ja/es 번역만 있어서
 *    native_lang=en 이면 _officialBooksForMe() 가 false 가 되고 책장이 0권이다.
 *    빈 책장을 스토어에 올릴 수는 없다. 영어까지 찍으려면 먼저
 *    scripts/translate-official.py --lang en 으로 뜻을 만들어야 한다.
 *
 * ⚠️ 이건 웹 화면이다. App Store 제출본으로는 시뮬레이터에서 'iPhone 17 Pro Max'
 *    로 띄워 ⌘S 로 찍은 것이 가장 낫다(실제 iOS 앱 화면). 이 스크립트 결과는
 *    언어별 초안·Play 용으로 쓰기 좋다.
 *
 * 실행:
 *   cd /home/user/voca
 *   (fuser -k 8899/tcp 2>/dev/null; true)
 *   (python3 -m http.server 8899 >/dev/null 2>&1 &)
 *   node scripts/build-store-shots.mjs
 *   fuser -k 8899/tcp
 *
 * 결과: appstore/<lang>/ios-6.9-<n>.png   1320x2868  (App Store 6.9")
 *       appstore/<lang>/play-<n>.png      1206x2622  (Play)
 */
import { mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';

// playwright-core 는 이 저장소에 없고 컨테이너에 전역으로 깔려 있다.
// ESM 의 import 는 NODE_PATH 를 보지 않으므로 그냥 import 하면
// ERR_MODULE_NOT_FOUND 가 난다 → require 로 경로를 직접 찾아 쓴다.
const _req = createRequire(import.meta.url);
const _paths = [
  '/opt/node-tools/node_modules',
  '/usr/local/lib/node_modules_global',
  '/opt/node22/lib/node_modules',
  process.env.NODE_PATH || '',
].filter(Boolean);
let chromium;
for (const base of [null, ..._paths]) {
  try {
    const id = base ? _req.resolve('playwright-core', { paths: [base] }) : 'playwright-core';
    ({ chromium } = _req(id));
    break;
  } catch (e) { /* 다음 경로 */ }
}
if (!chromium) {
  console.error('playwright-core 를 찾지 못했습니다. 아래로 경로를 확인하세요:');
  console.error("  node -e \"console.log(require.resolve('playwright-core',{paths:['/opt/node-tools/node_modules']}))\"");
  process.exit(1);
}

const EXE = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const BASE = 'http://127.0.0.1:8899/index.html?probe=1';
const LANGS = ['ko', 'zh', 'ja', 'es'];
const SIZES = [
  { tag: 'ios-6.9', w: 440, h: 956, dpr: 3 },   // → 1320x2868
  { tag: 'play',    w: 402, h: 874, dpr: 3 },   // → 1206x2622
];

// 찍을 화면. 각 단계는 페이지 안에서 앱 상태를 만들고 렌더까지 끝낸다.
const SHOTS = [
  { name: '책장', fn: async (pg) => {
      await pg.evaluate(async () => { await startGuest(); });
      await pg.waitForTimeout(900);
    }},
  { name: 'Day 목록', fn: async (pg) => {
      await pg.evaluate(async () => {
        const b = eval('books').find(x => /^Lv\.1\s*$/.test(String(x.title).trim())) || eval('books')[0];
        push({ name: 'book', bookId: b.id });
      });
      await pg.waitForTimeout(1500);
    }},
  { name: '단어 목록', fn: async (pg) => {
      await pg.evaluate(async () => {
        const st = eval('stack'); const bid = st[st.length - 1].bookId;
        await ensureOfficialBookWords(bid);
        const bk = findBook(bid);
        const pgs = (bk.pages || []).slice().sort((a, c) => (parseFloat(a.num)||0) - (parseFloat(c.num)||0));
        push({ name: 'page-words', bookId: bid, pageNum: pgs[0].num });
      });
      await pg.waitForTimeout(1200);
    }},
  { name: '암기 카드(뜻)', fn: async (pg) => {
      await pg.evaluate(async () => {
        const st = eval('stack'); const r = st[st.length - 1];
        initStudy(r.bookId, 'page', r.pageNum);
        push({ name: 'study-cards', bookId: r.bookId, scope: 'page', pageNum: r.pageNum });
        eval('studyState').flipped = true; renderStudyCard();   // 뒷면(뜻)을 보여준다
      });
      await pg.waitForTimeout(700);
    }},
  { name: '레벨 테스트', fn: async (pg) => {
      await pg.evaluate(async () => {
        goTab('books');
        window.toast = () => {};
        startLevelTest('screenshot');
      });
      await pg.waitForTimeout(2500);
    }},
];

const b = await chromium.launch({ executablePath: EXE, args: ['--no-sandbox'] });
let total = 0;
for (const lang of LANGS) {
  await mkdir(`appstore/${lang}`, { recursive: true });
  for (const sz of SIZES) {
    const ctx = await b.newContext({
      viewport: { width: sz.w, height: sz.h }, deviceScaleFactor: sz.dpr });
    await ctx.addInitScript((l) => {
      try { localStorage.setItem('imvoca.nativeLang', l); } catch (e) {}
    }, lang);
    const pg = await ctx.newPage();
    pg.on('pageerror', e => console.log(`  [${lang}/${sz.tag}] PAGEERR`, e.message.slice(0, 90)));
    await pg.goto(BASE, { waitUntil: 'domcontentloaded' });
    await pg.waitForTimeout(1800);
    for (let i = 0; i < SHOTS.length; i++) {
      try { await SHOTS[i].fn(pg); } catch (e) {
        console.log(`  [${lang}/${sz.tag}] ${SHOTS[i].name} 실패: ${e.message.slice(0, 80)}`); continue;
      }
      const path = `appstore/${lang}/${sz.tag}-${i + 1}.png`;
      await pg.screenshot({ path });
      total++;
    }
    console.log(`${lang} / ${sz.tag}  ${sz.w * sz.dpr}x${sz.h * sz.dpr}  ${SHOTS.length}장`);
    await ctx.close();
  }
}
await b.close();
console.log(`\n${total}장 완료 → appstore/<lang>/`);
