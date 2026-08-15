import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import * as api from "../api/client";
import { showToast } from "../utils/toast";
import { useApp } from "../context/AppContext";

export default function GroupSettings() {
  const { groupId } = useParams();
  const navigate = useNavigate();
  const { groups, onRefreshGroups } = useApp();

  const [group, setGroup] = useState(null);
  const [showInvite, setShowInvite] = useState(false);
  const [copied, setCopied] = useState(false);
  const [leaving, setLeaving] = useState(false);

  const known = groups.find((g) => String(g.id) === String(groupId));

  useEffect(() => {
    let cancelled = false;
    api.getGroup(groupId)
      .then((data) => { if (!cancelled) setGroup(data); })
      .catch(() => { /* the list still gives us a name */ });
    return () => { cancelled = true; };
  }, [groupId]);

  const name = group?.name || known?.name || "This group";
  const inviteCode = group?.invite_code;
  const inviteLink = inviteCode ? `${window.location.origin}?invite=${inviteCode}` : "";
  const inviteMessage = `Join ${name} on AccaPicks: ${inviteLink}`;

  const copyInviteLink = async () => {
    try {
      await navigator.clipboard.writeText(inviteLink);
      setCopied(true);
    } catch {
      try {
        const textArea = document.createElement("textarea");
        textArea.value = inviteLink;
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
        setCopied(true);
      } catch {
        showToast("Couldn't copy. Invite link: " + inviteLink, "warning");
        return;
      }
    }
    setTimeout(() => setCopied(false), 2000);
  };

  const shareNative = async () => {
    try {
      await navigator.share({ title: `Join ${name} on AccaPicks`, text: inviteMessage, url: inviteLink });
    } catch {
      copyInviteLink();
    }
  };

  const handleLeave = async () => {
    if (leaving) return;
    if (!window.confirm("Are you sure you want to leave this group? Your picks will be removed.")) return;
    setLeaving(true);
    try {
      await api.leaveGroup(groupId);
      showToast("Successfully left the group", "success");
      if (onRefreshGroups) onRefreshGroups();
      navigate("/");
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to leave group", "error");
      setLeaving(false);
    }
  };

  return (
    <div className="group-settings">
      <h3 className="more-section-title">{name}</h3>

      {!showInvite ? (
        <button className="btn btn-secondary" onClick={() => setShowInvite(true)}>
          Invite Friends
        </button>
      ) : (
        <div className="invite-panel">
          <button className="invite-panel-close" onClick={() => setShowInvite(false)} aria-label="Close invite panel">
            &times;
          </button>
          <div className="invite-code-row">
            <code className="invite-code">{inviteCode || "…"}</code>
          </div>
          <div className="invite-share-buttons">
            <button className="btn btn-share" onClick={copyInviteLink} disabled={!inviteLink}>
              {copied ? "Copied!" : "Copy Link"}
            </button>
            <button
              className="btn btn-share"
              onClick={() => window.open(`https://wa.me/?text=${encodeURIComponent(inviteMessage)}`, "_blank")}
              disabled={!inviteLink}
            >
              WhatsApp
            </button>
            <button
              className="btn btn-share"
              onClick={() => window.open(`fb-messenger://share/?link=${encodeURIComponent(inviteLink)}`, "_blank")}
              disabled={!inviteLink}
            >
              Messenger
            </button>
            {typeof navigator !== "undefined" && navigator.share && (
              <button className="btn btn-share btn-native-share" onClick={shareNative} disabled={!inviteLink}>
                Share...
              </button>
            )}
          </div>
        </div>
      )}

      <button className="group-leave-link" onClick={handleLeave} disabled={leaving}>
        {leaving ? "Leaving…" : "Leave this group"}
      </button>
    </div>
  );
}
