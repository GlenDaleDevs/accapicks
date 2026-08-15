import { useNavigate } from "react-router-dom";
import GroupSwitcher from "./GroupSwitcher";
import { SETTINGS } from "../../utils/routes";

export default function GlobalHeader() {
  const navigate = useNavigate();

  return (
    <header className="global-header">
      <div className="global-header-inner">
        <GroupSwitcher />
        <button
          type="button"
          className="global-header-profile"
          onClick={() => navigate(SETTINGS)}
          aria-label="Settings"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="12" cy="8" r="3.6" />
            <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
          </svg>
        </button>
      </div>
    </header>
  );
}
