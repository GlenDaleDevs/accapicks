import { Link, useNavigate } from "react-router-dom";
import GroupsList from "./GroupsList";
import { useApp } from "../context/AppContext";
import { SETTINGS } from "../utils/routes";

export default function MoreTab() {
  const { groups, loadingGroups, error, onCreateGroup, onJoinGroup, onLogout } = useApp();
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate("/");
  };

  return (
    <div className="groups-page">
      <GroupsList
        groups={groups}
        loading={loadingGroups}
        onCreateGroup={onCreateGroup}
        onJoinGroup={onJoinGroup}
        error={error}
      />

      <div className="more-links">
        <button className="btn btn-ghost" onClick={() => navigate(SETTINGS)}>
          Settings
        </button>
        <button className="btn btn-danger" onClick={handleLogout}>
          Logout
        </button>
      </div>

      {/* Compliance copy. Lives here now that .page-logout-footer is gone —
          a fixed tab bar would have covered it at the bottom of every page. */}
      <footer className="responsible-gambling-footer">
        18+ only | Please gamble responsibly | <a href="https://www.begambleaware.org/" target="_blank" rel="noopener noreferrer">BeGambleAware.org</a>
        <br />
        <Link to="/terms">Terms of Service</Link> | <Link to="/privacy">Privacy Policy</Link>
      </footer>
    </div>
  );
}
