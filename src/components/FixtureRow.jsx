// The match row and its last-five trackers. Kept apart from FixturesList so
// that file stays about fetching a week and choosing what to show.

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
function Form({ marks, tracker }) {
  if (!marks?.length) return null;
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

function Team({ name, stats, tracker }) {
  return (
    <div className="fixture-team">
      {stats?.pos ? <span className="fixture-pos">{stats.pos}</span> : null}
      <span className="fixture-name">{name}</span>
      <Form marks={stats?.[tracker]} tracker={tracker} />
    </div>
  );
}

export function MatchRow({ match, teams, tracker }) {
  return (
    <li className="fixture-row">
      <Team name={match.home} stats={teams[match.home]} tracker={tracker} />
      <span className={`fixture-mid${match.played ? " fixture-score" : ""}`}>
        {match.played ? `${match.home_goals}–${match.away_goals}` : kickoffTime(match.kickoff)}
      </span>
      <Team name={match.away} stats={teams[match.away]} tracker={tracker} />
    </li>
  );
}

// Dots alone don't say which end is the latest game, and nobody should have to
// guess from the data.
export function FormKey({ tracker }) {
  return (
    <p className="fixture-key">
      {LEGENDS[tracker].map(([mark, label]) => (
        <span key={mark} className="fixture-key-item">
          <span className={`form-dot form-${mark.toLowerCase()}`} />
          {label}
        </span>
      ))}
      <span className="fixture-key-note">Last 5, most recent on the right</span>
    </p>
  );
}
