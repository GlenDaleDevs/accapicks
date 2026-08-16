import { ACCA_STATE, isAwaitingResults, landedCount, potentialReturns, formatMoney } from "../../utils/accaState";
import { NOTIONAL_STAKE } from "../../utils/constants";
import { weekLabel } from "../../utils/week";

function formatLockTime(iso) {
  const d = new Date(iso);
  const day = d.toLocaleDateString("en-GB", { weekday: "short" });
  const time = d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  return `${day} ${time}`;
}

// The deadline folds into the week strip rather than becoming a third bar.
function contextLine(acca, state) {
  const total = (acca?.bets || []).length;
  const landed = landedCount(acca);

  if (state === ACCA_STATE.SETTLED) {
    const returns = potentialReturns(acca);
    return `Settled — ${landed} of ${total} landed, £${NOTIONAL_STAKE} → ${formatMoney(returns)}`;
  }
  if (state === ACCA_STATE.IN_PLAY) {
    if (isAwaitingResults(acca)) {
      return `Awaiting results — ${landed} of ${total} landed so far`;
    }
    return `In play — ${landed} of ${total} landed`;
  }
  if (state === ACCA_STATE.EXPIRED) return "Lapsed — nobody picked in time";
  if (!acca?.locks_at) return "No picks yet — locks at the first kickoff picked";
  return `Locks ${formatLockTime(acca.locks_at)}`;
}

export default function WeekStrip({
  acca,
  state,
  onPrev,
  onNext,
  hasPrev,
  hasNext,
  showBackToCurrent,
  onBackToCurrent,
}) {
  return (
    <div className="week-strip">
      <div className="week-strip-row">
        <button
          type="button"
          className="week-arrow"
          onClick={onPrev}
          disabled={!hasPrev}
          aria-label="Previous week"
        >
          ‹
        </button>
        <span className="week-label">
          {weekLabel(acca)}
        </span>
        <button
          type="button"
          className="week-arrow"
          onClick={onNext}
          disabled={!hasNext}
          aria-label="Next week"
        >
          ›
        </button>
      </div>

      <div className={`week-context week-context-${state}`}>{contextLine(acca, state)}</div>

      {showBackToCurrent && (
        <button type="button" className="week-back-current" onClick={onBackToCurrent}>
          Back to current
        </button>
      )}
    </div>
  );
}
