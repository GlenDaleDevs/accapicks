import { useState, useEffect } from "react";
import "./Landing.css"; // owns the .install-prompt styles

function detectPlatform() {
  const ua = navigator.userAgent || "";
  const isIOS =
    /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  if (isIOS) return "ios";
  // Samsung Internet builds its own Android package for installed web apps, which Play Protect blocks on
  // Android 14+ ("built for an older version of Android"). Chrome installs the same app cleanly.
  if (/Android/.test(ua) && /SamsungBrowser/.test(ua)) return "android-samsung";
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
  "android-samsung": [
    "Tap “Open in Chrome” below.",
    "In Chrome, tap “Add to Home Screen” — AccaPicks will appear on your home screen.",
  ],
  desktop: [
    "Look for the install icon in your browser's address bar.",
    "Or open the browser menu and choose “Install AccaPicks”.",
  ],
};

const DISMISS_KEY = "installPromptDismissed";

// Opens this page in Chrome on Android; without Chrome, Android opens its Play Store page instead.
const CHROME_STORE = encodeURIComponent("https://play.google.com/store/apps/details?id=com.android.chrome");
function chromeLink() {
  const { host, pathname, search } = window.location;
  return `intent://${host}${pathname}${search}#Intent;scheme=https;package=com.android.chrome;S.browser_fallback_url=${CHROME_STORE};end`;
}

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
  const alwaysShowHelp = platform === "ios" || platform === "android-samsung";
  if (!alwaysShowHelp && !deferredPrompt) return null;
  if (dismissible && dismissed) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  const handleClick = async () => {
    // Never start Samsung Internet's own install: Play Protect blocks what it builds
    if (!deferredPrompt || platform === "android-samsung") {
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
            {platform === "android-samsung" && (
              <p className="install-help-note">
                Samsung Internet's install gets blocked by Google Play Protect on newer Android, so
                install from Chrome instead.
              </p>
            )}
            <ol>
              {INSTRUCTIONS[platform].map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <div className="install-help-actions">
              {platform === "android-samsung" && (
                <a className="btn btn-primary" href={chromeLink()}>
                  Open in Chrome
                </a>
              )}
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setShowHelp(false)}
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
