import { useState, useEffect } from "react";
import "./Landing.css"; // owns the .install-prompt styles

function detectPlatform() {
  const ua = navigator.userAgent || "";
  const isIOS =
    /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  if (isIOS) return "ios";
  if (/Android/.test(ua)) return "android";
  return "desktop";
}

const INSTRUCTIONS = {
  ios: [
    "Tap the Share button at the bottom of Safari.",
    "Scroll down and tap “Add to Home Screen”.",
    "Tap “Add” — AccaPicks will appear on your home screen.",
  ],
  android: [
    "Tap the menu button (⋮) in your browser's toolbar.",
    "Tap “Install app” or “Add to Home screen”.",
    "Confirm — AccaPicks will appear on your home screen.",
  ],
  desktop: [
    "Look for the install icon in your browser's address bar.",
    "Or open the browser menu and choose “Install AccaPicks”.",
  ],
};

const DISMISS_KEY = "installPromptDismissed";

// Whether we're already running as the installed app.
function isStandalone() {
  return (
    window.matchMedia?.("(display-mode: standalone)").matches ||
    window.navigator.standalone === true
  );
}

export default function InstallPrompt({ dismissible = false }) {
  // index.html captures the event for us if it fired before React mounted
  const [deferredPrompt, setDeferredPrompt] = useState(() => window.__installPromptEvent);
  const [showHelp, setShowHelp] = useState(false);
  const [dismissed, setDismissed] = useState(() => !!localStorage.getItem(DISMISS_KEY));
  const platform = detectPlatform();

  useEffect(() => {
    const onBeforeInstallPrompt = (e) => {
      e.preventDefault();
      window.__installPromptEvent = e;
      setDeferredPrompt(e);
    };
    const onInstalled = () => {
      window.__installPromptEvent = null;
      setDeferredPrompt(null);
      setShowHelp(false);
    };

    window.addEventListener("beforeinstallprompt", onBeforeInstallPrompt);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onBeforeInstallPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  // Installed-state detection is only partial: inside the app it's certain;
  // on Android/desktop Chrome the install event only fires when NOT installed,
  // so no event means nothing to offer; iOS gives no signal at all from
  // Safari — which is what the dismiss cross is for.
  if (isStandalone()) return null;
  if (platform !== "ios" && !deferredPrompt) return null;
  if (dismissible && dismissed) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  const handleClick = async () => {
    if (!deferredPrompt) {
      setShowHelp(true);
      return;
    }
    // A beforeinstallprompt event can only be used once
    const promptEvent = deferredPrompt;
    window.__installPromptEvent = null;
    setDeferredPrompt(null);
    try {
      promptEvent.prompt();
      await promptEvent.userChoice;
    } catch {
      setShowHelp(true);
    }
  };

  return (
    <div className="install-prompt">
      {dismissible && (
        <button
          type="button"
          className="install-prompt-dismiss"
          aria-label="Dismiss install suggestion"
          onClick={dismiss}
        >
          ×
        </button>
      )}
      <button type="button" className="install-prompt-btn" onClick={handleClick}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 3v12" />
          <path d="m7 10 5 5 5-5" />
          <path d="M5 21h14" />
        </svg>
        Add to Home Screen
      </button>
      <p className="install-prompt-hint">Use AccaPicks like an app — no store needed.</p>

      {showHelp && (
        <div
          className="install-help-backdrop"
          role="dialog"
          aria-modal="true"
          aria-label="How to install AccaPicks"
          onClick={() => setShowHelp(false)}
        >
          <div className="install-help" onClick={(e) => e.stopPropagation()}>
            <h3>Add AccaPicks to your home screen</h3>
            <ol>
              {INSTRUCTIONS[platform].map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setShowHelp(false)}
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
