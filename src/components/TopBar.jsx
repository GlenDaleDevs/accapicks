export default function TopBar({ user, onLogout }) {
  return (
    <div className="top-bar">
      <div>
        <p className="top-bar-welcome">
          Welcome back, <span className="top-bar-username">{user?.username}</span>!
        </p>
      </div>
      <button className="btn btn-ghost" onClick={onLogout}>
        Logout
      </button>
    </div>
  );
}
