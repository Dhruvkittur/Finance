/* =========================================================
   ANIRUDH AGENCY — Service Worker (sw.js)
   100% Offline Progressive Web App Caching Engine
   ========================================================= */

const CACHE_NAME = 'order2invoice-v1.3';

const PRECACHE_ASSETS = [
  './',
  './index.html',
  './style.css',
  './app.js',
  './xlsx.full.min.js',
  './qrcode.min.js',
  './manifest.json',
  './Shop_Items.xlsx',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-192.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon.png'
];

// Install: Pre-cache all core app assets for instant offline execution
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Use individual caching to prevent one missing file from breaking entire install
      return Promise.allSettled(
        PRECACHE_ASSETS.map((asset) =>
          cache.add(asset).catch((err) => {
            console.warn(`[ServiceWorker] Could not pre-cache: ${asset}`, err);
          })
        )
      );
    })
  );
});

// Activate: Clean up old versions of cache and claim clients immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log(`[ServiceWorker] Removing legacy cache: ${key}`);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: Cache-first strategy for local assets, network fallback
self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Network-only for live APIs (tunnel status, network IP)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // For app navigation, serve index.html if offline
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match('./index.html') || caches.match('./');
      })
    );
    return;
  }

  // Cache-first strategy for static resources
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }

      return fetch(event.request).then((networkResponse) => {
        // Cache valid same-origin responses
        if (
          networkResponse &&
          networkResponse.status === 200 &&
          (url.origin === location.origin || url.hostname.includes('sheetjs') || url.hostname.includes('googleapis') || url.hostname.includes('gstatic'))
        ) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch((err) => {
        console.warn(`[ServiceWorker] Network fetch failed for ${event.request.url}:`, err);
        // Fallback for image requests if needed
        if (event.request.destination === 'image') {
          return caches.match('./icons/icon-192.png');
        }
      });
    })
  );
});
