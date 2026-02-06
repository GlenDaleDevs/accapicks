let toasts = [];
let listeners = [];
let nextId = 0;

export function showToast(message, type = "info") {
  const toast = { id: nextId++, message, type };
  toasts = [...toasts, toast];
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
