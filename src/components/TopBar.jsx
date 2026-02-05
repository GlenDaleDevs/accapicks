export default function TopBar({ user, onLogout, oddsFormat, setOddsFormat }) {
  const toggleOddsFormat = () => {
    setOddsFormat(prev => prev === "decimal" ? "fractional" : "decimal");
  };

  return (
    <div className="top-bar">
      <div>
        <p className="top-bar-welcome">
          Welcome back, <span className="top-bar-username">{user?.username}</span>!
        </p>
      </div>
      <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
        <button
          className="btn btn-ghost"
          onClick={toggleOddsFormat}
          title={`Switch to ${oddsFormat === "decimal" ? "fractional" : "decimal"} odds`}
        >
          {oddsFormat === "decimal" ? "Decimal" : "Fractional"}
        </button>
        <button className="btn btn-ghost" onClick={onLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}
