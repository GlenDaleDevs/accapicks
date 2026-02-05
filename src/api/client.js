import axios from "axios";
import { API_URL } from "../utils/constants";

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

// Auto-logout on 401
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      delete axios.defaults.headers.common["Authorization"];
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = async (identifier, password) => {
  const response = await axios.post(`${API_URL}/auth/login`, { identifier, password });
  return response.data;
};

export const signup = async (email, username, password) => {
  const response = await axios.post(`${API_URL}/auth/signup`, { email, username, password });
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

export const getMe = async () => {
  const response = await axios.get(`${API_URL}/auth/me`);
  return response.data;
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
export const createBet = async (accaId, description, odds) => {
  const response = await axios.post(`${API_URL}/bets`, {
    acca_id: accaId,
    description,
    odds,
  });
  return response.data;
};

export const deleteBet = async (betId) => {
  const response = await axios.delete(`${API_URL}/bets/${betId}`);
  return response.data;
};

export const updateBetResult = async (betId, result) => {
  const response = await axios.put(`${API_URL}/bets/${betId}/result`, { result });
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
