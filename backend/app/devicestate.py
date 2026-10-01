"""Pure logic behind the display-device state endpoint.

No DB, no network, no request objects: plain acca/bet-like objects in, a compact
dict out, so it can be unit-tested directly. It ports the semantics of
src/utils/accaState.js (resolveCurrent, isExpired, pickedCount,
isAwaitingResults) to the server, because a microcontroller cannot reasonably
re-implement them. Keys are deliberately short to keep the payload small.
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from . import season
from .timeutils import as_utc

UK_TZ = ZoneInfo("Europe/London")
SETTLED_STATUSES = ("won", "lost", "settled")
SETTLE_DELAY = timedelta(hours=2)  # settlement only runs 2h past kickoff
MAX_LEGS = 24
LB_SIZE = 5
RESULT_CODES = {"won": "W", "lost": "L", "void": "V"}


def is_expired(acca, now: datetime) -> bool:
    """An open acca whose last match day (UK end-of-day) has passed.

    One nobody picked in never gets a locks_at, so it stays "open" forever.
    """
    if acca.status != "open" or not acca.match_dates:
        return False
    try:
        last = datetime.fromisoformat(max(acca.match_dates))
    except ValueError:
        return False
    return datetime.combine(last.date(), time(23, 59, 59), tzinfo=UK_TZ) < now


def pick_current(accas, now: datetime):
    """The acca a display should show, or None if the group has never had one.

    Soonest open non-expired, else the latest locked, else (a deliberate
    deviation from the frontend, because a display should never sit blank) the
    most recent settled one. Ordered by first_match_date, never round_number.
    """
    ordered = season.chronological(accas)
    for acca in ordered:
        if acca.status == "open" and not is_expired(acca, now):
            return acca
    # chronological() sorts legacy accas (null first_match_date) LAST, so a
    # bare [-1] could prefer a pre-numbering relic over the newest real week.
    def _latest(pool):
        dated = [a for a in pool if a.first_match_date is not None]
        return (dated or pool)[-1] if pool else None

    locked = [a for a in ordered if a.status == "locked"]
    if locked:
        return _latest(locked)
    return _latest([a for a in ordered if a.status in SETTLED_STATUSES])


def derive_state(acca, bets, member_count: int, now: datetime) -> str:
    """One of: open, complete, in_play, awaiting, won, lost, settled.

    `bets` must already be limited to current members' bets.
    """
    if acca.status in SETTLED_STATUSES:
        return acca.status

    if acca.status == "locked":
        kickoffs = [as_utc(b.commence_time) for b in bets]
        finished = bool(bets) and all(k and k + SETTLE_DELAY < now for k in kickoffs)
        if finished and any(not b.result for b in bets):
            return "awaiting"
        return "in_play"

    picked = len({b.user_id for b in bets})
    if member_count > 0 and picked >= member_count:
        # The auto-lock task ticks every 60s, so an acca can be past its lock
        # time while still marked open. That is in play, not complete.
        locks_at = as_utc(acca.locks_at)
        if locks_at and locks_at <= now:
            return "in_play"
        return "complete"
    return "open"


def build_payload(now: datetime, acca, week, member_ids, usernames, bets, lb_rows) -> dict:
    """Assemble the response. `acca` None means the group has never had a week.

    member_ids: set of current member user ids; usernames: {user_id: name};
    bets: every bet on the acca (orphans from departed members are dropped
    here, matching pickedCount); lb_rows: leaderboard_rows() output.
    """
    payload = {"now": int(now.timestamp()), "acca": None}
    if acca is None:
        return payload

    mine = [b for b in bets if b.user_id in member_ids]
    far_future = datetime.max.replace(tzinfo=now.tzinfo)
    mine.sort(key=lambda b: (as_utc(b.commence_time) or far_future, usernames.get(b.user_id, "")))

    locks_at = as_utc(acca.locks_at)
    locks_in = None if locks_at is None else max(0, int((locks_at - now).total_seconds()))

    payload["acca"] = {
        "week": week,
        "state": derive_state(acca, mine, len(member_ids), now),
        "locks_in": locks_in,
        "picks_in": len({b.user_id for b in mine}),
        "members": len(member_ids),
        "legs": [
            {"u": usernames.get(b.user_id, "?"), "r": RESULT_CODES.get(b.result, "-")}
            for b in mine[:MAX_LEGS]
        ],
        # Counts cover every leg, not just the capped list. Voids are in none.
        "legs_w": sum(1 for b in mine if b.result == "won"),
        "legs_l": sum(1 for b in mine if b.result == "lost"),
        "legs_p": sum(1 for b in mine if not b.result),
        "lb": [
            {"u": r["username"], "w": r["won"], "l": r["lost"], "rk": r["rank"]}
            for r in lb_rows[:LB_SIZE]
        ],
    }
    return payload
