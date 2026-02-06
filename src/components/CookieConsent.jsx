import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem("cookieConsent");
    if (!consent) {
      setVisible(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem("cookieConsent", "accepted");
    setVisible(false);
  };

  if (!visible) {
    return null;
  }

  return (
    <div className="cookie-consent-banner">
      <div className="cookie-consent-content">
        <p className="cookie-consent-text">
          This site uses local browser storage for essential features like keeping you logged in. No tracking cookies are used.
        </p>
        <div className="cookie-consent-actions">
          <button className="cookie-consent-button" onClick={handleAccept}>
            Got it
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
