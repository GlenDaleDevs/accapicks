import { useState } from "react";
import { useParams } from "react-router-dom";
import AppMenu from "./AppMenu";
import GroupSettingsPanel from "./GroupSettingsPanel";
import GroupSwitcher from "./GroupSwitcher";
import Modal from "../ui/Modal";

export default function GlobalHeader() {
  const { groupId } = useParams();
  const [menuOpen, setMenuOpen] = useState(false);
  // Owned here, not by the menu: the menu unmounts when it closes, and the
  // settings dialog has to survive that.
  const [settingsOpen, setSettingsOpen] = useState(false);

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

      {menuOpen && (
        <AppMenu
          onClose={() => setMenuOpen(false)}
          onOpenSettings={() => setSettingsOpen(true)}
        />
      )}

      <Modal open={settingsOpen} title="Group settings" onClose={() => setSettingsOpen(false)}>
        <GroupSettingsPanel groupId={groupId} onClose={() => setSettingsOpen(false)} />
      </Modal>
    </header>
  );
}
