import { useState } from "react";
import AppMenu from "./AppMenu";
import GroupSwitcher from "./GroupSwitcher";

export default function GlobalHeader() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="global-header">
      <div className="global-header-inner">
        <GroupSwitcher />
        <button
          type="button"
          className="global-header-profile"
          onClick={() => setMenuOpen(true)}
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          aria-label="Menu"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M4 7h16" />
            <path d="M4 12h16" />
            <path d="M4 17h16" />
          </svg>
        </button>
      </div>

      {menuOpen && <AppMenu onClose={() => setMenuOpen(false)} />}
    </header>
  );
}
