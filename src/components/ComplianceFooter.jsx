import { Link } from "react-router-dom";

// The 18+ / BeGambleAware notice and the legal links. Rendered on every screen
// a signed-in user can reach, so it lives in one place rather than four.
export default function ComplianceFooter() {
  return (
    <footer className="responsible-gambling-footer">
      18+ only | Please gamble responsibly |{" "}
      <a href="https://www.begambleaware.org/" target="_blank" rel="noopener noreferrer">
        BeGambleAware.org
      </a>
      <br />
      <Link to="/terms">Terms of Service</Link> | <Link to="/privacy">Privacy Policy</Link>
    </footer>
  );
}
