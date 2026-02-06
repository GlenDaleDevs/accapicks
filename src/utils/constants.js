export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const LEAGUE_OPTIONS = [
  { key: "soccer_epl", name: "Premier League" },
  { key: "soccer_efl_champ", name: "Championship" },
  { key: "soccer_england_league1", name: "League One" },
  { key: "soccer_england_league2", name: "League Two" },
  { key: "soccer_spain_la_liga", name: "La Liga" },
  { key: "soccer_germany_bundesliga", name: "Bundesliga" },
  { key: "soccer_italy_serie_a", name: "Serie A" },
  { key: "soccer_france_ligue_one", name: "Ligue 1" },
];

export const LEAGUE_NAME_MAP = Object.fromEntries(
  LEAGUE_OPTIONS.map((l) => [l.key, l.name]),
);

export const BOOKMAKER_DISPLAY_NAMES = {
  betfair_ex_uk: "Betfair Exchange",
  betfair_sb_uk: "Betfair",
  unibet_uk: "Unibet",
  ladbrokes_uk: "Ladbrokes",
  livescorebet_eu: "LiveScore Bet",
  marathonbet: "Marathon Bet",
  virginbet: "Virgin Bet",
  betuk: "Bet UK",
  mrgreen: "Mr Green",
  supabets: "Supa Bets",
  gentingbet: "Genting Bet",
  tonybet: "Tony Bet",
  nordicbet: "Nordic Bet",
  skybet: "Sky Bet",
  betvictor: "BetVictor",
  boylesports: "BoyleSports",
  paddypower: "Paddy Power",
  williamhill: "William Hill",
  livescorebet: "LiveScore Bet",
};
