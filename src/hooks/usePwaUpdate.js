import { useEffect } from "react";
import { useRegisterSW } from "virtual:pwa-register/react";

// Activate a waiting service worker and reload once it takes control. The
// sessionStorage flag breaks the reload loop a broken update would cause.
export default function usePwaUpdate() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW();

  useEffect(() => {
    if (!needRefresh) {
      sessionStorage.removeItem("pwa-reloading");
      return;
    }

    // Already reloaded for this update — stop the loop
    if (sessionStorage.getItem("pwa-reloading")) {
      sessionStorage.removeItem("pwa-reloading");
      setNeedRefresh(false);
      return;
    }

    // Activate new service worker and reload when it takes control
    sessionStorage.setItem("pwa-reloading", "1");
    updateServiceWorker(true);
    navigator.serviceWorker?.addEventListener("controllerchange", () => {
      window.location.reload();
    }, { once: true });
  }, [needRefresh, setNeedRefresh, updateServiceWorker]);
}
