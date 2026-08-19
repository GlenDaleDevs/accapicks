import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import InvitePanel from "./InvitePanel";
import * as api from "../../api/client";
import { useApp } from "../../context/AppContext";
import { showToast } from "../../utils/toast";
import { GROUPS, SETTINGS } from "../../utils/routes";

// Everything the old More tab held, minus a tab: group actions and app
// settings. The compliance copy lives in the page footer, not in here.
export default function AppMenu({ onClose, onOpenSettings }) {
  const { groupId } = useParams();
  const navigate = useNavigate();
  const { user, groups, onLogout, onRefreshGroups } = useApp();
  const [showInvite, setShowInvite] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const panelRef = useRef(null);

  const group = groups.find((g) => String(g.id) === String(groupId));

  // Group settings are admin-only, so the item only appears once membership
  // confirms the role. The menu opens rarely; one small fetch is fine.
  useEffect(() => {
    if (!group || !user) return;
    let cancelled = false;
    api.getGroupMembers(groupId)
      .then((members) => {
        if (cancelled) return;
        setIsAdmin(members.some((m) => m.user_id === user.id && m.role === "admin"));
      })
      .catch(() => { /* no role, no settings item */ });
    return () => { cancelled = true; };
  }, [group, groupId, user]);

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
            {isAdmin && (
              <button
                type="button"
                role="menuitem"
                className="app-menu-item"
                onClick={() => { onClose(); onOpenSettings(); }}
              >
                Group settings
              </button>
            )}
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
      </div>
    </div>
  );
}
