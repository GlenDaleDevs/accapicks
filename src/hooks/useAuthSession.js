import { useEffect, useState } from "react";
import * as api from "../api/client";
import { clearLastGroupId } from "../utils/routes";

// Session state and every auth flow handler, lifted out of App.jsx. The
// handlers throw a plain Error with the API's message so form components can
// show it without knowing about axios.
export default function useAuthSession() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [pendingVerificationEmail, setPendingVerificationEmail] = useState("");

  useEffect(() => {
    const token = api.getStoredToken();
    if (token) {
      api.setAuthToken(token);
      api.getMe().then((userData) => {
        setUser(userData);
        setIsLoggedIn(true);
      }).catch(() => {
        api.setAuthToken(null);
        setIsLoggedIn(false);
      });
    }

    // Sync logout across tabs
    const handleStorageChange = (e) => {
      if (e.key === "token" && !e.newValue) {
        api.setAuthToken(null);
        setUser(null);
        setIsLoggedIn(false);
        clearLastGroupId();
      }
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const handleLogin = async (identifier, password) => {
    setError("");
    try {
      const data = await api.login(identifier, password);
      api.setAuthToken(data.access_token);
      setUser(data.user);
      setIsLoggedIn(true);
    } catch (err) {
      throw new Error(err.response?.data?.detail || "Login failed");
    }
  };

  const handleSignup = async (email, username, password, ageConfirmed) => {
    setError("");
    try {
      const data = await api.signup(email, username, password, ageConfirmed);
      if (data.requires_verification) {
        setPendingVerificationEmail(email);
      }
    } catch (err) {
      throw new Error(err.response?.data?.detail || "Signup failed");
    }
  };

  const handleVerify = async (email, code) => {
    setError("");
    try {
      const data = await api.verifyEmail(email, code);
      api.setAuthToken(data.access_token);
      setUser(data.user);
      setIsLoggedIn(true);
      setPendingVerificationEmail("");
    } catch (err) {
      throw new Error(err.response?.data?.detail || "Verification failed");
    }
  };

  const handleResendCode = async (email) => {
    setError("");
    try {
      await api.resendVerificationCode(email);
    } catch (err) {
      throw new Error(err.response?.data?.detail || "Failed to resend code");
    }
  };

  const handleForgotPassword = async (email) => {
    setError("");
    try {
      await api.forgotPassword(email);
    } catch (err) {
      throw new Error(err.response?.data?.detail || "Failed to send reset code");
    }
  };

  const handleResetPassword = async (email, code, newPassword) => {
    setError("");
    try {
      await api.resetPassword(email, code, newPassword);
    } catch (err) {
      throw new Error(err.response?.data?.detail || "Password reset failed");
    }
  };

  const handleLogout = async () => {
    // Try the backend logout (blacklists the token) but never let a failed
    // request strand a live session on the device — clear locally regardless.
    try {
      await api.logout();
    } finally {
      api.setAuthToken(null);
      setUser(null);
      setIsLoggedIn(false);
      // Otherwise the next user on this device gets redirected into this user's group
      clearLastGroupId();
      window.history.replaceState({}, "", "/");
    }
  };

  return {
    isLoggedIn, user, error, pendingVerificationEmail,
    handleLogin, handleSignup, handleVerify, handleResendCode,
    handleForgotPassword, handleResetPassword, handleLogout,
  };
}
