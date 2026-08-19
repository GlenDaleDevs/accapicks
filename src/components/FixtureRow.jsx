// The match row and its last-five trackers. Kept apart from FixturesList so
// that file stays about fetching a week and choosing what to show.

import { MoreBets, OddsChip } from "./FixtureOdds";

function kickoffTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

// Dot meanings per tracker: [outcome letter, what it means]
const LEGENDS = {
  results: [["W", "Won"], ["D", "Drew"], ["L", "Lost"]],
  btts: [["Y", "Both scored"], ["N", "Not both"]],
  over25: [["Y", "3+ goals"], ["N", "2 or fewer"]],
};

function meanings(tracker) {
  return Object.fromEntries(LEGENDS[tracker]);
}

// Oldest to newest, so the rightmost circle is the most recent match.
function Form({ marks, tracker, emptyLabel }) {
  // Early season a club can have no record at this venue at all — say so
  // rather than rendering nothing, which reads as a broken row.
  if (!marks?.length) {
    return <span className="fixture-form-empty" title={emptyLabel}>–</span>;
  }
  const title = meanings(tracker);
  return (
    <span className="fixture-form">
      {marks.map((mark, i) => (
        <span
          key={i}
          className={`form-dot form-${mark.toLowerCase()}`}
          title={title[mark]}
        />
      ))}
      <span className="sr-only">
        {marks.map((mark) => title[mark]).join(", ")}
      </span>
    </span>
  );
}

// In "venue" mode each side shows its own half of the record — the home team's
// home games, the away team's away games — a different last five from overall.
function Team({ name, stats, tracker, venue, side, chip }) {
  const byVenue = venue === "venue";
  const split = stats?.[byVenue ? side : "overall"];
  return (
    <div className="fixture-team">
      {stats?.pos ? <span className="fixture-pos">{stats.pos}</span> : null}
      <span className="fixture-name">{name}</span>
      {chip}
      <Form
        marks={split?.[tracker]}
        tracker={tracker}
        emptyLabel={byVenue ? `No ${side} games played yet` : "No games played yet"}
      />
    </div>
  );
}

export function MatchRow({
  match, teams, tracker, venue,
  canPick = false, takenBy, onPick, submitting = false, oddsFormat = "decimal",
}) {
  const shared = { tracker, venue };
  const mid = match.played
    ? `${match.home_goals}–${match.away_goals}`
    : kickoffTime(match.kickoff);
  // Odds render whenever the join found a price — greyed out when the fixture
  // can't be picked (taken, already picked, locked) — home under the home
  // name, away under the away name, the draw under the kickoff time.
  const odds = !match.played && match.odds ? match.odds : null;
  const chip = (value, type, label) => (
    <OddsChip
      label={label}
      value={value}
      disabled={!canPick || submitting}
      onClick={() => onPick(odds, type)}
      oddsFormat={oddsFormat}
    />
  );
  return (
    <li className="fixture-row">
      <Team name={match.home} stats={teams[match.home]} side="home" {...shared}
        chip={odds && chip(odds.home_odds, "home")} />
      <div className="fixture-mid-col">
        <span className={`fixture-mid${match.played ? " fixture-score" : ""}`}>{mid}</span>
        {odds && chip(odds.draw_odds, "draw", "Draw")}
      </div>
      <Team name={match.away} stats={teams[match.away]} side="away" {...shared}
        chip={odds && chip(odds.away_odds, "away")} />
      {odds && canPick && (
        <MoreBets odds={odds} onPick={onPick} submitting={submitting} oddsFormat={oddsFormat} />
      )}
      {takenBy && <span className="fixture-taken-note">Picked by {takenBy}</span>}
    </li>
  );
}

// Dots alone don't say which end is the latest game, and nobody should have to
// guess from the data.
export function FormKey({ tracker, venue }) {
  return (
    <p className="fixture-key">
      {LEGENDS[tracker].map(([mark, label]) => (
        <span key={mark} className="fixture-key-item">
          <span className={`form-dot form-${mark.toLowerCase()}`} />
          {label}
        </span>
      ))}
      <span className="fixture-key-note">
        {venue === "venue" ? "Last 5 home/away" : "Last 5"}, most recent on the right
      </span>
    </p>
  );
}
