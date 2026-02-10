import { LEAGUE_NAME_MAP } from "../utils/constants";
import { formatDisplayDate } from "../utils/formatters";
import FixtureCard from "./FixtureCard";

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
                {matches.map((match) => {
                  const fixtureTaken = takenEventIds.has(match.id);
                  const takenBet = takenEventBets[match.id];
                  return (
                    <FixtureCard
                      key={match.id}
                      match={match}
                      fixtureTaken={fixtureTaken}
                      takenBet={takenBet}
                      onPickMatch={onPickMatch}
                      isSubmitting={isSubmitting}
                      oddsFormat={oddsFormat}
                    />
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
