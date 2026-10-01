import { useCallback, useEffect, useState } from "react";
import * as api from "../../api/client";
import { showToast } from "../../utils/toast";

const countLabel = (n) => {
  if (n === null) return "";
  if (n === 0) return "No displays connected";
  return `${n} ${n === 1 ? "display" : "displays"} connected`;
};

// The device token is held in component state only: never context, never
// storage. It is shown once by the backend and can't be fetched again.
export default function DevicesSection({ groupId }) {
  const [count, setCount] = useState(null);
  const [token, setToken] = useState("");
  const [generating, setGenerating] = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [copyNote, setCopyNote] = useState("");

  const refreshCount = useCallback(async () => {
    try {
      const data = await api.getDeviceCount(groupId);
      setCount(data.connected);
    } catch {
      showToast("Failed to load connected displays", "error");
    }
  }, [groupId]);

  useEffect(() => {
    let cancelled = false;
    api.getDeviceCount(groupId)
      .then((data) => { if (!cancelled) setCount(data.connected); })
      .catch(() => {
        if (!cancelled) showToast("Failed to load connected displays", "error");
      });
    return () => { cancelled = true; };
  }, [groupId]);

  const handleGenerate = async () => {
    if (generating) return;
    if (token && !window.confirm("This replaces the token shown below, and it won't be shown again. Generate a new one?")) return;
    setGenerating(true);
    try {
      const data = await api.createDeviceToken(groupId);
      setToken(data.token);
      setCopyNote("");
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to generate device token", "error");
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(token);
      setCopyNote("Copied");
    } catch {
      // Clipboard API is unavailable or blocked on some iOS versions
      setCopyNote("Long-press to copy");
    }
  };

  const handleRevoke = async () => {
    if (revoking) return;
    if (!window.confirm("Revoke your device token? Displays using it will stop working.")) return;
    setRevoking(true);
    try {
      await api.revokeDeviceToken(groupId);
      setToken("");
      setCopyNote("");
      showToast("Device token revoked", "success");
      await refreshCount();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to revoke device token", "error");
    } finally {
      setRevoking(false);
    }
  };

  return (
    <>
      <p className="group-settings-label">Display device</p>
      <p className="group-settings-hint">
        Connect a DIY status display (e.g. a Pico W) to this group's live acca state.
      </p>
      {count !== null && <p className="group-settings-device-count">{countLabel(count)}</p>}

      <div className="group-settings-actions">
        <button
          type="button"
          className="btn btn-ghost"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Generating…" : "Generate device token"}
        </button>
      </div>
      <p className="group-settings-hint">Generating a new token replaces your previous one.</p>

      {token && (
        <div className="group-settings-token">
          <div className="group-settings-token-row">
            <input
              className="group-settings-input group-settings-token-input"
              type="text"
              value={token}
              readOnly
              aria-label="Device token"
              onFocus={(e) => e.target.select()}
            />
            <button type="button" className="btn btn-ghost" onClick={handleCopy}>
              Copy
            </button>
          </div>
          {copyNote && <p className="group-settings-hint">{copyNote}</p>}
          <p className="group-settings-token-warning">
            Shown once — copy it now. You won't see it again.
          </p>
        </div>
      )}

      <button
        type="button"
        className="group-settings-link"
        onClick={handleRevoke}
        disabled={revoking}
      >
        {revoking ? "Revoking…" : "Revoke my device token"}
      </button>
    </>
  );
}
