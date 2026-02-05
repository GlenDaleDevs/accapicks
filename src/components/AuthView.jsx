import { useState, useEffect } from "react";

export default function AuthView({
  onLogin,
  onSignup,
  onVerify,
  onResendCode,
  error: externalError,
  pendingVerificationEmail,
}) {
  const [mode, setMode] = useState(pendingVerificationEmail ? "verify" : "login"); // login, signup, verify
  const [email, setEmail] = useState(pendingVerificationEmail || "");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Switch to verify mode when pendingVerificationEmail is set after signup
  useEffect(() => {
    if (pendingVerificationEmail) {
      setMode("verify");
      setEmail(pendingVerificationEmail);
    }
  }, [pendingVerificationEmail]);

  const displayError = externalError || error;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "signup") {
        if (password.length < 8) {
          setError("Password must be at least 8 characters");
          setLoading(false);
          return;
        }
        if (!/[a-zA-Z]/.test(password)) {
          setError("Password must contain at least one letter");
          setLoading(false);
          return;
        }
        if (!/\d/.test(password)) {
          setError("Password must contain at least one digit");
          setLoading(false);
          return;
        }
        await onSignup(email, username, password);
      } else if (mode === "verify") {
        await onVerify(email, verificationCode);
      } else {
        await onLogin(email, password);
      }
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    setError("");
    setLoading(true);
    try {
      await onResendCode(email);
      setError(""); // Clear any previous error
      alert("Verification code sent! Check your email.");
    } catch (err) {
      setError(err.message || "Failed to resend code");
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    setError("");
    setVerificationCode("");
    if (newMode !== "verify") {
      setEmail("");
      setUsername("");
      setPassword("");
    }
  };

  return (
    <div className="auth-container">
      <h1 className="auth-title">AccaPicks</h1>
      <p className="auth-subtitle">
        {mode === "signup" && "Create your account"}
        {mode === "login" && "Login to start creating accumulators"}
        {mode === "verify" && "Enter verification code"}
      </p>

      {displayError && <div className="alert-error">{displayError}</div>}

      <form className="auth-form" onSubmit={handleSubmit}>
        {mode === "verify" ? (
          <>
            <div className="form-group">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                placeholder="000000"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ""))}
                required
                className="verification-code-input"
                autoComplete="one-time-code"
              />
            </div>
            <div className="auth-actions">
              <button type="submit" className="btn btn-primary" disabled={loading || verificationCode.length !== 6}>
                {loading ? "Verifying..." : "Verify Email"}
              </button>
              <button type="button" className="btn btn-ghost" onClick={handleResendCode} disabled={loading}>
                Resend Code
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => switchMode("login")}>
                Back to Login
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="form-group">
              <input
                type={mode === "signup" ? "email" : "text"}
                placeholder={mode === "signup" ? "Email" : "Email or Username"}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {mode === "signup" && (
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
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? "Loading..." : mode === "signup" ? "Sign Up" : "Login"}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => switchMode(mode === "signup" ? "login" : "signup")}
              >
                {mode === "signup" ? "Already have an account?" : "Need an account?"}
              </button>
            </div>
          </>
        )}
      </form>
    </div>
  );
}
