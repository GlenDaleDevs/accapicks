import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Skeleton from "./Skeleton";
import MiniLeaderboard from "./MiniLeaderboard";

export default function GroupsList({ groups, onCreateGroup, onJoinGroup, error: externalError, loading, miniLeaderboards }) {
  const navigate = useNavigate();
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showJoinGroup, setShowJoinGroup] = useState(false);
  const [groupName, setGroupName] = useState("");
  const [groupDescription, setGroupDescription] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState("");

  const displayError = externalError || error;

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await onCreateGroup(groupName, groupDescription);
      setShowCreateGroup(false);
      setGroupName("");
      setGroupDescription("");
    } catch (err) {
      setError(err.message || "Failed to create group");
    }
  };

  const handleJoin = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await onJoinGroup(inviteCode);
      setShowJoinGroup(false);
      setInviteCode("");
    } catch (err) {
      setError(err.message || "Failed to join group");
    }
  };

  return (
    <>
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
                <button type="submit" className="btn btn-primary">
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
          <div className={`groups-grid${groups.length === 1 ? " groups-grid-single" : ""}`}>
            {groups.map((group) => (
              <div
                key={group.id}
                onClick={() => navigate(`/groups/${group.id}`)}
                className="card card-clickable group-card"
              >
                <div className="group-card-info">
                  <h3 className="group-card-name">{group.name}</h3>
                  {group.description && (
                    <p className="group-card-desc">{group.description}</p>
                  )}
                  <small className="group-card-date">
                    Created {new Date(group.created_at).toLocaleDateString()}
                  </small>
                </div>
                <div className="group-card-lb">
                  <MiniLeaderboard entries={miniLeaderboards?.[group.id]} />
                </div>
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
                <button type="submit" className="btn btn-primary">
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
    </>
  );
}
