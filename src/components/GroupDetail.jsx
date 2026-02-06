import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { LEAGUE_NAME_MAP } from "../utils/constants";
import { formatCountdown } from "../utils/formatters";
import * as api from "../api/client";
import { showToast } from "../utils/toast";
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
  const [leaderboard, setLeaderboard] = useState([]);
  const [loadingLeaderboard, setLoadingLeaderboard] = useState(false);
  const [loadingGroup, setLoadingGroup] = useState(true);
  const [copiedInvite, setCopiedInvite] = useState(false);
  const [error, setError] = useState("");
  const [accaCountdowns, setAccaCountdowns] = useState({});
  const [members, setMembers] = useState([]);
  const [loadingMembers, setLoadingMembers] = useState(false);

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

  const loadGroupData = async () => {
    setLoadingGroup(true);
    try {
      const [groupData, accasData, leaderboardData, membersData] = await Promise.all([
        api.getGroup(groupId),
        api.getAccasByGroup(groupId),
        api.getGroupLeaderboard(groupId),
        api.getGroupMembers(groupId)
      ]);
      setGroup(groupData);
      setAccas(accasData);
      setLeaderboard(leaderboardData);
      setMembers(membersData);
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

  const copyInviteLink = () => {
    const inviteLink = `${window.location.origin}?invite=${group.invite_code}`;
    navigator.clipboard.writeText(inviteLink);
    setCopiedInvite(true);
    setTimeout(() => setCopiedInvite(false), 2000);
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
    if (!window.confirm("Are you sure you want to leave this group? Your picks will be removed.")) {
      return;
    }

    try {
      await api.leaveGroup(groupId);
      showToast("Successfully left the group", "success");
      if (onRefreshGroups) onRefreshGroups();
      navigate("/");
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to leave group", "error");
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

  // Determine if current user is admin
  const isCurrentUserAdmin = members.find(m => m.user_id === user?.id)?.role === "admin";

  if (loadingGroup) {
    return (
      <div>
        <button className="btn btn-ghost mb-20" disabled>
          &larr; Back to Groups
        </button>
        <Skeleton width="200px" height="24px" count={1} />
        <div style={{ marginTop: "20px" }}>
          <Skeleton width="100%" height="80px" count={1} />
        </div>
        <div style={{ marginTop: "20px" }}>
          <Skeleton width="100%" height="120px" count={1} />
        </div>
        <div style={{ marginTop: "20px" }}>
          <Skeleton width="60%" height="20px" count={1} />
          <Skeleton width="80%" height="16px" count={1} />
          <Skeleton width="70%" height="16px" count={1} />
        </div>
      </div>
    );
  }

  if (error && !group) {
    return <div className="alert-error">{error}</div>;
  }

  if (!group) {
    return <div className="alert-error">Group not found</div>;
  }

  return (
    <>
      <button
        className="btn btn-ghost mb-20"
        onClick={() => navigate("/")}
      >
        &larr; Back to Groups
      </button>

      <h2 className="section-title">{group.name}</h2>

      {/* Invite Section */}
      <div className="invite-section">
        <h3 className="invite-title">Invite Friends</h3>
        <p className="invite-text">Share this code with your mates:</p>
        <div className="invite-code-row">
          <code className="invite-code">{group.invite_code}</code>
          <button className="btn btn-primary" onClick={copyInviteLink}>
            {copiedInvite ? "Copied!" : "Copy Link"}
          </button>
        </div>
      </div>

      {/* Members Section */}
      <div style={{ marginBottom: "24px" }}>
        <h3 className="section-title">Members</h3>
        {loadingMembers ? (
          <Skeleton width="100%" height="60px" count={2} />
        ) : members.length === 0 ? (
          <p className="empty-state">No members found</p>
        ) : (
          <div>
            {members.map((member) => (
              <div key={member.user_id} className="member-card">
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span className="member-name">{member.username}</span>
                  <span className={`badge badge-role ${member.role === "admin" ? "badge-admin" : "badge-member"}`}>
                    {member.role === "admin" ? "Admin" : "Member"}
                  </span>
                </div>
                {isCurrentUserAdmin && member.role !== "admin" && member.user_id !== user?.id && (
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveMember(member.user_id, member.username);
                    }}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Leaderboard Display */}
      <Leaderboard
        leaderboard={leaderboard}
        loading={loadingLeaderboard}
        accas={accas}
      />

      {/* Create Acca Wizard */}
      {!showAccaWizard ? (
        <button
          className="btn btn-primary mb-20"
          onClick={() => setShowAccaWizard(true)}
        >
          + Create New Acca
        </button>
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

      {/* Active Accas Section */}
      <h3 className="section-title">Active Accas</h3>

      {/* Active Acca List */}
      {(() => {
        const activeAccas = accas.filter(
          (a) => a.status === "open" || a.status === "locked"
        );
        const settledAccas = accas.filter((a) => a.status === "settled");

        return (
          <>
            {activeAccas.length === 0 ? (
              <p className="empty-state">
                No active accumulators. Create one to get started!
              </p>
            ) : (
              <div>
                {activeAccas.map((acca) => (
                  <div
                    key={acca.id}
                    onClick={() => navigate(`/groups/${groupId}/accas/${acca.id}`)}
                    className="card card-clickable"
                  >
                    <div className="card-header">
                      <h3 className="group-card-name">{acca.name}</h3>
                      {acca.status === "locked" && (
                        <span className="badge badge-locked">LOCKED</span>
                      )}
                      {acca.status === "open" && (
                        <span className="badge badge-open">OPEN</span>
                      )}
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
                      Status: {acca.status} | Created{" "}
                      {new Date(acca.created_at).toLocaleDateString()}
                    </small>
                    {acca.status === "open" && acca.locks_at && (
                      <small className="acca-card-countdown">
                        Locks in {accaCountdowns[acca.id] || "..."}
                      </small>
                    )}
                    {acca.status === "locked" && (
                      <small className="acca-card-locked-status">
                        Matches in progress
                      </small>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Settled Accas Toggle */}
            <button
              className="btn btn-secondary mb-20"
              onClick={() => setShowSettled(!showSettled)}
            >
              {showSettled
                ? "Hide Settled Accas"
                : `Show Settled Accas (${settledAccas.length})`}
            </button>

            {showSettled && (
              settledAccas.length === 0 ? (
                <p className="empty-state">No settled accumulators yet.</p>
              ) : (
                <div>
                  {settledAccas.map((acca) => (
                      <div
                        key={acca.id}
                        onClick={() => navigate(`/groups/${groupId}/accas/${acca.id}`)}
                        className="card card-clickable"
                      >
                        <div className="card-header">
                          <h3 className="group-card-name">{acca.name}</h3>
                          <span className="badge badge-settled">SETTLED</span>
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
                          Status: {acca.status} | Created{" "}
                          {new Date(acca.created_at).toLocaleDateString()}
                        </small>
                      </div>
                    ))}
                </div>
              )
            )}
          </>
        );
      })()}

      {/* Leave Group */}
      <div style={{ marginTop: "40px", paddingTop: "20px", borderTop: "1px solid #e5e7eb" }}>
        <button
          className="btn btn-danger"
          onClick={handleLeaveGroup}
        >
          Leave Group
        </button>
      </div>
    </>
  );
}
