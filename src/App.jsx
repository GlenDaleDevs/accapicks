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
  // consume once the user is signed in.
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const rawInvite = urlParams.get("invite");
    const inviteCode = rawInvite
      ? rawInvite.trim().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6)
      : null;
    if (inviteCode) {
      localStorage.setItem("pendingInvite", JSON.stringify({
        code: inviteCode,
        savedAt: Date.now(),
      }));
    }
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
                    />
                    <ComplianceFooter />
                  </div>
                )
              }
            />
          </Routes>
          <CookieConsent />
        </MotionConfig>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
