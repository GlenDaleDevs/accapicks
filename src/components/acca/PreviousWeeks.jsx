import { weekLabel } from "../../utils/week";

// The index endpoint returns AccaResponse, which carries no bets — so this
// says only what the list actually knows. Leg counts and returns need the
// detail endpoint, and are on the week's own screen a tap away.
const OUTCOMES = {
  won: "Won",
  lost: "Lost",
  locked: "In play",
  settled: "Settled",
  open: "Lapsed — nobody picked in time",
};

function played(acca) {
  if (!acca.first_match_date) return "";
  const d = new Date(`${acca.first_match_date}T12:00:00`);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export default function PreviousWeeks({ accas, onSelect }) {
  // Most recent first: looking back usually means looking back one week.
  const weeks = [...accas].reverse();

  if (!weeks.length) {
    return <p className="previous-weeks-empty">No weeks have finished yet this season.</p>;
  }

  return (
    <ul className="previous-weeks">
      {weeks.map((acca) => (
        <li key={acca.id}>
          <button type="button" className="previous-week" onClick={() => onSelect(acca)}>
            <span className="previous-week-main">
              <span className="previous-week-label">{weekLabel(acca)}</span>
              <span className={`previous-week-outcome previous-week-${acca.status}`}>
                {OUTCOMES[acca.status] || acca.status}
              </span>
            </span>
            <span className="previous-week-date">{played(acca)}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
