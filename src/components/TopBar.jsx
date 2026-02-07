import { useNavigate } from "react-router-dom";

export default function TopBar({ user }) {
  const navigate = useNavigate();

  return (
    <div className="top-bar">
      <p className="top-bar-welcome">
        Welcome back, <span className="top-bar-username">{user?.username}</span>!
      </p>
      <button className="btn btn-ghost btn-sm" onClick={() => navigate("/settings")}>
        Settings
      </button>
    </div>
  );
}
