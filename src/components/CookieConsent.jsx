import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

const GA_ID = "G-K35NV43XK0";

function loadGoogleAnalytics() {
  if (document.querySelector(`script[src*="gtag"]`)) return;
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
  document.head.appendChild(script);
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag("js", new Date());
  gtag("config", GA_ID);
}

function CookieConsent() {
  // Lazy init from storage — a synchronous setState inside the effect would
  // just re-render the first frame for the same answer.
  const [visible, setVisible] = useState(() => !localStorage.getItem("cookieConsent"));

  useEffect(() => {
    if (localStorage.getItem("cookieConsent") === "accepted") {
      loadGoogleAnalytics();
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem("cookieConsent", "accepted");
    loadGoogleAnalytics();
    setVisible(false);
  };

  const handleDecline = () => {
    localStorage.setItem("cookieConsent", "declined");
    setVisible(false);
  };

  if (!visible) {
    return null;
  }

  return (
    <div className="cookie-consent-banner">
      <div className="cookie-consent-content">
        <p className="cookie-consent-text">
          We use cookies for essential features like keeping you logged in, and analytics to help improve the site.
        </p>
        <div className="cookie-consent-actions">
          <button className="cookie-consent-button" onClick={handleAccept}>
            Accept
          </button>
          <button className="cookie-consent-button cookie-consent-decline" onClick={handleDecline}>
            Decline
          </button>
          <Link to="/privacy" className="cookie-consent-link">
            Privacy Policy
          </Link>
        </div>
      </div>
    </div>
  );
}

export default CookieConsent;
