import { LEAGUE_NAME_MAP } from "../utils/constants";
import { formatDisplayDate, formatOdds } from "../utils/formatters";

export default function FixtureGrid({
  acca,
  filteredMatches,
  loadingFilteredMatches,
  fixtureLeague,
  onPickMatch,
  onSelectLeague,
  onCancel,
  error,
  oddsFormat = "decimal",
  isSubmitting = false,
}) {
  // Build set of taken event_ids (fixture-level exclusion)
  const takenEventIds = new Set(
    (acca?.bets || []).filter((b) => b.event_id).map((b) => b.event_id)
  );
  // Map event_id to the bet that took it (for banner display)
  const takenEventBets = {};
  (acca?.bets || []).forEach((b) => {
    if (b.event_id) takenEventBets[b.event_id] = b;
  });

  // League selector when multiple leagues and none selected yet
  if (!fixtureLeague && acca.leagues && acca.leagues.length > 1) {
    return (
      <div className="form-panel">
        <h3 className="form-panel-title">Select League</h3>
        {acca.leagues.map((key) => (
          <button
            key={key}
            className="league-select-btn"
            onClick={() => onSelectLeague(key)}
          >
            {LEAGUE_NAME_MAP[key] || key}
          </button>
        ))}
        <button className="btn btn-ghost mt-12" onClick={onCancel}>
          Cancel
        </button>
      </div>
    );
  }

  // Fixture grid with matches
  if (loadingFilteredMatches) {
    return (
      <div className="form-panel">
        <h3 className="form-panel-title">
          {LEAGUE_NAME_MAP[fixtureLeague] || fixtureLeague} - Pick a Match
        </h3>
        <p className="text-muted">Loading fixtures...</p>
      </div>
    );
  }

  const byDate = {};
  filteredMatches.forEach((m) => {
    const date = m.commence_time.slice(0, 10);
    if (!byDate[date]) byDate[date] = [];
    byDate[date].push(m);
  });

  return (
    <div className="form-panel">
      <h3 className="form-panel-title">
        {LEAGUE_NAME_MAP[fixtureLeague] || fixtureLeague} - Pick a Match
      </h3>

      {error && <div className="alert-error">{error}</div>}

      {filteredMatches.length === 0 ? (
        <p className="text-muted">
          No fixtures found for the selected dates and leagues.
        </p>
      ) : (
        <div>
          {Object.entries(byDate)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([date, matches]) => (
              <div key={date} className="mb-16">
                <h4 className="fixture-date-header">{formatDisplayDate(date)}</h4>
                {matches.map((match, idx) => {
                  const kickoff = new Date(match.commence_time).toLocaleTimeString(
                    "en-GB",
                    { hour: "2-digit", minute: "2-digit" },
                  );
                  const fixtureTaken = takenEventIds.has(match.id);
                  const takenBet = takenEventBets[match.id];
                  return (
                    <div key={idx} className={`fixture-card${fixtureTaken ? " fixture-card-taken" : ""}`}>
                      {fixtureTaken && takenBet && (
                        <div className="fixture-taken-banner">
                          Picked by {takenBet.username}: {takenBet.description}
                        </div>
                      )}
                      <div className="fixture-teams-row">
                        <span className="fixture-team">{match.home_team}</span>
                        <span className="fixture-kickoff">{kickoff}</span>
                        <span className="fixture-team fixture-team-away">
                          {match.away_team}
                        </span>
                      </div>
                      <div className="fixture-odds-row">
                        <button
                          className={`fixture-odds-btn${fixtureTaken ? " fixture-odds-taken" : ""}`}
                          onClick={() => !fixtureTaken && onPickMatch(match, "home")}
                          disabled={fixtureTaken || isSubmitting}
                        >
                          <div className="fixture-odds-label">
                            {fixtureTaken ? "Taken" : "Home"}
                          </div>
                          <div className={fixtureTaken ? "fixture-odds-value-taken" : "fixture-odds-value"}>
                            {formatOdds(match.home_odds, oddsFormat)}
                          </div>
                        </button>
                        <button
                          className={`fixture-odds-btn${fixtureTaken ? " fixture-odds-taken" : ""}`}
                          onClick={() => !fixtureTaken && onPickMatch(match, "draw")}
                          disabled={fixtureTaken || isSubmitting}
                        >
                          <div className="fixture-odds-label">
                            {fixtureTaken ? "Taken" : "Draw"}
                          </div>
                          <div className={fixtureTaken ? "fixture-odds-value-taken" : "fixture-odds-value"}>
                            {formatOdds(match.draw_odds, oddsFormat)}
                          </div>
                        </button>
                        <button
                          className={`fixture-odds-btn${fixtureTaken ? " fixture-odds-taken" : ""}`}
                          onClick={() => !fixtureTaken && onPickMatch(match, "away")}
                          disabled={fixtureTaken || isSubmitting}
                        >
                          <div className="fixture-odds-label">
                            {fixtureTaken ? "Taken" : "Away"}
                          </div>
                          <div className={fixtureTaken ? "fixture-odds-value-taken" : "fixture-odds-value"}>
                            {formatOdds(match.away_odds, oddsFormat)}
                          </div>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
        </div>
      )}

      <button className="btn btn-ghost mt-12" onClick={onCancel}>
        Cancel
      </button>
    </div>
  );
}
