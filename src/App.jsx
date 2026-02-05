import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, Link } from "react-router-dom";
import * as api from "./api/client";
import "./App.css";

import AuthView from "./components/AuthView";
import ErrorBoundary from "./components/ErrorBoundary";
import TopBar from "./components/TopBar";
import GroupsList from "./components/GroupsList";
import GroupDetail from "./components/GroupDetail";
import AccaDetail from "./components/AccaDetail";
import TermsOfService from "./components/TermsOfService";
import PrivacyPolicy from "./components/PrivacyPolicy";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [groups, setGroups] = useState([]);
  const [error, setError] = useState("");
  const [pendingVerificationEmail, setPendingVerificationEmail] = useState("");
  const [oddsFormat, setOddsFormat] = useState(() => {
    return localStorage.getItem("oddsFormat") || "decimal";
  });

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
            alert(err.message || 'Failed to join group from invite link');
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
    try {
      const data = await api.getGroups();
      setGroups(data);
    } catch (err) {
      console.error("Error loading groups:", err);
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
      alert("Successfully joined group!");
    } catch (err) {
      throw new Error(
        err.response?.data?.detail || "Failed to join group",
      );
    }
  };

  return (
    <BrowserRouter>
      <ErrorBoundary>
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
                    error={error}
                    pendingVerificationEmail={pendingVerificationEmail}
                  />
                ) : (
                  <AppContent
                    user={user}
                    groups={groups}
                    onLogout={handleLogout}
                    onCreateGroup={handleCreateGroup}
                    onJoinGroup={handleJoinGroup}
                    error={error}
                    oddsFormat={oddsFormat}
                    setOddsFormat={setOddsFormat}
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
      </ErrorBoundary>
    </BrowserRouter>
  );
}

function AppContent({ user, groups, onLogout, onCreateGroup, onJoinGroup, error, oddsFormat, setOddsFormat }) {
  const navigate = useNavigate();

  const handleLogoutWithNav = () => {
    onLogout();
    navigate("/");
  };

  return (
    <div>
      <TopBar user={user} onLogout={handleLogoutWithNav} oddsFormat={oddsFormat} setOddsFormat={setOddsFormat} />
      <Routes>
        <Route
          path="/"
          element={
            <GroupsList
              groups={groups}
              onCreateGroup={onCreateGroup}
              onJoinGroup={onJoinGroup}
              error={error}
            />
          }
        />
        <Route
          path="/groups/:groupId"
          element={<GroupDetail user={user} />}
        />
        <Route
          path="/groups/:groupId/accas/:accaId"
          element={<AccaDetail user={user} oddsFormat={oddsFormat} />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
