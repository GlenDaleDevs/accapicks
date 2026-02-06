import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/client";

export default function UserSettings({ user, oddsFormat, setOddsFormat }) {
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    // Client-side validation
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (!/[a-zA-Z]/.test(newPassword)) {
      setError("Password must contain at least one letter");
      return;
    }
    if (!/\d/.test(newPassword)) {
      setError("Password must contain at least one digit");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      await api.changePassword(currentPassword, newPassword);
      setSuccess("Password changed successfully!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to change password");
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-GB", {
      day: "numeric",
      month: "long",
      year: "numeric"
    });
  };

  return (
    <div className="settings-container">
      <button
        className="settings-back-link"
        onClick={() => navigate("/")}
      >
        ← Back to Groups
      </button>

      <h2 className="section-title" style={{ marginTop: "24px" }}>Settings</h2>

      {/* Account Info */}
      <div className="settings-section">
        <h3 className="settings-section-title">Account Information</h3>
        <div className="settings-info-row">
          <span className="settings-info-label">Username</span>
          <span className="settings-info-value">{user?.username}</span>
        </div>
        <div className="settings-info-row">
          <span className="settings-info-label">Email</span>
          <span className="settings-info-value">{user?.email}</span>
        </div>
        <div className="settings-info-row" style={{ borderBottom: "none" }}>
          <span className="settings-info-label">Member since</span>
          <span className="settings-info-value">
            {user?.created_at ? formatDate(user.created_at) : "N/A"}
          </span>
        </div>
      </div>

      {/* Odds Format */}
      <div className="settings-section">
        <h3 className="settings-section-title">Odds Format</h3>
        <div className="settings-toggle-group">
          <button
            className={`settings-toggle-btn ${oddsFormat === "decimal" ? "settings-toggle-active" : ""}`}
            onClick={() => setOddsFormat("decimal")}
          >
            Decimal
          </button>
          <button
            className={`settings-toggle-btn ${oddsFormat === "fractional" ? "settings-toggle-active" : ""}`}
            onClick={() => setOddsFormat("fractional")}
          >
            Fractional
          </button>
        </div>
      </div>

      {/* Change Password */}
      <div className="settings-section">
        <h3 className="settings-section-title">Change Password</h3>
        {error && <div className="alert-error">{error}</div>}
        {success && <div className="alert-success">{success}</div>}
        <form onSubmit={handlePasswordChange}>
          <div className="form-group">
            <input
              type="password"
              placeholder="Current Password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <input
              type="password"
              placeholder="New Password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <input
              type="password"
              placeholder="Confirm New Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: "100%", marginTop: "8px" }}
          >
            {loading ? "Changing Password..." : "Change Password"}
          </button>
        </form>
      </div>
    </div>
  );
}
