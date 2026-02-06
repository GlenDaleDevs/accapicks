import { useState, useEffect } from "react";

export default function AuthView({
  onLogin,
  onSignup,
  onVerify,
  onResendCode,
  onForgotPassword,
  onResetPassword,
  error: externalError,
  pendingVerificationEmail,
}) {
  const [mode, setMode] = useState(pendingVerificationEmail ? "verify" : "login"); // login, signup, verify, forgot, reset
  const [email, setEmail] = useState(pendingVerificationEmail || "");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [ageConfirmed, setAgeConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

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
    setSuccessMessage("");
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
      } else if (mode === "forgot") {
        await onForgotPassword(email);
        setSuccessMessage("If an account exists with that email, we've sent a reset code.");
        switchMode("reset");
      } else if (mode === "reset") {
        await onResetPassword(email, verificationCode, password);
        setSuccessMessage("Password reset successful!");
        setTimeout(() => switchMode("login"), 2000);
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
    setSuccessMessage("");
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

  const handleResendResetCode = async () => {
    setError("");
    setSuccessMessage("");
    setLoading(true);
    try {
      await onForgotPassword(email);
      setError("");
      alert("Reset code sent! Check your email.");
    } catch (err) {
      setError(err.message || "Failed to resend code");
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    setError("");
    setSuccessMessage("");
    setVerificationCode("");
    setAgeConfirmed(false);
    if (newMode !== "verify" && newMode !== "reset") {
      setEmail("");
      setUsername("");
      setPassword("");
    }
  };

  return (
    <div className="auth-container">
      <h1 className="auth-title">AccaPicks</h1>
      <p className="auth-tagline">Find out who sends the best picks in your group chat!</p>

      {displayError && <div className="alert-error">{displayError}</div>}
      {successMessage && <div className="alert-success">{successMessage}</div>}

      <div className="auth-form-container">
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
        ) : mode === "forgot" ? (
          <>
            <h2 className="auth-mode-title">Reset Password</h2>
            <div className="form-group">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="auth-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? "Sending..." : "Send Reset Code"}
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => switchMode("login")}>
                Back to Login
              </button>
            </div>
          </>
        ) : mode === "reset" ? (
          <>
            <h2 className="auth-mode-title">Enter Reset Code</h2>
            <p className="auth-feedback">Check your email for a 6-digit reset code</p>
            <div className="form-group">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                readOnly
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
            <div className="form-group">
              <input
                type="password"
                placeholder="New Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <div className="auth-actions">
              <button type="submit" className="btn btn-primary" disabled={loading || verificationCode.length !== 6}>
                {loading ? "Resetting..." : "Reset Password"}
              </button>
              <button type="button" className="btn btn-ghost" onClick={handleResendResetCode} disabled={loading}>
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

            {mode === "signup" && (
              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={ageConfirmed}
                    onChange={(e) => setAgeConfirmed(e.target.checked)}
                    required
                  />
                  <span>I confirm I am 18 years or older</span>
                </label>
              </div>
            )}

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
              {mode === "login" && (
                <button type="button" className="btn btn-ghost" onClick={() => switchMode("forgot")}>
                  Forgot password?
                </button>
              )}
            </div>
          </>
        )}
      </form>
      </div>
    </div>
  );
}
