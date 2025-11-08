// RAAS Service Worker for Push Notifications
const CACHE_NAME = 'raas-v1';

// Install event
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installed');
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activated');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('Service Worker: Clearing old cache');
            return caches.delete(cache);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Check if there's already a window/tab open
      for (let client of clientList) {
        if (client.url.includes(self.registration.scope) && 'focus' in client) {
          return client.focus();
        }
      }
      // If no window is open, open a new one
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    })
  );
});

// Handle push events (for future server-sent notifications)
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'You have a task due soon!',
    icon: '/static/icon-192.png',
    badge: '/static/icon-72.png',
    vibrate: [200, 100, 200],
    tag: 'raas-reminder',
    requireInteraction: true
  };

  event.waitUntil(
    self.registration.showNotification('RAAS Reminder', options)
  );
});
