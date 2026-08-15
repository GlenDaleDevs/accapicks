// Builds the human description and odds for a pick. Extracted from AccaDetail
// so the pick modal and any future entry point stay in step.
export function buildPick(match, pickType) {
  switch (pickType) {
    case "home":
      return { description: `${match.home_team} to win`, odds: String(match.home_odds) };
    case "away":
      return { description: `${match.away_team} to win`, odds: String(match.away_odds) };
    case "draw":
      return { description: `Draw - ${match.home_team} vs ${match.away_team}`, odds: String(match.draw_odds) };
    case "btts_yes":
      return { description: `BTTS Yes - ${match.home_team} vs ${match.away_team}`, odds: String(match.btts_yes) };
    case "btts_no":
      return { description: `BTTS No - ${match.home_team} vs ${match.away_team}`, odds: String(match.btts_no) };
    case "over_2_5":
      return { description: `Over ${match.totals_line} Goals - ${match.home_team} vs ${match.away_team}`, odds: String(match.over_2_5) };
    case "under_2_5":
      return { description: `Under ${match.totals_line} Goals - ${match.home_team} vs ${match.away_team}`, odds: String(match.under_2_5) };
    default:
      return null;
  }
}

export function buildStructuredData(match, pickType) {
  return {
    event_id: match.id,
    home_team: match.home_team,
    away_team: match.away_team,
    pick_type: pickType,
    sport_key: match.league,
    commence_time: match.commence_time,
  };
}
