// Service worker for web push notifications

self.addEventListener('push', (event) => {
  let data;
  try {
    data = event.data ? event.data.json() : { title: 'Nanobot', body: 'New message' };
  } catch {
    data = { title: 'Nanobot', body: 'New message' };
  }
  event.waitUntil(
    self.registration.showNotification(data.title || 'Nanobot', {
      body: data.body || 'New message',
      icon: '/favicon.ico',
      badge: '/favicon.ico',
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url && 'focus' in client) {
          return client.focus();
        }
      }
      return clients.openWindow('/');
    })
  );
});
