import { useState } from "react";
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
  const [expandedMatches, setExpandedMatches] = useState(new Set());

  const toggleExpanded = (matchId) => {
    setExpandedMatches(prev => {
      const next = new Set(prev);
      if (next.has(matchId)) next.delete(matchId);
      else next.add(matchId);
      return next;
    });
  };

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
                      {/* More bets toggle - only if match has BTTS or totals odds */}
                      {(match.btts_yes || match.over_2_5) && !fixtureTaken && (
                        <>
                          <button
                            className="fixture-more-bets-toggle"
                            onClick={() => toggleExpanded(match.id)}
                          >
                            {expandedMatches.has(match.id) ? "Less bets" : "More bets"}
                          </button>
                          {expandedMatches.has(match.id) && (
                            <div className="fixture-extra-odds">
                              {match.btts_yes && (
                                <div className="fixture-extra-odds-row">
                                  <button
                                    className="fixture-odds-btn"
                                    onClick={() => onPickMatch(match, "btts_yes")}
                                    disabled={isSubmitting}
                                  >
                                    <div className="fixture-odds-label">BTTS Yes</div>
                                    <div className="fixture-odds-value">{formatOdds(match.btts_yes, oddsFormat)}</div>
                                  </button>
                                  <button
                                    className="fixture-odds-btn"
                                    onClick={() => onPickMatch(match, "btts_no")}
                                    disabled={isSubmitting}
                                  >
                                    <div className="fixture-odds-label">BTTS No</div>
                                    <div className="fixture-odds-value">{formatOdds(match.btts_no, oddsFormat)}</div>
                                  </button>
                                </div>
                              )}
                              {match.over_2_5 && (
                                <div className="fixture-extra-odds-row">
                                  <button
                                    className="fixture-odds-btn"
                                    onClick={() => onPickMatch(match, "over_2_5")}
                                    disabled={isSubmitting}
                                  >
                                    <div className="fixture-odds-label">Over {match.totals_line}</div>
                                    <div className="fixture-odds-value">{formatOdds(match.over_2_5, oddsFormat)}</div>
                                  </button>
                                  <button
                                    className="fixture-odds-btn"
                                    onClick={() => onPickMatch(match, "under_2_5")}
                                    disabled={isSubmitting}
                                  >
                                    <div className="fixture-odds-label">Under {match.totals_line}</div>
                                    <div className="fixture-odds-value">{formatOdds(match.under_2_5, oddsFormat)}</div>
                                  </button>
                                </div>
                              )}
                            </div>
                          )}
                        </>
                      )}
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
