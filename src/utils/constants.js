export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const LEAGUE_OPTIONS = [
  { key: "soccer_epl", name: "Premier League" },
  { key: "soccer_spain_la_liga", name: "La Liga" },
  { key: "soccer_germany_bundesliga", name: "Bundesliga" },
  { key: "soccer_italy_serie_a", name: "Serie A" },
  { key: "soccer_france_ligue_one", name: "Ligue 1" },
];

export const LEAGUE_NAME_MAP = Object.fromEntries(
  LEAGUE_OPTIONS.map((l) => [l.key, l.name]),
);
