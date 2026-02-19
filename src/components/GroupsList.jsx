import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Skeleton from "./Skeleton";
import Leaderboard from "./Leaderboard";

export default function GroupsList({ groups, onCreateGroup, onJoinGroup, error: externalError, loading, leaderboards, accaStatsMap }) {
  const navigate = useNavigate();
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showJoinGroup, setShowJoinGroup] = useState(false);
  const [groupName, setGroupName] = useState("");
  const [groupDescription, setGroupDescription] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const displayError = externalError || error;

  const handleCreate = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;
    setIsSubmitting(true);
    setError("");
    try {
      await onCreateGroup(groupName, groupDescription);
      setShowCreateGroup(false);
      setGroupName("");
      setGroupDescription("");
    } catch (err) {
      setError(err.message || "Failed to create group");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleJoin = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;
    setIsSubmitting(true);
    setError("");
    try {
      await onJoinGroup(inviteCode);
      setShowJoinGroup(false);
      setInviteCode("");
    } catch (err) {
      setError(err.message || "Failed to join group");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="groups-page">
      <div className="dashboard-hero">
        <div className="dashboard-header">
          <h2 className="dashboard-title">Your Groups</h2>
          {!showJoinGroup && (
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setShowJoinGroup(true)}
            >
              Join Group
            </button>
          )}
        </div>
        {showJoinGroup && (
          <div className="form-panel mb-16">
            <h3 className="form-panel-title">Join Group</h3>

            {displayError && <div className="alert-error">{displayError}</div>}

            <form onSubmit={handleJoin}>
              <div className="form-group">
                <input
                  type="text"
                  placeholder="Enter Invite Code (e.g., ABC123)"
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
                  required
                />
              </div>

              <div className="btn-group">
                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                  Join Group
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    setShowJoinGroup(false);
                    setInviteCode("");
                    setError("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {loading ? (
          <Skeleton width="100%" height="80px" count={2} />
        ) : groups.length > 0 ? (
          <div className="home-groups-list">
            {groups.map((group) => (
              <div key={group.id} className="home-group-section">
                <button
                  className="home-group-header"
                  onClick={() => navigate(`/groups/${group.id}`)}
                >
                  <span className="home-group-name">{group.name}</span>
                  <span className="home-group-chevron">›</span>
                </button>
                <Leaderboard
                  leaderboard={leaderboards?.[group.id] || []}
                  loading={false}
                  groupId={group.id}
                  accaStats={accaStatsMap?.[group.id]}
                  title={null}
                />
              </div>
            ))}
          </div>
        ) : null}

        <p className="dashboard-subtitle">Create accumulators with your mates and climb the leaderboard</p>
      </div>

      {!loading && groups.length === 0 && (
        <div className="welcome-guide">
          <h3 className="welcome-guide-title">How AccaPicks Works</h3>
          <div className="welcome-steps">
            <div className="welcome-step">
              <span className="welcome-step-num">1</span>
              <div>
                <h4 className="welcome-step-title">Create or Join a Group</h4>
                <p className="welcome-step-desc">Start a group for your mates or join one with an invite code.</p>
              </div>
            </div>
            <div className="welcome-step">
              <span className="welcome-step-num">2</span>
              <div>
                <h4 className="welcome-step-title">Build Accumulators Together</h4>
                <p className="welcome-step-desc">Each person picks one match per acca. Your picks combine into a group accumulator.</p>
              </div>
            </div>
            <div className="welcome-step">
              <span className="welcome-step-num">3</span>
              <div>
                <h4 className="welcome-step-title">Track Results & Compete</h4>
                <p className="welcome-step-desc">Results update automatically. See who has the best win rate on the group leaderboard.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="groups-actions">
        {!showCreateGroup ? (
          <button
            className="btn btn-primary"
            onClick={() => setShowCreateGroup(true)}
          >
            + Create New Group
          </button>
        ) : (
          <div className="form-panel mb-20">
            <h3 className="form-panel-title">Create New Group</h3>

            {displayError && <div className="alert-error">{displayError}</div>}

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <input
                  type="text"
                  placeholder="Group Name"
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  required
                  maxLength={100}
                />
              </div>

              <div className="form-group">
                <textarea
                  placeholder="Description (optional)"
                  value={groupDescription}
                  onChange={(e) => setGroupDescription(e.target.value)}
                  style={{ minHeight: "60px" }}
                  maxLength={500}
                />
              </div>

              <div className="btn-group">
                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                  Create Group
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    setShowCreateGroup(false);
                    setGroupName("");
                    setGroupDescription("");
                    setError("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

      </div>
    </div>
  );
}
