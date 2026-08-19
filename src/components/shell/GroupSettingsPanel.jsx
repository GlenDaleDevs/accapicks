import { useEffect, useState } from "react";
import * as api from "../../api/client";
import { useApp } from "../../context/AppContext";
import { showToast } from "../../utils/toast";

// The admin surface lost with the More tab: rename the group, set or clear
// the season boundary, remove a member. Lives in a modal off the header menu.
export default function GroupSettingsPanel({ groupId, onClose }) {
  const { user, onRefreshGroups } = useApp();
  const [name, setName] = useState("");
  const [seasonStart, setSeasonStart] = useState("");
  const [members, setMembers] = useState([]);
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getGroup(groupId), api.getGroupMembers(groupId)])
      .then(([group, memberList]) => {
        if (cancelled) return;
        setName(group.name || "");
        setSeasonStart(group.season_start_date || "");
        setMembers(memberList);
      })
      .catch(() => {
        if (!cancelled) showToast("Failed to load group settings", "error");
      });
    return () => { cancelled = true; };
  }, [groupId]);

  const handleSave = async (e) => {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    try {
      // null clears the boundary; the next auto week re-derives it
      await api.updateGroup(groupId, {
        name: name.trim(),
        season_start_date: seasonStart || null,
      });
      showToast("Group settings saved", "success");
      if (onRefreshGroups) onRefreshGroups();
      onClose();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to save settings", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async (member) => {
    if (removing) return;
    if (!window.confirm(`Remove ${member.username} from the group? Their picks will be removed.`)) return;
    setRemoving(member.user_id);
    try {
      await api.removeMember(groupId, member.user_id);
      showToast(`${member.username} removed`, "success");
      setMembers((current) => current.filter((m) => m.user_id !== member.user_id));
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to remove member", "error");
    } finally {
      setRemoving(null);
    }
  };

  return (
    <form className="group-settings" onSubmit={handleSave}>
      <label className="group-settings-label" htmlFor="group-name">Group name</label>
      <input
        id="group-name"
        className="group-settings-input"
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        maxLength={100}
        required
      />

      <label className="group-settings-label" htmlFor="season-start">Season start date</label>
      <input
        id="season-start"
        className="group-settings-input"
        type="date"
        value={seasonStart}
        onChange={(e) => setSeasonStart(e.target.value)}
      />
      <p className="group-settings-hint">
        The table and stats count from this date. Leave blank and it sets
        itself from the first week that opens.
      </p>

      <p className="group-settings-label">Members</p>
      <ul className="group-settings-members">
        {members.map((m) => (
          <li key={m.user_id} className="group-settings-member">
            <span>
              {m.username}
              {m.role === "admin" && <span className="group-settings-admin">admin</span>}
            </span>
            {/* Admins can't be removed, and leaving is its own action */}
            {m.role !== "admin" && m.user_id !== user?.id && (
              <button
                type="button"
                className="group-settings-remove"
                onClick={() => handleRemove(m)}
                disabled={removing === m.user_id}
              >
                {removing === m.user_id ? "Removing…" : "Remove"}
              </button>
            )}
          </li>
        ))}
      </ul>

      <div className="group-settings-actions">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? "Saving…" : "Save"}
        </button>
        <button type="button" className="btn btn-ghost" onClick={onClose}>
          Cancel
        </button>
      </div>
    </form>
  );
}
