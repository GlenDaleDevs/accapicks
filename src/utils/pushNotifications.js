import { getVapidKey, subscribePush, unsubscribePush } from "../api/client";

/**
 * Check if push notifications are supported in this browser.
 */
export function isPushSupported() {
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

/**
 * Get the current notification permission state.
 * Returns 'granted', 'denied', or 'default'.
 */
export function getPushPermission() {
  if (!("Notification" in window)) return "unsupported";
  return Notification.permission;
}

/**
 * Subscribe the current browser to push notifications.
 * Requests permission, creates a PushSubscription, and sends it to the backend.
 */
export async function subscribeToPush() {
  if (!isPushSupported()) {
    throw new Error("Push notifications are not supported in this browser");
  }

  // Request permission
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    throw new Error("Notification permission denied");
  }

  // Get VAPID key from backend
  const { vapid_key } = await getVapidKey();

  // Convert base64url VAPID key to Uint8Array
  const applicationServerKey = urlBase64ToUint8Array(vapid_key);

  // Get the service worker registration
  const registration = await navigator.serviceWorker.ready;

  // Subscribe to push
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey,
  });

  // Send subscription to backend
  await subscribePush(subscription.toJSON());

  return subscription;
}

/**
 * Unsubscribe from push notifications.
 * Removes the subscription from the browser and the backend.
 */
export async function unsubscribeFromPush() {
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();

  if (subscription) {
    const endpoint = subscription.endpoint;
    await subscription.unsubscribe();
    try {
      await unsubscribePush(endpoint);
    } catch {
      // Backend cleanup is best-effort
    }
  }
}

/**
 * Check if user is currently subscribed to push.
 */
export async function isSubscribedToPush() {
  if (!isPushSupported()) return false;
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return !!subscription;
  } catch {
    return false;
  }
}

// Helper: convert base64url string to Uint8Array (for applicationServerKey)
function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}
