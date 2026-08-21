// Shared last-five form dots — used by the Fixtures tab rows (FixtureRow)
// and the team detail page (TeamDetail). Kept apart so neither has to import
// the other.
import { LEGENDS } from "../utils/formLegends";

function meanings(tracker) {
  return Object.fromEntries(LEGENDS[tracker]);
}

// Oldest to newest, so the rightmost circle is the most recent match.
export function Form({ marks, tracker, emptyLabel }) {
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
