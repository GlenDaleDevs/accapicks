import { useNavigate } from "react-router-dom";

export default function TopBar({ user, oddsFormat, setOddsFormat }) {
  const navigate = useNavigate();

  const toggleOddsFormat = () => {
    setOddsFormat(prev => prev === "decimal" ? "fractional" : "decimal");
  };

  return (
    <div className="top-bar">
      <p className="top-bar-welcome">
        Welcome back, <span className="top-bar-username">{user?.username}</span>!
      </p>
      <div className="top-bar-actions">
        <button
          className="btn btn-ghost btn-sm"
          onClick={toggleOddsFormat}
          title={`Switch to ${oddsFormat === "decimal" ? "fractional" : "decimal"} odds`}
        >
          {oddsFormat === "decimal" ? "Decimal" : "Fractional"}
        </button>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate("/settings")}>
          Settings
        </button>
      </div>
    </div>
  );
}
