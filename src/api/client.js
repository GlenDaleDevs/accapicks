import axios from "axios";
import { API_URL } from "../utils/constants";
import { showToast } from "../utils/toast";

// Auth token management
export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem("token", token);
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    localStorage.removeItem("token");
    delete axios.defaults.headers.common["Authorization"];
  }
};

export const getStoredToken = () => localStorage.getItem("token");

// Auto-logout on 401, rate limit handling on 429
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Only redirect if we had a token (avoid loop from unauthenticated requests)
      if (localStorage.getItem("token")) {
        localStorage.removeItem("token");
        delete axios.defaults.headers.common["Authorization"];
        window.location.href = "/";
      }
    } else if (error.response?.status === 429) {
      const retryAfter = error.response?.data?.retry_after || error.response?.headers?.["retry-after"];
      const parsed = retryAfter ? parseInt(retryAfter, 10) : null;
      const seconds = parsed && !isNaN(parsed) ? Math.max(1, parsed) : null;
      const message = seconds
        ? `Too many requests. Please try again in ${seconds} seconds.`
        : "Too many requests. Please try again shortly.";
      showToast(message, "warning");
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = async (identifier, password) => {
  const response = await axios.post(`${API_URL}/auth/login`, { identifier, password });
  return response.data;
};

export const signup = async (email, username, password, ageConfirmed) => {
  const response = await axios.post(`${API_URL}/auth/signup`, {
    email,
    username,
    password,
    age_confirmed: ageConfirmed
  });
  return response.data;
};

export const checkUsername = async (username) => {
  const response = await axios.get(`${API_URL}/auth/check-username`, {
    params: { username }
  });
  return response.data;
};

export const verifyEmail = async (email, code) => {
  const response = await axios.post(`${API_URL}/auth/verify-email`, { email, code });
  return response.data;
};

export const resendVerificationCode = async (email) => {
  const response = await axios.post(`${API_URL}/auth/resend-code`, { email });
  return response.data;
};

export const forgotPassword = async (email) => {
  const response = await axios.post(`${API_URL}/auth/forgot-password`, { email });
  return response.data;
};

export const resetPassword = async (email, code, newPassword) => {
  const response = await axios.post(`${API_URL}/auth/reset-password`, {
    email,
    code,
    new_password: newPassword
  });
  return response.data;
};

export const getMe = async () => {
  const response = await axios.get(`${API_URL}/auth/me`);
  return response.data;
};

export const logout = async () => {
  try {
    await axios.post(`${API_URL}/auth/logout`);
  } catch (err) {
    // Fire-and-forget: don't block logout if API call fails
  }
};

// Groups
export const getGroups = async () => {
  const response = await axios.get(`${API_URL}/groups`);
  return response.data;
};

export const getGroup = async (groupId) => {
  const response = await axios.get(`${API_URL}/groups/${groupId}`);
  return response.data;
};

export const updateGroup = async (groupId, settings) => {
  const response = await axios.patch(`${API_URL}/groups/${groupId}`, settings);
  return response.data;
};

export const createGroup = async (name, description) => {
  const response = await axios.post(`${API_URL}/groups`, { name, description });
  return response.data;
};

export const joinGroup = async (inviteCode) => {
  const response = await axios.post(`${API_URL}/groups/join/${inviteCode}`);
  return response.data;
};

export const getGroupMembers = async (groupId) => {
  const response = await axios.get(`${API_URL}/groups/${groupId}/members`);
  return response.data;
};

export const getGroupLeaderboard = async (groupId) => {
  const response = await axios.get(`${API_URL}/groups/${groupId}/leaderboard`);
  return response.data;
};

export const getMemberPicks = async (groupId, userId) => {
  const response = await axios.get(`${API_URL}/groups/${groupId}/members/${userId}/picks`);
  return response.data;
};

export const getGroupAccaStats = async (groupId) => {
  const response = await axios.get(`${API_URL}/groups/${groupId}/acca-stats`);
  return response.data;
};

// Accas
export const getAccasByGroup = async (groupId) => {
  const response = await axios.get(`${API_URL}/groups/${groupId}/accas`);
  return response.data;
};

export const getAccaById = async (accaId) => {
  const response = await axios.get(`${API_URL}/accas/${accaId}`);
  return response.data;
};

export const createAcca = async (groupId, name, matchDates, leagues, betType) => {
  const response = await axios.post(`${API_URL}/accas`, {
    group_id: groupId,
    name,
    match_dates: matchDates,
    leagues,
    bet_type: betType,
  });
  return response.data;
};

export const compareBookmakers = async (accaId) => {
  const response = await axios.get(`${API_URL}/accas/${accaId}/compare-bookmakers`);
  return response.data;
};

// Bets
export const createBet = async (accaId, description, odds, structuredData = {}) => {
  const response = await axios.post(`${API_URL}/bets`, {
    acca_id: accaId,
    description,
    odds,
    ...structuredData,
  });
  return response.data;
};

export const deleteBet = async (betId) => {
  const response = await axios.delete(`${API_URL}/bets/${betId}`);
  return response.data;
};

// Odds
export const getMatches = async (sport = "soccer_epl") => {
  const response = await axios.get(`${API_URL}/odds/matches?sport=${sport}`);
  return response.data;
};

export const getFilteredMatches = async (leagues, dateFrom, dateTo) => {
  const response = await axios.get(`${API_URL}/odds/matches/filtered`, {
    params: {
      leagues: leagues.join(","),
      date_from: dateFrom,
      date_to: dateTo,
    },
  });
  return response.data;
};

export const getFavourableMatchups = async () => {
  const response = await axios.get(`${API_URL}/odds/favourable`);
  return response.data;
};

export const getBttsOdds =async (eventId, sportKey) => {
  const response = await axios.get(`${API_URL}/odds/matches/${eventId}/btts`, {
    params: { sport_key: sportKey },
  });
  return response.data;
};

// Affiliate
export const getBookmakerLinks = async () => {
  const response = await axios.get(`${API_URL}/affiliate/links`);
  return response.data;
};

export const trackBookmakerClick = async (bookmakerKey, accaId, source) => {
  try {
    await axios.post(`${API_URL}/affiliate/clicks`, {
      bookmaker_key: bookmakerKey,
      acca_id: accaId,
      source,
    });
  } catch (err) {
    // Fire-and-forget: catch silently so navigation is never blocked
  }
};

export const changePassword = async (currentPassword, newPassword) => {
  const response = await axios.put(`${API_URL}/auth/change-password`, {
    current_password: currentPassword,
    new_password: newPassword
  });
  return response.data;
};

export const deleteAccount = async (password) => {
  const response = await axios.post(`${API_URL}/auth/delete-account`, { password });
  return response.data;
};

export const leaveGroup = async (groupId) => {
  const response = await axios.delete(`${API_URL}/groups/${groupId}/leave`);
  return response.data;
};

export const deleteAcca = async (accaId) => {
  const response = await axios.delete(`${API_URL}/accas/${accaId}`);
  return response.data;
};

export const removeMember = async (groupId, userId) => {
  const response = await axios.delete(`${API_URL}/groups/${groupId}/members/${userId}`);
  return response.data;
};

// Push Notifications
export const getVapidKey = async () => {
  const response = await axios.get(`${API_URL}/notifications/vapid-key`);
  return response.data;
};

export const subscribePush = async (subscription) => {
  const response = await axios.post(`${API_URL}/notifications/subscribe`, { subscription });
  return response.data;
};

export const unsubscribePush = async (endpoint) => {
  const response = await axios.delete(`${API_URL}/notifications/unsubscribe`, {
    data: { endpoint },
  });
  return response.data;
};
