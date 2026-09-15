// IM VOCA Service Worker
// 전략: HTML은 항상 네트워크 우선 (최신 유지), 정적 자원은 캐시 우선 (속도)

const CACHE_VERSION = 'imvoca-v8';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

// 미리 캐시할 정적 자원 (앱 첫 실행 시 빠르게)
const PRECACHE_URLS = [
  '/',
  '/manifest.json',
  '/2.png',
  '/og-image.png'
];

// 설치 — 정적 자원 미리 캐시 후 바로 활성화.
// 예전엔 '새 버전이 있어요' 토스트를 눌러야 SKIP_WAITING 으로 넘어갔는데, 토스트를 없애서
// 대기 상태로 남으면 업데이트가 영영 안 걸린다. 그래서 설치 즉시 새 SW 로 교체한다.
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS).catch(() => {}))
      .then(() => self.skipWaiting())
  );
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

// ── 웹 푸시: 복습 알림 ─────────────────────────────────────────────
// 안드로이드는 navigator.setAppBadge() 를 지원하지 않는다. 대신 '읽지 않은 알림'이
// 있으면 OS 가 런처 아이콘에 배지(숫자 또는 점)를 붙여준다 — 그래서 배지를 띄우려면
// 알림을 보내야 한다. iOS 16.4+/PC 는 setAppBadge 로 숫자까지 직접 찍는다.
self.addEventListener('push', (event) => {
  let d = {};
  try { d = event.data ? event.data.json() : {}; } catch (e) {}
  const title = d.title || '🔁 복습할 단어가 있어요';
  const opts = {
    body: d.body || '',
    icon: '/icon-192.png?v=3',
    badge: '/icon-192.png?v=3',
    tag: d.tag || 'imvoca-review',   // 같은 tag 는 덮어쓴다 → 알림이 쌓이지 않음
    renotify: true,
    data: { url: d.url || '/' },
  };
  event.waitUntil((async () => {
    await self.registration.showNotification(title, opts);
    // 숫자 배지를 지원하는 플랫폼에서는 개수까지 찍는다 (안드로이드는 무시됨)
    try { if (self.navigator && self.navigator.setAppBadge && d.badge > 0) await self.navigator.setAppBadge(d.badge); } catch (e) {}
  })());
});

// 알림을 누르면 이미 열린 탭이 있으면 그리로, 없으면 새로 연다
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil((async () => {
    try { if (self.navigator && self.navigator.clearAppBadge) await self.navigator.clearAppBadge(); } catch (e) {}
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const c of all) {
      if (c.url.indexOf(self.location.origin) === 0 && 'focus' in c) {
        try { c.postMessage({ type: 'OPEN_REVIEW' }); } catch (e) {}
        return c.focus();
      }
    }
    if (self.clients.openWindow) return self.clients.openWindow(url);
  })());
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
  // → 앱 재시작이 네트워크를 기다리지 않고 바로 뜸. 새로 받은 HTML 은 조용히 캐시에만
  //   넣어두고, 사용자는 다음 실행 때 새 버전을 보게 된다 (알림 없음).
  if (request.mode === 'navigate' || request.destination === 'document') {
    event.respondWith((async () => {
      // ⚠️ 반드시 RUNTIME 캐시를 먼저 본다. caches.match() 는 생성 순서대로 찾기 때문에
      //    설치 때 넣어둔 STATIC 의 '/' 를 항상 먼저 돌려줘 갱신된 사본이 무시된다.
      const runtime = await caches.open(RUNTIME_CACHE);
      const cached = (await runtime.match(request)) || (await runtime.match('/'))
                  || (await caches.match(request)) || (await caches.match('/'));
      const network = fetch(request).then(async (response) => {
        if (response.ok) await runtime.put(request, response.clone());
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
