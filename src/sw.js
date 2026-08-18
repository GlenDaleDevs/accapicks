import { precacheAndRoute } from 'workbox-precaching'
import { clientsClaim } from 'workbox-core'

// v2.1 — bust cache after splash screen removal
// Precache app shell (injected by vite-plugin-pwa at build time)
precacheAndRoute(self.__WB_MANIFEST)

// injectManifest builds our own worker, so the skip-waiting handshake that
// generateSW would add has to be wired up here. Without it the new worker sits
// in "waiting" forever and open tabs keep serving the old precached shell.
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting()
})

// Take over open tabs as soon as the new worker activates
clientsClaim()

// Push notification handler
self.addEventListener('push', (event) => {
  if (!event.data) return

  let payload
  try {
    payload = event.data.json()
  } catch {
    payload = { title: 'AccaPicks', body: event.data.text() }
  }

  const options = {
    body: payload.body || '',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.png',
    tag: payload.tag || 'accapicks-default',
    data: { url: payload.url || '/' },
    renotify: !!payload.tag,
  }

  event.waitUntil(self.registration.showNotification(payload.title || 'AccaPicks', options))
})

// Notification click handler — navigate to the relevant page
self.addEventListener('notificationclick', (event) => {
  event.notification.close()

  // Only allow relative URLs (prevent XSS via javascript: or external/protocol-relative URLs)
  const rawUrl = event.notification.data?.url || '/'
  const url = (rawUrl.startsWith('/') && !rawUrl.startsWith('//')) ? rawUrl : '/'

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      // Focus existing window if one is open
      for (const client of clients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(url)
          return client.focus()
        }
      }
      // Otherwise open a new window
      return self.clients.openWindow(url)
    })
  )
})
