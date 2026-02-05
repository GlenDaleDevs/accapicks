import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import * as api from "./api/client";
import "./App.css";

import AuthView from "./components/AuthView";
import ErrorBoundary from "./components/ErrorBoundary";
import TopBar from "./components/TopBar";
import GroupsList from "./components/GroupsList";
import GroupDetail from "./components/GroupDetail";
import AccaDetail from "./components/AccaDetail";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [groups, setGroups] = useState([]);
  const [error, setError] = useState("");

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
    if (isLoggedIn) {
      loadGroups();
    }
  }, [isLoggedIn]);

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
      api.setAuthToken(data.access_token);
      setUser(data.user);
      setIsLoggedIn(true);
    } catch (err) {
      throw new Error(err.response?.data?.detail || "Signup failed");
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
        <div className="app-container">
          {!isLoggedIn ? (
            <AuthView
              onLogin={handleLogin}
              onSignup={handleSignup}
              error={error}
            />
          ) : (
            <AppContent
              user={user}
              groups={groups}
              onLogout={handleLogout}
              onCreateGroup={handleCreateGroup}
              onJoinGroup={handleJoinGroup}
              error={error}
            />
          )}
        </div>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

function AppContent({ user, groups, onLogout, onCreateGroup, onJoinGroup, error }) {
  const navigate = useNavigate();

  const handleLogoutWithNav = () => {
    onLogout();
    navigate("/");
  };

  return (
    <div>
      <TopBar user={user} onLogout={handleLogoutWithNav} />
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
          element={<AccaDetail user={user} />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
