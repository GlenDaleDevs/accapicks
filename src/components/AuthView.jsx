import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import "./Landing.css";
import InstallPrompt from "./InstallPrompt";
import { showToast } from "../utils/toast";
import { checkUsername } from "../api/client";

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
  const [usernameStatus, setUsernameStatus] = useState(null); // null | "checking" | "available" | "taken" | "invalid"

  useEffect(() => {
    if (pendingVerificationEmail) {
      setMode("verify");
      setEmail(pendingVerificationEmail);
    }
  }, [pendingVerificationEmail]);

  useEffect(() => {
    if (mode !== "signup" || username.length < 3) {
      setUsernameStatus(null);
      return;
    }

    // Client-side regex check
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      setUsernameStatus("invalid");
      return;
    }

    const timeout = setTimeout(async () => {
      setUsernameStatus("checking");
      try {
        const response = await checkUsername(username);
        if (response.username === username) {
          setUsernameStatus(response.available ? "available" : "taken");
        }
      } catch (err) {
        setUsernameStatus(null);
      }
    }, 300);

    return () => clearTimeout(timeout);
  }, [username, mode]);

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
        await onSignup(email, username, password, ageConfirmed);
      } else if (mode === "verify") {
        await onVerify(email, verificationCode);
      } else if (mode === "forgot") {
        await onForgotPassword(email);
        setSuccessMessage("If an account exists with that email, we've sent a reset code.");
        switchMode("reset");
      } else if (mode === "reset") {
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
        await onResetPassword(email, verificationCode, password);
        setSuccessMessage("Password reset successful!");
        setTimeout(() => switchMode("login"), 2000);
      } else {
        await onLogin(email.trim(), password);
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
      showToast("Verification code sent! Check your email.", "success");
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
      showToast("Reset code sent! Check your email.", "success");
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
    setUsernameStatus(null);
    if (newMode !== "verify" && newMode !== "reset") {
      setEmail("");
      setUsername("");
      setPassword("");
    }
  };

  return (
    <div className="landing-container">
      <div className="landing-hero">
        <h1 className="landing-brand">AccaPicks</h1>
        <h2 className="landing-headline">One group. One acca. Bragging rights.</h2>
        <p className="landing-subtitle">The acca tracker for your group chat.</p>
      </div>

      <div className="landing-features">
        <div className="landing-feature">
          <div className="landing-feature-icon">
            <svg viewBox="0 0 24 24">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </div>
          <span className="landing-feature-text">Build accas together</span>
        </div>
        <div className="landing-feature">
          <div className="landing-feature-icon">
            <svg viewBox="0 0 24 24">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
          </div>
          <span className="landing-feature-text">Compare bookmakers</span>
        </div>
        <div className="landing-feature">
          <div className="landing-feature-icon">
            <svg viewBox="0 0 24 24">
              <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>
              <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>
              <path d="M4 22h16"></path>
              <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path>
              <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path>
              <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path>
            </svg>
          </div>
          <span className="landing-feature-text">Group Leaderboards</span>
        </div>
      </div>

      <div className="auth-form-container">
        {displayError && <div className="alert-error">{displayError}</div>}
        {successMessage && <div className="alert-success">{successMessage}</div>}
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
                maxLength={254}
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
                maxLength={254}
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
                maxLength={254}
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
                maxLength={128}
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
                inputMode="email"
                autoCapitalize="off"
                autoCorrect="off"
                spellCheck={false}
                autoComplete={mode === "signup" ? "email" : "username"}
                placeholder={mode === "signup" ? "Email" : "Email or Username"}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                maxLength={254}
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
                  maxLength={20}
                />
                {usernameStatus && (
                  <div className={`username-feedback ${usernameStatus}`}>
                    {usernameStatus === "checking" && "Checking..."}
                    {usernameStatus === "available" && "\u2713 Username available"}
                    {usernameStatus === "taken" && "\u2717 Username taken"}
                    {usernameStatus === "invalid" && "\u2717 Letters, numbers, and underscores only"}
                  </div>
                )}
              </div>
            )}

            <div className="form-group">
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                maxLength={128}
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
              <button type="submit" className="btn btn-primary" disabled={loading || (mode === "signup" && (usernameStatus === "taken" || usernameStatus === "invalid" || usernameStatus === "checking"))}>
                {loading ? "Loading..." : mode === "signup" ? "Sign Up" : "Login Here"}
              </button>
              <div className="auth-links">
                <a
                  href="#"
                  className="auth-link"
                  onClick={(e) => { e.preventDefault(); switchMode(mode === "signup" ? "login" : "signup"); }}
                >
                  {mode === "signup" ? "Login" : "Sign up"}
                </a>
                {mode === "login" && (
                  <a
                    href="#"
                    className="auth-link"
                    onClick={(e) => { e.preventDefault(); switchMode("forgot"); }}
                  >
                    Forgot password?
                  </a>
                )}
              </div>
            </div>
          </>
        )}
      </form>
      </div>

      <InstallPrompt />

      <footer className="landing-footer">
        <div className="landing-footer-links">
          <Link to="/terms">Terms of Service</Link>
          <Link to="/privacy">Privacy Policy</Link>
        </div>
        <p className="landing-footer-responsible">18+ only. Please gamble responsibly.</p>
      </footer>
    </div>
  );
}
