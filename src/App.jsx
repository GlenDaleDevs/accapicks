import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, Link } from "react-router-dom";
import * as api from "./api/client";
import "./App.css";
import "./responsive.css";

import AuthView from "./components/AuthView";
import ErrorBoundary from "./components/ErrorBoundary";
import TopBar from "./components/TopBar";
import GroupsList from "./components/GroupsList";
import GroupDetail from "./components/GroupDetail";
import AccaDetail from "./components/AccaDetail";
import UserSettings from "./components/UserSettings";
import TermsOfService from "./components/TermsOfService";
import PrivacyPolicy from "./components/PrivacyPolicy";
import CookieConsent from "./components/CookieConsent";
import ToastContainer from "./components/ToastContainer";
import { showToast } from "./utils/toast";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [groups, setGroups] = useState([]);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [error, setError] = useState("");
  const [pendingVerificationEmail, setPendingVerificationEmail] = useState("");
  const [oddsFormat, setOddsFormat] = useState(() => {
    return localStorage.getItem("oddsFormat") || "decimal";
  });
  const [bookmakerLinks, setBookmakerLinks] = useState({});

  useEffect(() => {
    const token = api.getStoredToken();
    if (token) {
      api.setAuthToken(token);
      api.getMe().then(userData => {
        setUser(userData);
        setIsLoggedIn(true);
      }).catch(() => {
        api.setAuthToken(null);
        setIsLoggedIn(false);
      });
    }
  }, []);

  useEffect(() => {
    const fetchBookmakerLinks = async () => {
      try {
        const links = await api.getBookmakerLinks();
        setBookmakerLinks(links);
      } catch (err) {
        console.error("Failed to fetch bookmaker links:", err);
      }
    };
    fetchBookmakerLinks();
  }, []);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const inviteCode = urlParams.get('invite');
    if (inviteCode) {
      localStorage.setItem('pendingInvite', inviteCode);
    }
  }, []);

  useEffect(() => {
    if (isLoggedIn) {
      loadGroups();
    }
  }, [isLoggedIn]);

  useEffect(() => {
    if (isLoggedIn) {
      const pendingInvite = localStorage.getItem('pendingInvite');
      if (pendingInvite) {
        handleJoinGroup(pendingInvite)
          .catch(err => {
            console.error('Auto-join failed:', err);
            showToast(err.message || 'Failed to join group from invite link', 'error');
          })
          .finally(() => {
            localStorage.removeItem('pendingInvite');
            window.history.replaceState({}, '', window.location.pathname);
          });
      }
    }
  }, [isLoggedIn]);

  useEffect(() => {
    localStorage.setItem("oddsFormat", oddsFormat);
  }, [oddsFormat]);

  const loadGroups = async () => {
    setLoadingGroups(true);
    try {
      const data = await api.getGroups();
      setGroups(data);
    } catch (err) {
      console.error("Error loading groups:", err);
    } finally {
      setLoadingGroups(false);
    }
  };

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

  const handleSignup = async (email, username, password) => {
    setError("");
    try {
      const data = await api.signup(email, username, password);
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

  const handleLogout = () => {
    api.setAuthToken(null);
    setUser(null);
    setIsLoggedIn(false);
    setGroups([]);
  };

  const handleCreateGroup = async (name, description) => {
    try {
      await api.createGroup(name, description);
      loadGroups();
    } catch (err) {
      throw new Error(
        err.response?.data?.detail || "Failed to create group",
      );
    }
  };

  const handleJoinGroup = async (inviteCode) => {
    try {
      await api.joinGroup(inviteCode);
      loadGroups();
      showToast("Successfully joined group!", "success");
    } catch (err) {
      throw new Error(
        err.response?.data?.detail || "Failed to join group",
      );
    }
  };

  return (
    <BrowserRouter>
      <ErrorBoundary>
        <ToastContainer />
        <Routes>
          <Route path="/terms" element={<TermsOfService />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route
            path="/*"
            element={
              <div className="app-container">
                {!isLoggedIn ? (
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
                ) : (
                  <AppContent
                    user={user}
                    groups={groups}
                    loadingGroups={loadingGroups}
                    onLogout={handleLogout}
                    onCreateGroup={handleCreateGroup}
                    onJoinGroup={handleJoinGroup}
                    onRefreshGroups={loadGroups}
                    error={error}
                    oddsFormat={oddsFormat}
                    setOddsFormat={setOddsFormat}
                    bookmakerLinks={bookmakerLinks}
                  />
                )}
                <footer className="responsible-gambling-footer">
                  18+ only | Please gamble responsibly | <a href="https://www.begambleaware.org/" target="_blank" rel="noopener noreferrer">BeGambleAware.org</a>
                  <br />
                  <Link to="/terms">Terms of Service</Link> | <Link to="/privacy">Privacy Policy</Link>
                </footer>
              </div>
            }
          />
        </Routes>
        <CookieConsent />
      </ErrorBoundary>
    </BrowserRouter>
  );
}

function AppContent({ user, groups, loadingGroups, onLogout, onCreateGroup, onJoinGroup, onRefreshGroups, error, oddsFormat, setOddsFormat, bookmakerLinks }) {
  const navigate = useNavigate();

  const handleLogoutWithNav = () => {
    onLogout();
    navigate("/");
  };

  return (
    <div>
      <TopBar user={user} />
      <Routes>
        <Route
          path="/"
          element={
            <GroupsList
              groups={groups}
              loading={loadingGroups}
              onCreateGroup={onCreateGroup}
              onJoinGroup={onJoinGroup}
              onLogout={handleLogoutWithNav}
              error={error}
            />
          }
        />
        <Route
          path="/groups/:groupId"
          element={<GroupDetail user={user} onRefreshGroups={onRefreshGroups} />}
        />
        <Route
          path="/groups/:groupId/accas/:accaId"
          element={<AccaDetail user={user} oddsFormat={oddsFormat} bookmakerLinks={bookmakerLinks} />}
        />
        <Route
          path="/settings"
          element={<UserSettings user={user} oddsFormat={oddsFormat} setOddsFormat={setOddsFormat} onLogout={handleLogoutWithNav} />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
