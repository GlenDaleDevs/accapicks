import { NOTIONAL_STAKE } from "./constants";

export const ACCA_STATE = {
  OPEN: "open",
  COMPLETE: "complete",
  IN_PLAY: "in_play",
  SETTLED: "settled",
};

const SETTLED_STATUSES = ["won", "lost", "settled"];
const SETTLE_DELAY_MS = 2 * 60 * 60 * 1000; // settlement only runs 2h past kickoff

/**
 * How many *current* members have picked.
 *
 * Counting acca.bets directly is wrong: bets from members who have left are
 * deliberately preserved as orphans, so 4 real picks + 1 orphan would read as
 * "everyone's in" while somebody still hasn't picked.
 */
export function pickedCount(acca, members = []) {
  const memberIds = new Set(members.map((m) => String(m.user_id)));
  const picked = new Set();
  for (const bet of acca?.bets || []) {
    if (memberIds.has(String(bet.user_id))) picked.add(String(bet.user_id));
  }
  return picked.size;
}

/**
 * Four visually distinct states. `status` alone can't express them: it flips
 * open -> locked at first kickoff, so "locked" already means in-play, while
 * "all picks in, nothing kicked off" is still "open".
 */
export function getAccaState(acca, members = []) {
  if (!acca) return ACCA_STATE.OPEN;
  if (SETTLED_STATUSES.includes(acca.status)) return ACCA_STATE.SETTLED;
  if (acca.status === "locked") return ACCA_STATE.IN_PLAY;

  const total = members.length;
  const picked = pickedCount(acca, members);
  if (total > 0 && picked >= total) {
    // The auto-lock task runs on a 60s tick, so an acca can be past its lock
    // time while still marked open. Treat that as in play, not complete.
    if (acca.locks_at && new Date(acca.locks_at).getTime() <= Date.now()) {
      return ACCA_STATE.IN_PLAY;
    }
    return ACCA_STATE.COMPLETE;
  }
  return ACCA_STATE.OPEN;
}

/**
 * True when every match has finished but results haven't landed yet.
 * Without this an acca reads "In play" for hours after the football ended.
 */
export function isAwaitingResults(acca) {
  const bets = acca?.bets || [];
  if (bets.length === 0) return false;
  const now = Date.now();
  const allFinished = bets.every(
    (b) => b.commence_time && new Date(b.commence_time).getTime() + SETTLE_DELAY_MS < now,
  );
  return allFinished && bets.some((b) => !b.result);
}

export function landedCount(acca) {
  return (acca?.bets || []).filter((b) => b.result === "won").length;
}

export function combinedOdds(acca) {
  const filled = (acca?.bets || []).filter((b) => b.odds);
  if (filled.length === 0) return 0;
  return filled.reduce((acc, bet) => acc * parseFloat(bet.odds), 1);
}

/** Illustrative returns on NOTIONAL_STAKE. Zero once any leg has lost. */
export function potentialReturns(acca) {
  const bets = acca?.bets || [];
  if (bets.some((b) => b.result === "lost")) return 0;
  const odds = combinedOdds(acca);
  return odds > 0 ? odds * NOTIONAL_STAKE : 0;
}

export function formatMoney(value) {
  return `£${value.toFixed(2)}`;
}
