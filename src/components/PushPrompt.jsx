import { useEffect, useState } from "react";
import {
  isPushSupported,
  getPushPermission,
  isSubscribedToPush,
  subscribeToPush,
} from "../utils/pushNotifications";
import { showToast } from "../utils/toast";
import Modal from "./ui/Modal";

const DISMISS_KEY = "pushPromptDismissed";   // hard no — never nudge again
const WELCOME_KEY = "pushWelcomeSeen";       // the first-open modal has been shown once

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

// A one-tap nudge to turn on push. The browser forbids enabling it silently —
// permission must come from a real tap — so the best we can do is make that tap
// unmissable. On the first open of the INSTALLED app it's a centered modal;
// after that (or in a plain browser) it's a quiet inline card. Shown only when
// it's actually actionable: supported, permission undecided, not already on,
// and on iOS only inside the installed app (Safari can't deliver push).
export default function PushPrompt() {
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [dismissed, setDismissed] = useState(() => !!localStorage.getItem(DISMISS_KEY));
  // The prominent first-open modal: only in the installed app, only once.
  const [asModal, setAsModal] = useState(
    () => isStandalone() && !localStorage.getItem(WELCOME_KEY)
  );

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

  // Mark the first-open modal seen as soon as it actually shows, so a reload
  // doesn't pop it a second time.
  useEffect(() => {
    if (ready && asModal) localStorage.setItem(WELCOME_KEY, "1");
  }, [ready, asModal]);

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

  // Hard dismiss from the inline card's × — never nudge again on this device.
  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  // "Maybe later" on the modal: don't nag with the modal again, but fall back
  // to the quiet inline card on the next visit.
  const laterFromModal = () => setAsModal(false);

  const cta = (
    <button type="button" className="btn btn-primary push-prompt-btn" onClick={enable} disabled={busy}>
      {busy ? "Turning on…" : "Enable notifications"}
    </button>
  );

  if (asModal) {
    return (
      <Modal open title="Stay in the loop" onClose={laterFromModal}>
        <div className="push-modal">
          <p className="push-modal-text">
            Turn on notifications and AccaPicks will nudge you when it's your turn
            to pick, and ping you with results as they land.
          </p>
          <div className="push-modal-actions">
            {cta}
            <button type="button" className="btn btn-ghost" onClick={laterFromModal} disabled={busy}>
              Maybe later
            </button>
          </div>
        </div>
      </Modal>
    );
  }

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
      {cta}
    </div>
  );
}
