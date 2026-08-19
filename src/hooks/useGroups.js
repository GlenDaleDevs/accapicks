import { useCallback, useEffect, useState } from "react";
import * as api from "../api/client";
import { showToast } from "../utils/toast";

// The signed-in user's groups, plus create/join. Also consumes a pending
// invite (?invite=CODE saved to localStorage before login) once logged in.
export default function useGroups(isLoggedIn) {
  const [groups, setGroups] = useState([]);
  const [loadingGroups, setLoadingGroups] = useState(false);

  const loadGroups = useCallback(async () => {
    setLoadingGroups(true);
    try {
      const data = await api.getGroups();
      setGroups(data);
    } catch (err) {
      console.error("Error loading groups:", err);
    } finally {
      setLoadingGroups(false);
    }
  }, []);

  const handleCreateGroup = useCallback(async (name, description) => {
    try {
      await api.createGroup(name, description);
      loadGroups();
    } catch (err) {
      throw new Error(err.response?.data?.detail || "Failed to create group");
    }
  }, [loadGroups]);

  const handleJoinGroup = useCallback(async (inviteCode) => {
    try {
      await api.joinGroup(inviteCode);
      loadGroups();
      showToast("Successfully joined group!", "success");
    } catch (err) {
      throw new Error(err.response?.data?.detail || "Failed to join group");
    }
  }, [loadGroups]);

  useEffect(() => {
    if (isLoggedIn) loadGroups();
    else setGroups([]); // covers cross-tab logout too
  }, [isLoggedIn, loadGroups]);

  useEffect(() => {
    if (!isLoggedIn) return;
    const pendingInviteRaw = localStorage.getItem("pendingInvite");
    if (!pendingInviteRaw) return;
    let inviteCode;
    try {
      const parsed = JSON.parse(pendingInviteRaw);
      // Expire after 24 hours
      if (Date.now() - parsed.savedAt < 24 * 60 * 60 * 1000) {
        inviteCode = parsed.code;
      }
    } catch {
      // Legacy format (plain string) — use as-is
      inviteCode = pendingInviteRaw;
    }
    if (inviteCode) {
      handleJoinGroup(inviteCode)
        .catch((err) => {
          console.error("Auto-join failed:", err);
          showToast(err.message || "Failed to join group from invite link", "error");
        })
        .finally(() => {
          localStorage.removeItem("pendingInvite");
          window.history.replaceState({}, "", window.location.pathname);
        });
    } else {
      localStorage.removeItem("pendingInvite");
    }
  }, [isLoggedIn, handleJoinGroup]);

  return { groups, loadingGroups, loadGroups, handleCreateGroup, handleJoinGroup };
}
