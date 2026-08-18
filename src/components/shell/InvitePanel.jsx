import { useEffect, useState } from "react";
import * as api from "../../api/client";
import { showToast } from "../../utils/toast";

export default function InvitePanel({ groupId, groupName }) {
  const [inviteCode, setInviteCode] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.getGroup(groupId)
      .then((g) => { if (!cancelled) setInviteCode(g.invite_code || ""); })
      .catch(() => { /* the code just stays blank and the buttons stay disabled */ });
    return () => { cancelled = true; };
  }, [groupId]);

  const link = inviteCode ? `${window.location.origin}?invite=${inviteCode}` : "";
  const message = `Join ${groupName} on AccaPicks: ${link}`;

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(link);
    } catch {
      // clipboard API needs a secure context and a user gesture; the textarea
      // fallback works where it doesn't
      try {
        const field = document.createElement("textarea");
        field.value = link;
        field.style.position = "fixed";
        field.style.opacity = "0";
        document.body.appendChild(field);
        field.select();
        document.execCommand("copy");
        document.body.removeChild(field);
      } catch {
        showToast(`Couldn't copy. Invite link: ${link}`, "warning");
        return;
      }
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const shareNative = async () => {
    try {
      await navigator.share({ title: `Join ${groupName} on AccaPicks`, text: message, url: link });
    } catch {
      copyLink();
    }
  };

  return (
    <div className="invite-panel">
      <div className="invite-code-row">
        <code className="invite-code">{inviteCode || "…"}</code>
      </div>
      <div className="invite-share-buttons">
        <button className="btn btn-share" onClick={copyLink} disabled={!link}>
          {copied ? "Copied!" : "Copy Link"}
        </button>
        <button
          className="btn btn-share"
          onClick={() => window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, "_blank")}
          disabled={!link}
        >
          WhatsApp
        </button>
        <button
          className="btn btn-share"
          onClick={() => window.open(`fb-messenger://share/?link=${encodeURIComponent(link)}`, "_blank")}
          disabled={!link}
        >
          Messenger
        </button>
        {typeof navigator !== "undefined" && navigator.share && (
          <button className="btn btn-share btn-native-share" onClick={shareNative} disabled={!link}>
            Share...
          </button>
        )}
      </div>
    </div>
  );
}
