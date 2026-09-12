// IM VOCA Service Worker
// 전략: HTML은 항상 네트워크 우선 (최신 유지), 정적 자원은 캐시 우선 (속도)

const CACHE_VERSION = 'imvoca-v6';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

// 미리 캐시할 정적 자원 (앱 첫 실행 시 빠르게)
const PRECACHE_URLS = [
  '/',
  '/manifest.json',
  '/2.png',
  '/og-image.png'
];

// 설치 — 정적 자원 미리 캐시. (skipWaiting 은 자동으로 하지 않음:
//  업데이트 토스트를 눌렀을 때만 SKIP_WAITING 메시지로 활성화 → 사용자 흐름 안 끊김)
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS).catch(() => {}))
  );
});

// 페이지에서 업데이트 토스트를 누르면 즉시 활성화
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

// 활성화 — 옛날 캐시 정리
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names
          .filter((name) => !name.startsWith(CACHE_VERSION))
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// 본문 비교용 간단 해시 (FNV-1a 32bit) — 길이가 같아도 내용이 다르면 잡아낸다
function _digest(s) {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); }
  return h >>> 0;
}

// 요청 가로채기
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // GET 요청만 처리 (POST/PUT 등은 그대로 통과)
  if (request.method !== 'GET') return;

  // Supabase, Stripe, Gemini, Google Books 등 API 요청은 캐시 안 함 (항상 최신)
  if (
    url.hostname.includes('supabase.co') ||
    url.hostname.includes('stripe.com') ||
    url.hostname.includes('googleapis.com') ||
    url.hostname.includes('generativelanguage') ||
    url.hostname.includes('canva.com')
  ) {
    return; // 기본 네트워크 동작 사용
  }

  // HTML/Document 요청: 캐시 즉시 표시 + 백그라운드 갱신 (stale-while-revalidate)
  // → 앱 재시작이 네트워크를 기다리지 않고 바로 뜸. 새 버전이 받아지면 앱에 알려
  //   '✨ 새 버전 — 새로고침' 토스트가 뜬다 (HTML_UPDATED 메시지).
  if (request.mode === 'navigate' || request.destination === 'document') {
    event.respondWith((async () => {
      // ⚠️ 반드시 RUNTIME 캐시를 먼저 본다. caches.match() 는 생성 순서대로 찾기 때문에
      //    설치 때 넣어둔 STATIC 의 '/' 를 항상 먼저 돌려줘, 갱신된 사본이 무시되고
      //    "새 버전" 알림이 매번 뜨던 문제가 있었다.
      const runtime = await caches.open(RUNTIME_CACHE);
      const cached = (await runtime.match(request)) || (await runtime.match('/'))
                  || (await caches.match(request)) || (await caches.match('/'));
      const network = fetch(request).then(async (response) => {
        if (response.ok) {
          const forCompare = response.clone();
          await runtime.put(request, response.clone());
          // 내용이 실제로 바뀌었을 때만 알림 — 헤더(ETag)는 CDN 사정으로 흔들리므로 본문을 비교
          try {
            if (cached) {
              const prevText = await cached.clone().text();
              const newText = await forCompare.text();
              if (prevText.length !== newText.length || _digest(prevText) !== _digest(newText)) {
                const clients = await self.clients.matchAll({ type: 'window' });
                clients.forEach((c) => c.postMessage({ type: 'HTML_UPDATED' }));
              }
            }
          } catch (e) {}
        }
        return response;
      }).catch(() => null);
      if (cached) { event.waitUntil(network); return cached; }
      const fresh = await network;
      return fresh || caches.match('/');
    })());
    return;
  }

  // 정적 자원 (이미지, CSS, JS 등): 캐시 우선
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) {
        // 캐시에서 즉시 반환, 백그라운드로 업데이트
        fetch(request).then((response) => {
          if (response.ok) {
            caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, response));
          }
        }).catch(() => {});
        return cached;
      }
      // 캐시 없으면 네트워크에서 가져와 캐시
      return fetch(request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, clone));
        }
        return response;
      }).catch(() => cached);
    })
  );
});
