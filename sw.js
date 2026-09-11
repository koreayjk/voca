// IM VOCA Service Worker
// 전략: HTML은 항상 네트워크 우선 (최신 유지), 정적 자원은 캐시 우선 (속도)

const CACHE_VERSION = 'imvoca-v5';
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
      const cached = (await caches.match(request)) || (await caches.match('/'));
      const network = fetch(request).then(async (response) => {
        if (response.ok) {
          const cache = await caches.open(RUNTIME_CACHE);
          const clone = response.clone();
          await cache.put(request, clone);
          // 내용이 실제로 바뀌었을 때만 열려있는 앱에 알림 (ETag/Last-Modified 비교)
          try {
            const prevTag = cached && (cached.headers.get('etag') || cached.headers.get('last-modified'));
            const newTag = response.headers.get('etag') || response.headers.get('last-modified');
            if (prevTag && newTag && prevTag !== newTag) {
              const clients = await self.clients.matchAll({ type: 'window' });
              clients.forEach((c) => c.postMessage({ type: 'HTML_UPDATED' }));
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
