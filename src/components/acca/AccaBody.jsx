import { motion } from "framer-motion";
import { staggerContainer, staggerItem } from "../../utils/animations";
import { formatOdds, formatKickoffTime } from "../../utils/formatters";
import { NOTIONAL_STAKE } from "../../utils/constants";
import {
  ACCA_STATE,
  combinedOdds,
  potentialReturns,
  formatMoney,
  pickedCount,
} from "../../utils/accaState";

// Plain English, one line. Not a progress bar, not icons.
function statusSentence(acca, members, state) {
  const total = members.length;
  const picked = pickedCount(acca, members);

  if (state === ACCA_STATE.SETTLED) return null;
  if (state === ACCA_STATE.IN_PLAY) return null;
  if (total === 0) return null;

  if (picked === 0) return "No picks in yet — be the first.";
  if (picked >= total) return "All picks in. Good luck.";

  const betUserIds = new Set((acca?.bets || []).map((b) => String(b.user_id)));
  const waiting = members
    .filter((m) => !betUserIds.has(String(m.user_id)))
    .map((m) => m.username);

  let names;
  if (waiting.length === 1) names = waiting[0];
  else if (waiting.length === 2) names = `${waiting[0]} and ${waiting[1]}`;
  else names = `${waiting.slice(0, -1).join(", ")} and ${waiting[waiting.length - 1]}`;

  return `${picked} of ${total} picks in — ${names} still to go.`;
}

function resultMark(result) {
  if (result === "won") return <span className="pick-mark pick-mark-won">✓</span>;
  if (result === "lost") return <span className="pick-mark pick-mark-lost">✗</span>;
  if (result === "void") return <span className="pick-mark pick-mark-void">—</span>;
  return null;
}

export default function AccaBody({
  acca,
  state,
  members,
  user,
  oddsFormat,
  onAddPick,
  onRemovePick,
  readOnly,
}) {
  const betByUser = {};
  (acca?.bets || []).forEach((b) => {
    betByUser[String(b.user_id)] = b;
  });

  // Current user first, then alphabetical.
  const ordered = [...members].sort((a, b) => {
    if (user && a.user_id === user.id) return -1;
    if (user && b.user_id === user.id) return 1;
    return a.username.localeCompare(b.username);
  });

  const ownBet = user ? betByUser[String(user.id)] : null;
  const canPick = !readOnly && state === ACCA_STATE.OPEN;
  const sentence = statusSentence(acca, members, state);
  const odds = combinedOdds(acca);
  const returns = potentialReturns(acca);

  return (
    <motion.div variants={staggerContainer} initial="initial" animate="animate" className="acca-body">
      {sentence && (
        <motion.p variants={staggerItem} className="acca-status-sentence">
          {sentence}
        </motion.p>
      )}

      {/* Your slot, treated differently: a large prompt until you've picked,
          then it collapses into a normal row and the affordance disappears. */}
      {canPick && !ownBet && (
        <motion.button variants={staggerItem} className="own-slot-card" onClick={onAddPick}>
          <span className="own-slot-title">Add your pick</span>
          <span className="own-slot-sub">One match, your call</span>
        </motion.button>
      )}

      <motion.div variants={staggerItem} className="pick-rows">
        {ordered.map((m) => {
          const bet = betByUser[String(m.user_id)];
          const isSelf = user && m.user_id === user.id;
          return (
            <div key={m.user_id} className={`pick-row${bet ? "" : " pick-row-empty"}`}>
              <div className="pick-row-who">
                <span className="pick-avatar" aria-hidden="true">
                  {m.username.charAt(0).toUpperCase()}
                </span>
                <span className="pick-name">{m.username}</span>
              </div>

              {bet ? (
                <div className="pick-row-bet">
                  <span className="pick-desc">{bet.description}</span>
                  <span className="pick-meta">
                    {bet.commence_time && (
                      <span className="pick-kickoff">{formatKickoffTime(bet.commence_time)}</span>
                    )}
                    <span className="pick-odds">{formatOdds(bet.odds, oddsFormat)}</span>
                    {resultMark(bet.result)}
                  </span>
                  {isSelf && canPick && (
                    <button type="button" className="pick-remove" onClick={() => onRemovePick(bet.id)}>
                      Remove
                    </button>
                  )}
                </div>
              ) : (
                <span className="pick-waiting">
                  {state === ACCA_STATE.OPEN ? "Waiting" : "No pick"}
                </span>
              )}
            </div>
          );
        })}
      </motion.div>

      {/* The payoff — pinned, never below the fold. */}
      {odds > 0 && (
        <div className="returns-bar">
          <div className="returns-odds">
            <span className="returns-label">Combined odds</span>
            <span className="returns-value">{formatOdds(odds, oddsFormat)}</span>
          </div>
          <div className="returns-money">
            <span className="returns-label">£{NOTIONAL_STAKE} returns</span>
            <span className="returns-value returns-value-money">{formatMoney(returns)}</span>
          </div>
        </div>
      )}
    </motion.div>
  );
}
