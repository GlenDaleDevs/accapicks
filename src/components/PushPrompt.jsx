import { useEffect, useState } from "react";
import {
  isPushSupported,
  getPushPermission,
  isSubscribedToPush,
  subscribeToPush,
} from "../utils/pushNotifications";
import { showToast } from "../utils/toast";

const DISMISS_KEY = "pushPromptDismissed";

function isIOS() {
  const ua = navigator.userAgent || "";
  return /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
}

function isStandalone() {
  return (
    window.matchMedia?.("(display-mode: standalone)").matches ||
    window.navigator.standalone === true
  );
}

// A one-tap nudge to turn on push, shown only when it's actually actionable:
// push supported, not already on, permission not blocked, and — on iOS —
// only inside the installed app, since Safari can't deliver push at all.
export default function PushPrompt() {
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [dismissed, setDismissed] = useState(() => !!localStorage.getItem(DISMISS_KEY));

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!isPushSupported()) return;
      if (getPushPermission() !== "default") return; // granted or blocked → nothing to nudge
      if (isIOS() && !isStandalone()) return; // Safari can't do push; wait for the installed app
      const already = await isSubscribedToPush();
      if (!cancelled && !already) setReady(true);
    })();
    return () => { cancelled = true; };
  }, []);

  if (!ready || dismissed) return null;

  const enable = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await subscribeToPush();
      showToast("Notifications on — you'll get pick reminders and results", "success");
      setReady(false);
    } catch (err) {
      if (err.message?.includes("denied")) {
        showToast("Notifications blocked in your browser settings", "warning");
        setReady(false); // permission is now 'denied' — stop nudging
      } else {
        showToast("Couldn't turn on notifications", "error");
      }
    } finally {
      setBusy(false);
    }
  };

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  return (
    <div className="push-prompt">
      <button
        type="button"
        className="push-prompt-dismiss"
        aria-label="Dismiss"
        onClick={dismiss}
      >
        ×
      </button>
      <div className="push-prompt-body">
        <span className="push-prompt-title">Turn on notifications</span>
        <span className="push-prompt-sub">
          Get a nudge when it's your turn to pick, and results as they land.
        </span>
      </div>
      <button type="button" className="btn btn-primary push-prompt-btn" onClick={enable} disabled={busy}>
        {busy ? "Turning on…" : "Enable"}
      </button>
    </div>
  );
}
