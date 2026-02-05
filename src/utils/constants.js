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

export const BOOKMAKER_URLS = {
  bet365: "https://www.bet365.com",
  williamhill: "https://www.williamhill.com",
  paddypower: "https://www.paddypower.com",
  betfair: "https://www.betfair.com",
  unibet_uk: "https://www.unibet.co.uk",
  betway: "https://www.betway.com",
  "888sport": "https://www.888sport.com",
  ladbrokes_uk: "https://www.ladbrokes.com",
  coral: "https://www.coral.co.uk",
  skybet: "https://www.skybet.com",
  betvictor: "https://www.betvictor.com",
  betfred: "https://www.betfred.com",
  boylesports: "https://www.boylesports.com",
  matchbook: "https://www.matchbook.com",
  betfair_ex_uk: "https://www.betfair.com/exchange",
  livescorebet_eu: "https://www.livescorebet.com",
  sport888: "https://www.888sport.com",
  marathonbet: "https://www.marathonbet.co.uk",
  virginbet: "https://www.virginbet.com",
  livescorebet: "https://www.livescorebet.com",
  betuk: "https://www.bet.co.uk",
  betsson: "https://www.betsson.com",
  mrgreen: "https://www.mrgreen.com",
  supabets: "https://www.supabets.co.uk",
  spreadex: "https://sports.spreadex.com",
  betdaq: "https://www.betdaq.com",
  gentingbet: "https://www.gentingbet.co.uk",
  tonybet: "https://www.tonybet.com",
  nordicbet: "https://www.nordicbet.com",
};
