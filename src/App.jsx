import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { MotionConfig } from "framer-motion";
import PageTransition from "./components/PageTransition";
import * as api from "./api/client";
import "./App.css";
import "./responsive.css";

import AuthView from "./components/AuthView";
import ErrorBoundary from "./components/ErrorBoundary";
import TermsOfService from "./components/TermsOfService";
import PrivacyPolicy from "./components/PrivacyPolicy";
import CookieConsent from "./components/CookieConsent";
import PolicyUpdateBanner from "./components/PolicyUpdateBanner";
import ToastContainer from "./components/ToastContainer";
import AppRoutes from "./AppRoutes";
import ComplianceFooter from "./components/ComplianceFooter";
import { AppContext } from "./context/AppContext";
import useAuthSession from "./hooks/useAuthSession";
import useGroups from "./hooks/useGroups";
import usePwaUpdate from "./hooks/usePwaUpdate";

// Composition only — session, groups and the PWA update cycle live in hooks.
function App() {
  const {
    isLoggedIn, user, error, pendingVerificationEmail,
    handleLogin, handleSignup, handleVerify, handleResendCode,
    handleForgotPassword, handleResetPassword, handleLogout,
  } = useAuthSession();
  const { groups, loadingGroups, loadGroups, handleCreateGroup, handleJoinGroup } =
    useGroups(isLoggedIn);
  usePwaUpdate();

  const [oddsFormat, setOddsFormat] = useState(() => {
    const stored = localStorage.getItem("oddsFormat");
    return ["decimal", "fractional"].includes(stored) ? stored : "decimal";
  });
  const [bookmakerLinks, setBookmakerLinks] = useState({});
  // {code, name, member_count} when a live invite is parked — auth screen context
  const [invitePreview, setInvitePreview] = useState(null);

  // Hold splash for 1.6s then fade out and remove
  useEffect(() => {
    const splash = document.getElementById("splash");
    if (!splash) return;
    const fade = setTimeout(() => { splash.style.opacity = "0"; }, 1600);
    const remove = setTimeout(() => splash.remove(), 2100);
    return () => { clearTimeout(fade); clearTimeout(remove); };
  }, []);

  useEffect(() => {
    api.getBookmakerLinks()
      .then(setBookmakerLinks)
      .catch((err) => console.error("Failed to fetch bookmaker links:", err));
  }, []);

  // An invite link can arrive before login — park the code for useGroups to
  // consume once the user is signed in, and resolve the group's name so the
  // auth screen can say where the invite leads. A previously parked (and
  // unexpired) invite gets the same treatment, so closing and reopening the
  // app doesn't lose the context.
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const rawInvite = urlParams.get("invite");
    let inviteCode = rawInvite
      ? rawInvite.trim().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6)
      : null;
    if (inviteCode) {
      localStorage.setItem("pendingInvite", JSON.stringify({
        code: inviteCode,
        savedAt: Date.now(),
      }));
    } else {
      try {
        const parked = JSON.parse(localStorage.getItem("pendingInvite"));
        if (parked && Date.now() - parked.savedAt < 24 * 60 * 60 * 1000) {
          inviteCode = parked.code;
        }
      } catch {
        // legacy or absent — no context to show
      }
    }
    if (!inviteCode) return;
    let cancelled = false;
    api.getInvitePreview(inviteCode)
      .then((data) => {
        if (!cancelled) setInvitePreview({ code: inviteCode, ...data });
      })
      .catch(() => {
        // Dead code: drop it so signup isn't followed by a failed-join toast
        if (!cancelled) localStorage.removeItem("pendingInvite");
      });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    localStorage.setItem("oddsFormat", oddsFormat);
  }, [oddsFormat]);

  const appValue = {
    user,
    groups,
    loadingGroups,
    error,
    oddsFormat,
    setOddsFormat,
    bookmakerLinks,
    onCreateGroup: handleCreateGroup,
    onJoinGroup: handleJoinGroup,
    onRefreshGroups: loadGroups,
    onLogout: handleLogout,
  };

  return (
    <BrowserRouter>
      <ErrorBoundary>
        <MotionConfig reducedMotion="user">
          <ToastContainer />
          <Routes>
            <Route path="/terms" element={<PageTransition><TermsOfService /></PageTransition>} />
            <Route path="/privacy" element={<PageTransition><PrivacyPolicy /></PageTransition>} />
            <Route
              path="/*"
              element={
                isLoggedIn ? (
                  <AppContext.Provider value={appValue}>
                    <AppRoutes />
                  </AppContext.Provider>
                ) : (
                  <div className="app-container">
                    <AuthView
                      onLogin={handleLogin}
                      onSignup={handleSignup}
                      onVerify={handleVerify}
                      onResendCode={handleResendCode}
                      onForgotPassword={handleForgotPassword}
                      onResetPassword={handleResetPassword}
                      error={error}
                      pendingVerificationEmail={pendingVerificationEmail}
                      invitePreview={invitePreview}
                    />
                    <ComplianceFooter />
                  </div>
                )
              }
            />
          </Routes>
          <CookieConsent />
          <PolicyUpdateBanner isLoggedIn={isLoggedIn} />
        </MotionConfig>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
