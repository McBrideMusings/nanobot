import { useCallback, useEffect, useRef, useState } from 'react';

interface UsePushOptions {
  serverUrl: string;
}

/**
 * Manages web push notification subscription.
 *
 * Communicates with the backend via WebSocket to get the VAPID public key
 * and register/unregister push subscriptions.
 */
export function usePushNotifications({ serverUrl }: UsePushOptions) {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const registrationRef = useRef<ServiceWorkerRegistration | null>(null);

  // Derive the WS origin for the push subscription backend
  const getWsUrl = useCallback(() => serverUrl, [serverUrl]);

  // Check support and existing subscription on mount
  useEffect(() => {
    const supported = 'serviceWorker' in navigator && 'PushManager' in window;
    setIsSupported(supported);
    if (!supported) return;

    setPermission(Notification.permission);

    navigator.serviceWorker.register('/sw.js').then(reg => {
      registrationRef.current = reg;
      return reg.pushManager.getSubscription();
    }).then(sub => {
      setIsSubscribed(!!sub);
    }).catch(err => {
      console.warn('Push registration check failed:', err);
    });
  }, []);

  // Helper to send a message over a temporary WebSocket
  const sendPushMessage = useCallback((message: Record<string, unknown>): Promise<Record<string, unknown> | null> => {
    return new Promise((resolve) => {
      const ws = new WebSocket(getWsUrl());
      const timeout = setTimeout(() => { ws.close(); resolve(null); }, 5000);

      ws.onopen = () => {
        ws.send(JSON.stringify(message));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Ignore history/event messages, wait for our response
          if (data.type === 'push_vapid_key' || data.type === 'error') {
            clearTimeout(timeout);
            ws.close();
            resolve(data);
          }
        } catch { /* ignore */ }
      };

      ws.onerror = () => { clearTimeout(timeout); resolve(null); };
    });
  }, [getWsUrl]);

  const subscribe = useCallback(async () => {
    if (!isSupported || !registrationRef.current) return;

    // Request notification permission
    const perm = await Notification.requestPermission();
    setPermission(perm);
    if (perm !== 'granted') return;

    // Get VAPID public key from server
    const response = await sendPushMessage({ type: 'push_vapid' });
    if (!response || response.type !== 'push_vapid_key' || !response.key) {
      console.warn('Failed to get VAPID key from server');
      return;
    }

    // Convert URL-safe base64 to Uint8Array
    const vapidKey = response.key as string;
    const padding = '='.repeat((4 - vapidKey.length % 4) % 4);
    const base64 = (vapidKey + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawKey = Uint8Array.from(atob(base64), c => c.charCodeAt(0));

    // Subscribe to push
    const subscription = await registrationRef.current.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: rawKey,
    });

    // Send subscription to server (use the main WS for this since it's fire-and-forget)
    const subJson = subscription.toJSON();
    const ws = new WebSocket(getWsUrl());
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'push_subscribe', subscription: subJson }));
      setTimeout(() => ws.close(), 500);
    };

    setIsSubscribed(true);
  }, [isSupported, sendPushMessage, getWsUrl]);

  const unsubscribe = useCallback(async () => {
    if (!registrationRef.current) return;

    const subscription = await registrationRef.current.pushManager.getSubscription();
    if (subscription) {
      const endpoint = subscription.endpoint;
      await subscription.unsubscribe();

      // Notify server
      const ws = new WebSocket(getWsUrl());
      ws.onopen = () => {
        ws.send(JSON.stringify({ type: 'push_unsubscribe', endpoint }));
        setTimeout(() => ws.close(), 500);
      };
    }

    setIsSubscribed(false);
  }, [getWsUrl]);

  return { isSupported, isSubscribed, permission, subscribe, unsubscribe };
}
