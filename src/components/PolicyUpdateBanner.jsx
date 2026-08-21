import { useState } from "react";
import { Link } from "react-router-dom";

// Bump this when the Privacy Policy materially changes — it must match the
// policy's new Effective Date. The dismissal key below is version-scoped, so
// bumping this constant is the *entire* mechanism for re-showing the notice:
// existing dismissals only silence the version they were made against.
const POLICY_VERSION = "2026-08-21";
const DISMISS_KEY = `policyUpdateDismissed_${POLICY_VERSION}`;

function PolicyUpdateBanner({ isLoggedIn }) {
  // Lazy init from storage — a synchronous setState inside an effect would
  // just re-render the first frame for the same answer.
  const [dismissed, setDismissed] = useState(() => !!localStorage.getItem(DISMISS_KEY));

  const handleDismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  // Member-facing notice only — logged-out landing-page visitors aren't the
  // audience for a policy change affecting group notifications.
  if (!isLoggedIn || dismissed) {
    return null;
  }

  return (
    <div className="policy-update-banner">
      <div className="policy-update-content">
        <div className="policy-update-text">
          <p className="policy-update-headline">We&apos;ve updated our Privacy Policy</p>
          <p className="policy-update-detail">
            Group notifications now include the pick you make. Tap to see what changed.
          </p>
        </div>
        <div className="policy-update-actions">
          <Link to="/privacy" className="policy-update-link">
            Read what changed
          </Link>
          <button className="policy-update-button" onClick={handleDismiss}>
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}

export default PolicyUpdateBanner;
