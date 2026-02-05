import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function GroupsList({ groups, onCreateGroup, onJoinGroup, error: externalError }) {
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
      <h2 className="section-title">Your Groups</h2>

      <div className="mb-20">
        {!showCreateGroup ? (
          <button
            className="btn btn-primary mb-8"
            onClick={() => setShowCreateGroup(true)}
            style={{ marginRight: "10px" }}
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
                />
              </div>

              <div className="form-group">
                <textarea
                  placeholder="Description (optional)"
                  value={groupDescription}
                  onChange={(e) => setGroupDescription(e.target.value)}
                  style={{ minHeight: "60px" }}
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

        {!showJoinGroup ? (
          <button
            className="btn btn-secondary"
            onClick={() => setShowJoinGroup(true)}
          >
            Join Group with Code
          </button>
        ) : (
          <div className="form-panel mt-16">
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
      </div>

      {groups.length === 0 ? (
        <p className="empty-state">
          No groups yet. Create one or join with an invite code!
        </p>
      ) : (
        <div>
          {groups.map((group) => (
            <div
              key={group.id}
              onClick={() => navigate(`/groups/${group.id}`)}
              className="card card-clickable"
            >
              <h3 className="group-card-name">{group.name}</h3>
              {group.description && (
                <p className="group-card-desc">{group.description}</p>
              )}
              <small className="group-card-date">
                Created {new Date(group.created_at).toLocaleDateString()}
              </small>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
