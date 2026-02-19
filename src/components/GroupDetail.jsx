import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { LEAGUE_NAME_MAP } from "../utils/constants";
import { formatCountdown } from "../utils/formatters";
import * as api from "../api/client";
import { showToast } from "../utils/toast";
import { isPushSupported, getPushPermission, subscribeToPush } from "../utils/pushNotifications";
import AccaWizard from "./AccaWizard";
import Leaderboard from "./Leaderboard";
import Skeleton from "./Skeleton";

export default function GroupDetail({ user, onRefreshGroups }) {
  const { groupId } = useParams();
  const navigate = useNavigate();
  const [group, setGroup] = useState(null);
  const [accas, setAccas] = useState([]);
  const [showAccaWizard, setShowAccaWizard] = useState(false);
  const [showSettled, setShowSettled] = useState(false);
  const [showActive, setShowActive] = useState(false);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loadingLeaderboard, setLoadingLeaderboard] = useState(false);
  const [accaStats, setAccaStats] = useState(null);
  const [loadingGroup, setLoadingGroup] = useState(true);
  const [copiedInvite, setCopiedInvite] = useState(false);
  const [showInvite, setShowInvite] = useState(false);
  const [error, setError] = useState("");
  const [accaCountdowns, setAccaCountdowns] = useState({});
  const [members, setMembers] = useState([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [showPushPrompt, setShowPushPrompt] = useState(false);

  useEffect(() => {
    if (groupId) {
      loadGroupData();
    }
  }, [groupId]);

  // Countdown updater for open accas
  useEffect(() => {
    const openAccas = accas.filter((a) => a.status === "open" && a.locks_at);
    if (openAccas.length === 0) return;

    const update = () => {
      const countdowns = {};
      openAccas.forEach((acca) => {
        countdowns[acca.id] = formatCountdown(acca.locks_at);
      });
      setAccaCountdowns(countdowns);
    };

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [accas]);

  useEffect(() => {
    if (!isPushSupported()) return;
    if (localStorage.getItem("push-prompt-dismissed")) return;
    if (getPushPermission() !== "default") return;
    setShowPushPrompt(true);
  }, []);

  const loadGroupData = async () => {
    setLoadingGroup(true);
    try {
      const [groupData, accasData, leaderboardData, membersData, accaStatsData] = await Promise.all([
        api.getGroup(groupId),
        api.getAccasByGroup(groupId),
        api.getGroupLeaderboard(groupId),
        api.getGroupMembers(groupId),
        api.getGroupAccaStats(groupId)
      ]);
      setGroup(groupData);
      setAccas(accasData);
      setLeaderboard(leaderboardData);
      setMembers(membersData);
      setAccaStats(accaStatsData);
    } catch (err) {
      console.error("Error loading group data:", err);
      setError(err.response?.data?.detail || "Failed to load group");
    } finally {
      setLoadingGroup(false);
    }
  };

  const loadAccas = async () => {
    try {
      const data = await api.getAccasByGroup(groupId);
      setAccas(data);
    } catch (err) {
      console.error("Error loading accas:", err);
    }
  };

  const loadLeaderboard = async () => {
    setLoadingLeaderboard(true);
    try {
      const data = await api.getGroupLeaderboard(groupId);
      setLeaderboard(data);
    } catch (err) {
      console.error("Error loading leaderboard:", err);
    } finally {
      setLoadingLeaderboard(false);
    }
  };

  const getInviteLink = () => `${window.location.origin}?invite=${group.invite_code}`;
  const getInviteMessage = () => `Join my AccaPicks group "${group.name}"! ${getInviteLink()}`;

  const copyInviteLink = async () => {
    const inviteLink = getInviteLink();
    try {
      await navigator.clipboard.writeText(inviteLink);
      setCopiedInvite(true);
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
        setCopiedInvite(true);
      } catch {
        setCopiedInvite(false);
        alert("Failed to copy. Your invite link: " + inviteLink);
        return;
      }
    }
    setTimeout(() => setCopiedInvite(false), 2000);
  };

  const shareWhatsApp = () => {
    window.open(`https://wa.me/?text=${encodeURIComponent(getInviteMessage())}`, "_blank");
  };

  const shareMessenger = () => {
    window.open(`fb-messenger://share/?link=${encodeURIComponent(getInviteLink())}`, "_blank");
  };

  const shareNative = async () => {
    try {
      await navigator.share({
        title: `Join ${group.name} on AccaPicks`,
        text: getInviteMessage(),
        url: getInviteLink(),
      });
    } catch {
      // User cancelled or share API failed — fall back to copy
      copyInviteLink();
    }
  };

  const handleWizardCreate = async (wizardData) => {
    setError("");
    try {
      const data = await api.createAcca(
        groupId,
        wizardData.name,
        wizardData.matchDates,
        wizardData.leagues,
        wizardData.betType,
      );
      await loadAccas();
      setShowAccaWizard(false);
      navigate(`/groups/${groupId}/accas/${data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create acca");
    }
  };

  const handleLeaveGroup = async () => {
    if (leaving) return;
    if (!window.confirm("Are you sure you want to leave this group? Your picks will be removed.")) {
      return;
    }

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

  const handleRemoveMember = async (memberId, memberUsername) => {
    if (!window.confirm(`Remove ${memberUsername} from this group?`)) {
      return;
    }

    setLoadingMembers(true);
    try {
      await api.removeMember(groupId, memberId);
      showToast(`${memberUsername} has been removed from the group`, "success");
      const [membersData, leaderboardData] = await Promise.all([
        api.getGroupMembers(groupId),
        api.getGroupLeaderboard(groupId)
      ]);
      setMembers(membersData);
      setLeaderboard(leaderboardData);
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to remove member", "error");
    } finally {
      setLoadingMembers(false);
    }
  };

  const handleEnableNotifications = async () => {
    try {
      await subscribeToPush();
      showToast("Notifications enabled!", "success");
      setShowPushPrompt(false);
    } catch (err) {
      if (err.message?.includes("denied")) {
        showToast("Notifications blocked. You can enable them in browser settings.", "warning");
      }
      setShowPushPrompt(false);
    }
  };

  const handleDismissPushPrompt = () => {
    localStorage.setItem("push-prompt-dismissed", "1");
    setShowPushPrompt(false);
  };

  // Determine if current user is admin
  const isCurrentUserAdmin = members.find(m => m.user_id === user?.id)?.role === "admin";

  if (loadingGroup) {
    return (
      <div className="group-detail-page page-content">
        <button className="btn btn-ghost mb-20" disabled>
          &larr; Back to Groups
        </button>
        <Skeleton width="200px" height="24px" count={1} />
        <div className="skeleton-spacer">
          <Skeleton width="100%" height="80px" count={1} />
        </div>
        <div className="skeleton-spacer">
          <Skeleton width="100%" height="120px" count={1} />
        </div>
        <div className="skeleton-spacer">
          <Skeleton width="60%" height="20px" count={1} />
          <Skeleton width="80%" height="16px" count={1} />
          <Skeleton width="70%" height="16px" count={1} />
        </div>
      </div>
    );
  }

  if (error && !group) {
    return (
      <div className="group-detail-page page-content">
        <button className="btn btn-ghost mb-20" onClick={() => navigate("/")}>
          &larr; Back to Groups
        </button>
        <div className="alert-error">{error}</div>
      </div>
    );
  }

  if (!group) {
    return <div className="alert-error">Group not found</div>;
  }

  return (
    <div className="group-detail-page">
      <div className="group-detail-header">
        <button
          className="btn btn-ghost"
          onClick={() => navigate("/")}
        >
          &larr; Back to Groups
        </button>
        {!showInvite ? (
          <button className="btn btn-secondary btn-sm" onClick={() => setShowInvite(true)}>
            Invite Friends
          </button>
        ) : (
          <div className="invite-panel">
            <button className="invite-panel-close" onClick={() => setShowInvite(false)} aria-label="Close invite panel">&times;</button>
            <div className="invite-code-row">
              <code className="invite-code">{group.invite_code}</code>
              <button className="btn btn-primary btn-sm" onClick={copyInviteLink}>
                {copiedInvite ? "Copied!" : "Copy Link"}
              </button>
            </div>
            <div className="invite-share-buttons">
              <button className="btn btn-share btn-whatsapp" onClick={shareWhatsApp}>
                WhatsApp
              </button>
              <button className="btn btn-share btn-messenger" onClick={shareMessenger}>
                Messenger
              </button>
              {typeof navigator !== "undefined" && navigator.share && (
                <button className="btn btn-share btn-native-share" onClick={shareNative}>
                  Share...
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      <h2 className="section-title">{group.name}</h2>

      {/* Leaderboard Display */}
      <Leaderboard
        leaderboard={leaderboard}
        loading={loadingLeaderboard}
        accas={accas}
        groupId={groupId}
        accaStats={accaStats}
      />

      {/* Push Notification Prompt */}
      {showPushPrompt && (
        <div className="card" style={{ marginBottom: '16px', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
          <span style={{ fontSize: '14px', color: 'var(--text-secondary, #94a3b8)' }}>
            Get notified when mates add picks?
          </span>
          <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
            <button className="btn btn-primary btn-sm" onClick={handleEnableNotifications}>
              Enable
            </button>
            <button className="btn btn-ghost btn-sm" onClick={handleDismissPushPrompt}>
              Not now
            </button>
          </div>
        </div>
      )}

      {/* Create Acca Wizard */}
      {!showAccaWizard ? (
        <div className="groups-actions">
          <button
            className="btn btn-primary"
            onClick={() => setShowAccaWizard(true)}
          >
            + Create New Acca
          </button>
        </div>
      ) : (
        <AccaWizard
          onCreated={handleWizardCreate}
          onCancel={() => {
            setShowAccaWizard(false);
            setError("");
          }}
          error={error}
        />
      )}

      {/* Open Accas Section */}
      <h3 className="section-title">Open Accas</h3>

      {(() => {
        const openAccas = accas.filter((a) => a.status === "open");
        const activeAccas = accas.filter((a) => a.status === "locked");
        const settledAccas = accas.filter((a) => a.status === "settled" || a.status === "won" || a.status === "lost");

        return (
          <>
            {openAccas.length === 0 ? (
              <p className="empty-state">
                No open accumulators. Create one to get started!
              </p>
            ) : (
              <div>
                {openAccas.map((acca) => (
                  <div
                    key={acca.id}
                    onClick={() => navigate(`/groups/${groupId}/accas/${acca.id}`)}
                    className="card card-clickable"
                  >
                    <div className="card-header">
                      <h3 className="group-card-name">{acca.name}</h3>
                      <span className="badge badge-open">OPEN</span>
                    </div>
                    <div className="acca-card-meta">
                      {acca.leagues && (
                        <small className="acca-card-leagues">
                          {acca.leagues.map((k) => LEAGUE_NAME_MAP[k] || k).join(", ")}
                        </small>
                      )}
                      {acca.match_dates && (
                        <small className="acca-card-dates">
                          {[...acca.match_dates]
                            .sort()
                            .map((d) => {
                              const dt = new Date(d + "T00:00:00");
                              return dt.toLocaleDateString("en-GB", {
                                month: "short",
                                day: "numeric",
                              });
                            })
                            .join(", ")}
                        </small>
                      )}
                    </div>
                    <small className="acca-card-status">
                      Created {new Date(acca.created_at).toLocaleDateString()}
                    </small>
                    {acca.locks_at && (
                      <small className="acca-card-countdown">
                        Locks in {accaCountdowns[acca.id] || "..."}
                      </small>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Active (Locked) Accas Toggle */}
            {activeAccas.length > 0 && (
              <>
                <button
                  className="btn btn-secondary mb-20"
                  onClick={() => setShowActive(!showActive)}
                >
                  {showActive
                    ? "Hide Active Accas"
                    : `Active Accas (${activeAccas.length})`}
                </button>

                {showActive && (
                  <div>
                    {activeAccas.map((acca) => (
                      <div
                        key={acca.id}
                        onClick={() => navigate(`/groups/${groupId}/accas/${acca.id}`)}
                        className="card card-clickable"
                      >
                        <div className="card-header">
                          <h3 className="group-card-name">{acca.name}</h3>
                          <span className="badge badge-locked">LOCKED</span>
                        </div>
                        <div className="acca-card-meta">
                          {acca.leagues && (
                            <small className="acca-card-leagues">
                              {acca.leagues.map((k) => LEAGUE_NAME_MAP[k] || k).join(", ")}
                            </small>
                          )}
                          {acca.match_dates && (
                            <small className="acca-card-dates">
                              {[...acca.match_dates]
                                .sort()
                                .map((d) => {
                                  const dt = new Date(d + "T00:00:00");
                                  return dt.toLocaleDateString("en-GB", {
                                    month: "short",
                                    day: "numeric",
                                  });
                                })
                                .join(", ")}
                            </small>
                          )}
                        </div>
                        <small className="acca-card-status">
                          Created {new Date(acca.created_at).toLocaleDateString()}
                        </small>
                        <small className="acca-card-locked-status">
                          Matches in progress
                        </small>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* Settled Accas Toggle */}
            {settledAccas.length > 0 && (
              <>
                <button
                  className="btn btn-secondary mb-20"
                  onClick={() => setShowSettled(!showSettled)}
                >
                  {showSettled
                    ? "Hide Settled Accas"
                    : `Settled Accas (${settledAccas.length})`}
                </button>

                {showSettled && (
                  <div>
                    {settledAccas.map((acca) => (
                      <div
                        key={acca.id}
                        onClick={() => navigate(`/groups/${groupId}/accas/${acca.id}`)}
                        className="card card-clickable"
                      >
                        <div className="card-header">
                          <h3 className="group-card-name">{acca.name}</h3>
                          <span className={`badge ${acca.status === "won" ? "badge-won" : acca.status === "lost" ? "badge-lost" : "badge-settled"}`}>
                            {acca.status.toUpperCase()}
                          </span>
                        </div>
                        <div className="acca-card-meta">
                          {acca.leagues && (
                            <small className="acca-card-leagues">
                              {acca.leagues.map((k) => LEAGUE_NAME_MAP[k] || k).join(", ")}
                            </small>
                          )}
                          {acca.match_dates && (
                            <small className="acca-card-dates">
                              {[...acca.match_dates]
                                .sort()
                                .map((d) => {
                                  const dt = new Date(d + "T00:00:00");
                                  return dt.toLocaleDateString("en-GB", {
                                    month: "short",
                                    day: "numeric",
                                  });
                                })
                                .join(", ")}
                            </small>
                          )}
                        </div>
                        <small className="acca-card-status">
                          Created {new Date(acca.created_at).toLocaleDateString()}
                        </small>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </>
        );
      })()}

      {/* Leave Group — subtle link to avoid accidental taps near logout */}
      <div className="group-leave-section">
        <button
          className="group-leave-link"
          onClick={handleLeaveGroup}
          disabled={leaving}
        >
          {leaving ? "Leaving..." : "Leave this group"}
        </button>
      </div>
    </div>
  );
}
