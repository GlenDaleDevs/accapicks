import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import InvitePanel from "./InvitePanel";
import * as api from "../../api/client";
import { useApp } from "../../context/AppContext";
import { showToast } from "../../utils/toast";
import { GROUPS, SETTINGS } from "../../utils/routes";

// Everything the old More tab held, minus a tab: group actions, app settings
// and the compliance copy that has to appear somewhere.
export default function AppMenu({ onClose }) {
  const { groupId } = useParams();
  const navigate = useNavigate();
  const { groups, onLogout, onRefreshGroups } = useApp();
  const [showInvite, setShowInvite] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const panelRef = useRef(null);

  const group = groups.find((g) => String(g.id) === String(groupId));

  useEffect(() => {
    const onKeyDown = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const go = (path) => { onClose(); navigate(path); };

  const handleLeave = async () => {
    if (leaving) return;
    if (!window.confirm("Are you sure you want to leave this group? Your picks will be removed.")) return;
    setLeaving(true);
    try {
      await api.leaveGroup(groupId);
      showToast("Successfully left the group", "success");
      if (onRefreshGroups) onRefreshGroups();
      onClose();
      navigate("/");
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to leave group", "error");
      setLeaving(false);
    }
  };

  const handleLogout = () => {
    onClose();
    onLogout();
    navigate("/");
  };

  return (
    <div className="app-menu-backdrop" onClick={onClose}>
      <div
        className="app-menu"
        role="menu"
        aria-label="Menu"
        ref={panelRef}
        onClick={(e) => e.stopPropagation()}
      >
        {group && (
          <>
            <p className="app-menu-heading">{group.name}</p>
            <button
              type="button"
              role="menuitem"
              className="app-menu-item"
              aria-expanded={showInvite}
              onClick={() => setShowInvite((open) => !open)}
            >
              Invite friends
            </button>
            {showInvite && <InvitePanel groupId={groupId} groupName={group.name} />}
            <button
              type="button"
              role="menuitem"
              className="app-menu-item app-menu-item-danger"
              onClick={handleLeave}
              disabled={leaving}
            >
              {leaving ? "Leaving…" : "Leave this group"}
            </button>
            <hr className="app-menu-rule" />
          </>
        )}

        <button type="button" role="menuitem" className="app-menu-item" onClick={() => go(GROUPS)}>
          Your groups
        </button>
        <button type="button" role="menuitem" className="app-menu-item" onClick={() => go(SETTINGS)}>
          Settings
        </button>
        <button
          type="button"
          role="menuitem"
          className="app-menu-item app-menu-item-danger"
          onClick={handleLogout}
        >
          Log out
        </button>

        <footer className="app-menu-footer">
          18+ only | Please gamble responsibly |{" "}
          <a href="https://www.begambleaware.org/" target="_blank" rel="noopener noreferrer">
            BeGambleAware.org
          </a>
          <br />
          <Link to="/terms" onClick={onClose}>Terms of Service</Link>
          {" | "}
          <Link to="/privacy" onClick={onClose}>Privacy Policy</Link>
        </footer>
      </div>
    </div>
  );
}
