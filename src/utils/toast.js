let toasts = [];
let listeners = [];
let nextId = 0;
const MAX_TOASTS = 5;

export function showToast(message, type = "info") {
  // Deduplicate: skip if same message already visible
  if (toasts.some(t => t.message === message && t.type === type)) {
    return;
  }

  const toast = { id: nextId++, message, type };
  toasts = [...toasts, toast];

  // Cap at MAX_TOASTS — drop oldest
  if (toasts.length > MAX_TOASTS) {
    toasts = toasts.slice(-MAX_TOASTS);
  }

  listeners.forEach(fn => fn(toasts));

  // Auto-dismiss: longer for errors so users can read them
  const timeout = type === "error" ? 6000 : 4000;
  setTimeout(() => dismissToast(toast.id), timeout);

  return toast.id;
}

export function dismissToast(id) {
  toasts = toasts.filter(t => t.id !== id);
  listeners.forEach(fn => fn(toasts));
}

export function subscribe(listener) {
  listeners.push(listener);
  listener(toasts); // send current state
  return () => {
    listeners = listeners.filter(fn => fn !== listener);
  };
}
