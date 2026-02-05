import { useState } from "react";

export default function AuthView({ onLogin, onSignup, error: externalError }) {
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const displayError = externalError || error;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (isSignup) {
      if (password.length < 8) {
        setError("Password must be at least 8 characters");
        return;
      }
      if (!/[a-zA-Z]/.test(password)) {
        setError("Password must contain at least one letter");
        return;
      }
      if (!/\d/.test(password)) {
        setError("Password must contain at least one digit");
        return;
      }
    }

    try {
      if (isSignup) {
        await onSignup(email, username, password);
      } else {
        await onLogin(email, password);
      }
    } catch (err) {
      setError(err.message || (isSignup ? "Signup failed" : "Login failed"));
    }
  };

  return (
    <div className="auth-container">
      <h1 className="auth-title">AccaPicks</h1>
      <p className="auth-subtitle">
        {isSignup
          ? "Create your account"
          : "Login to start creating accumulators"}
      </p>

      {displayError && <div className="alert-error">{displayError}</div>}

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <input
            type="text"
            placeholder="Email or Username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        {isSignup && (
          <div className="form-group">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
        )}

        <div className="form-group">
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <div className="auth-actions">
          <button type="submit" className="btn btn-primary">
            {isSignup ? "Sign Up" : "Login"}
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              setIsSignup(!isSignup);
              setError("");
            }}
          >
            {isSignup ? "Already have an account?" : "Need an account?"}
          </button>
        </div>
      </form>
    </div>
  );
}
