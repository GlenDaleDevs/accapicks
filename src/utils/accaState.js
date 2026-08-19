import { NOTIONAL_STAKE } from "./constants";

export const ACCA_STATE = {
  OPEN: "open",
  COMPLETE: "complete",
  IN_PLAY: "in_play",
  SETTLED: "settled",
  EXPIRED: "expired",
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

export function lastMatchDate(acca) {
  const dates = acca?.match_dates || [];
  if (dates.length === 0) return null;
  return [...dates].sort()[dates.length - 1];
}

/**
 * An acca nobody ever picked in never locks: auto_lock_accas only considers
 * accas with a non-null locks_at, and locks_at stays null until the first
 * pick. So it sits at status "open" forever, long after its fixtures have
 * been played — and the odds API has nothing left to offer for those dates.
 * Treating it as live is what put "Add your pick" on a dead week.
 */
export function isExpired(acca) {
  if (!acca || acca.status !== "open") return false;
  const last = lastMatchDate(acca);
  if (!last) return false;
  return new Date(`${last}T23:59:59`).getTime() < Date.now();
}

/**
 * Visually distinct states. `status` alone can't express them: it flips
 * open -> locked at first kickoff, so "locked" already means in-play, while
 * "all picks in, nothing kicked off" is still "open".
 */
export function getAccaState(acca, members = []) {
  if (!acca) return ACCA_STATE.OPEN;
  if (SETTLED_STATUSES.includes(acca.status)) return ACCA_STATE.SETTLED;
  if (acca.status === "locked") return ACCA_STATE.IN_PLAY;
  if (isExpired(acca)) return ACCA_STATE.EXPIRED;

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

/**
 * The week picks should land in: the soonest one still taking picks, else the
 * one in play. Deliberately no fallback to the last settled result — landing
 * in a finished acca reads at a glance like one you can still pick in.
 * The list must arrive sorted by first_match_date; locks_at can't order weeks
 * because it stays null until somebody picks.
 */
export function resolveCurrent(accas) {
  if (accas.length === 0) return null;
  // Expired ones must be skipped — an acca nobody picked in stays "open"
  // forever, and landing on one offers picks that can never be made.
  const live = accas.find((a) => a.status === "open" && !isExpired(a));
  if (live) return live;
  const locked = accas.filter((a) => a.status === "locked");
  return locked.length ? locked[locked.length - 1] : null;
}
