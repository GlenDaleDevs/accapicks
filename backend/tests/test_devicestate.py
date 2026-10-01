"""devicestate: display-device state logic. Accas and bets are SimpleNamespace stubs, no DB."""

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from app import devicestate

UTC = timezone.utc
NOW = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)  # a Saturday in BST


def acca(id=1, status="open", match_dates=("2026-08-15",), first=date(2026, 8, 15),
         round_number=None, locks_at=None):
    return SimpleNamespace(
        id=id, status=status, match_dates=list(match_dates) if match_dates is not None else None,
        first_match_date=first, round_number=round_number or id, locks_at=locks_at,
    )


def bet(user_id=1, kickoff=None, result=None):
    return SimpleNamespace(user_id=user_id, commence_time=kickoff, result=result)


# --- is_expired ---------------------------------------------------------------

def test_is_expired_false_without_match_dates():
    assert devicestate.is_expired(acca(match_dates=[]), NOW) is False
    assert devicestate.is_expired(acca(match_dates=None), NOW) is False


def test_is_expired_false_for_future_date():
    assert devicestate.is_expired(acca(match_dates=["2026-08-20"]), NOW) is False


def test_is_expired_false_on_the_match_day_itself():
    assert devicestate.is_expired(acca(match_dates=["2026-08-15"]), NOW) is False


def test_is_expired_true_for_past_date():
    assert devicestate.is_expired(acca(match_dates=["2026-08-10"]), NOW) is True


def test_is_expired_false_for_malformed_date():
    assert devicestate.is_expired(acca(match_dates=["not-a-date"]), NOW) is False


def test_is_expired_uses_latest_match_date():
    a = acca(match_dates=["2026-08-10", "2026-08-15"])
    assert devicestate.is_expired(a, NOW) is False


def test_is_expired_only_applies_to_open_accas():
    assert devicestate.is_expired(acca(status="locked", match_dates=["2026-08-01"]), NOW) is False
    assert devicestate.is_expired(acca(status="won", match_dates=["2026-08-01"]), NOW) is False


def test_is_expired_bst_boundary():
    """In August UK end-of-day 23:59:59 BST is 22:59:59 UTC, not 23:59:59."""
    a = acca(match_dates=["2026-08-15"])
    assert devicestate.is_expired(a, datetime(2026, 8, 15, 22, 59, 58, tzinfo=UTC)) is False
    assert devicestate.is_expired(a, datetime(2026, 8, 15, 23, 0, 0, tzinfo=UTC)) is True


def test_is_expired_gmt_boundary():
    """In winter UK end-of-day lines up with UTC."""
    a = acca(match_dates=["2026-12-15"])
    assert devicestate.is_expired(a, datetime(2026, 12, 15, 23, 59, 58, tzinfo=UTC)) is False
    assert devicestate.is_expired(a, datetime(2026, 12, 16, 0, 0, 0, tzinfo=UTC)) is True


def test_is_expired_on_spring_forward_day():
    """2026-03-29 is the day clocks go forward; end of day is already BST."""
    a = acca(match_dates=["2026-03-29"])
    assert devicestate.is_expired(a, datetime(2026, 3, 29, 22, 59, 58, tzinfo=UTC)) is False
    assert devicestate.is_expired(a, datetime(2026, 3, 29, 23, 0, 0, tzinfo=UTC)) is True


# --- pick_current -------------------------------------------------------------

def test_pick_current_empty_returns_none():
    assert devicestate.pick_current([], NOW) is None


def test_pick_current_prefers_open_over_locked_and_settled():
    accas = [
        acca(1, "settled", ["2026-08-01"], date(2026, 8, 1)),
        acca(2, "locked", ["2026-08-08"], date(2026, 8, 8)),
        acca(3, "open", ["2026-08-15"], date(2026, 8, 15)),
    ]
    assert devicestate.pick_current(accas, NOW).id == 3


def test_pick_current_picks_soonest_open():
    accas = [
        acca(1, "open", ["2026-08-29"], date(2026, 8, 29)),
        acca(2, "open", ["2026-08-15"], date(2026, 8, 15)),
    ]
    assert devicestate.pick_current(accas, NOW).id == 2


def test_pick_current_orders_by_date_not_round_number():
    later_date_lower_round = acca(1, "open", ["2026-08-29"], date(2026, 8, 29), round_number=1)
    earlier_date_higher_round = acca(2, "open", ["2026-08-16"], date(2026, 8, 16), round_number=9)
    assert devicestate.pick_current([later_date_lower_round, earlier_date_higher_round], NOW).id == 2


def test_pick_current_skips_expired_open_acca():
    accas = [
        acca(1, "open", ["2026-08-08"], date(2026, 8, 8)),
        acca(2, "open", ["2026-08-15"], date(2026, 8, 15)),
    ]
    assert devicestate.pick_current(accas, NOW).id == 2


def test_pick_current_skips_open_acca_expired_in_bst_window():
    """23:30 UTC on the 15th is already the 16th in the UK, so the 15th is over."""
    late = datetime(2026, 8, 15, 23, 30, tzinfo=UTC)
    accas = [
        acca(1, "open", ["2026-08-15"], date(2026, 8, 15)),
        acca(2, "locked", ["2026-08-08"], date(2026, 8, 8)),
    ]
    assert devicestate.pick_current(accas, late).id == 2


def test_pick_current_falls_back_to_latest_locked_when_only_expired_open():
    accas = [
        acca(1, "locked", ["2026-08-01"], date(2026, 8, 1)),
        acca(2, "locked", ["2026-08-08"], date(2026, 8, 8)),
        acca(3, "open", ["2026-08-05"], date(2026, 8, 5)),
    ]
    assert devicestate.pick_current(accas, NOW).id == 2


def test_pick_current_falls_back_to_most_recent_settled():
    accas = [
        acca(1, "won", ["2026-07-25"], date(2026, 7, 25)),
        acca(2, "lost", ["2026-08-08"], date(2026, 8, 8)),
        acca(3, "settled", ["2026-08-01"], date(2026, 8, 1)),
    ]
    assert devicestate.pick_current(accas, NOW).id == 2


def test_pick_current_returns_none_when_only_expired_open():
    """Pins current behaviour: an expired open acca is never a fallback itself."""
    assert devicestate.pick_current([acca(1, "open", ["2026-08-01"], date(2026, 8, 1))], NOW) is None


# --- derive_state -------------------------------------------------------------

def test_derive_state_settled_passthrough():
    for status in ("won", "lost", "settled"):
        assert devicestate.derive_state(acca(status=status), [], 3, NOW) == status


def test_derive_state_open_when_not_everyone_picked():
    bets = [bet(1), bet(2)]
    assert devicestate.derive_state(acca(), bets, 3, NOW) == "open"


def test_derive_state_open_with_no_members():
    assert devicestate.derive_state(acca(), [], 0, NOW) == "open"


def test_derive_state_complete_when_all_members_picked():
    bets = [bet(1), bet(2), bet(3)]
    a = acca(locks_at=NOW + timedelta(hours=3))
    assert devicestate.derive_state(a, bets, 3, NOW) == "complete"


def test_derive_state_complete_counts_distinct_users_not_bets():
    bets = [bet(1), bet(1), bet(1)]
    assert devicestate.derive_state(acca(), bets, 3, NOW) == "open"


def test_derive_state_complete_with_null_locks_at():
    assert devicestate.derive_state(acca(locks_at=None), [bet(1), bet(2)], 2, NOW) == "complete"


def test_derive_state_lock_lag_open_but_locks_at_passed_is_in_play():
    a = acca(status="open", locks_at=NOW - timedelta(seconds=30))
    assert devicestate.derive_state(a, [bet(1), bet(2)], 2, NOW) == "in_play"


def test_derive_state_lock_lag_boundary_locks_at_equal_now_is_in_play():
    a = acca(status="open", locks_at=NOW)
    assert devicestate.derive_state(a, [bet(1)], 1, NOW) == "in_play"


def test_derive_state_lock_lag_accepts_naive_locks_at_as_utc():
    a = acca(status="open", locks_at=(NOW - timedelta(minutes=1)).replace(tzinfo=None))
    assert devicestate.derive_state(a, [bet(1)], 1, NOW) == "in_play"


def test_derive_state_locked_before_kickoffs_is_in_play():
    bets = [bet(1, NOW + timedelta(hours=1)), bet(2, NOW + timedelta(hours=2))]
    assert devicestate.derive_state(acca(status="locked"), bets, 2, NOW) == "in_play"


def test_derive_state_locked_awaiting_when_all_kickoffs_over_2h_ago_and_results_missing():
    old = NOW - timedelta(hours=3)
    bets = [bet(1, old, "won"), bet(2, old, None)]
    assert devicestate.derive_state(acca(status="locked"), bets, 2, NOW) == "awaiting"


def test_derive_state_awaiting_needs_every_kickoff_past_not_just_some():
    bets = [bet(1, NOW - timedelta(hours=3)), bet(2, NOW + timedelta(hours=1))]
    assert devicestate.derive_state(acca(status="locked"), bets, 2, NOW) == "in_play"


def test_derive_state_awaiting_needs_more_than_2h_past_kickoff():
    bets = [bet(1, NOW - timedelta(hours=2))]  # exactly 2h: not yet strictly past
    assert devicestate.derive_state(acca(status="locked"), bets, 1, NOW) == "in_play"


def test_derive_state_locked_all_finished_with_results_stays_in_play():
    old = NOW - timedelta(hours=5)
    bets = [bet(1, old, "won"), bet(2, old, "void")]
    assert devicestate.derive_state(acca(status="locked"), bets, 2, NOW) == "in_play"


def test_derive_state_locked_without_bets_is_in_play():
    assert devicestate.derive_state(acca(status="locked"), [], 2, NOW) == "in_play"


def test_derive_state_locked_missing_kickoff_is_never_awaiting():
    bets = [bet(1, None), bet(2, NOW - timedelta(hours=5))]
    assert devicestate.derive_state(acca(status="locked"), bets, 2, NOW) == "in_play"


def test_derive_state_locked_naive_kickoff_treated_as_utc():
    naive = (NOW - timedelta(hours=3)).replace(tzinfo=None)
    assert devicestate.derive_state(acca(status="locked"), [bet(1, naive)], 1, NOW) == "awaiting"


# --- build_payload ------------------------------------------------------------

def payload(a=None, week=1, members=(1, 2, 3), bets=(), lb=(), names=None):
    names = names or {1: "ann", 2: "bob", 3: "cat", 99: "gone"}
    return devicestate.build_payload(NOW, a or acca(), week, set(members), names, list(bets), list(lb))


def test_build_payload_no_acca():
    assert devicestate.build_payload(NOW, None, None, set(), {}, [], []) == {
        "now": int(NOW.timestamp()), "acca": None,
    }


def test_build_payload_top_level_shape():
    p = payload()
    assert p["now"] == int(NOW.timestamp())
    assert set(p["acca"]) == {
        "week", "state", "locks_in", "picks_in", "members", "legs",
        "legs_w", "legs_l", "legs_p", "lb",
    }
    assert p["acca"]["members"] == 3
    assert p["acca"]["state"] == "open"


def test_build_payload_picks_in_excludes_orphaned_bets():
    bets = [bet(1), bet(2), bet(99)]  # 99 left the group
    a = payload(bets=bets)["acca"]
    assert a["picks_in"] == 2
    assert [leg["u"] for leg in a["legs"]] == ["ann", "bob"]


def test_build_payload_orphans_do_not_complete_the_acca():
    bets = [bet(1), bet(2), bet(99)]
    assert payload(members=(1, 2, 3), bets=bets)["acca"]["state"] == "open"


def test_build_payload_picks_in_counts_distinct_users():
    assert payload(bets=[bet(1), bet(1)])["acca"]["picks_in"] == 1


def test_build_payload_result_letters():
    bets = [
        bet(1, result="won"), bet(2, result="lost"), bet(3, result="void"),
        bet(1, result=None), bet(2, result="weird"),
    ]
    legs = payload(bets=bets)["acca"]["legs"]
    assert sorted(leg["r"] for leg in legs) == ["-", "-", "L", "V", "W"]


def test_build_payload_leg_counts_exclude_voids():
    bets = [bet(1, result="won"), bet(2, result="won"), bet(3, result="lost"),
            bet(1, result="void"), bet(2, result=None)]
    a = payload(bets=bets)["acca"]
    assert (a["legs_w"], a["legs_l"], a["legs_p"]) == (2, 1, 1)


def test_build_payload_legs_sorted_by_kickoff_then_username_unknown_last():
    t = NOW + timedelta(hours=1)
    bets = [bet(3, None), bet(2, t), bet(1, t), bet(3, t - timedelta(minutes=30))]
    legs = payload(bets=bets)["acca"]["legs"]
    assert [leg["u"] for leg in legs] == ["cat", "ann", "bob", "cat"]


def test_build_payload_legs_capped_but_counts_truthful():
    n = devicestate.MAX_LEGS + 6
    members = set(range(1, n + 1))
    names = {i: f"u{i:02d}" for i in members}
    bets = [bet(i, NOW + timedelta(minutes=i), "won" if i % 2 else "lost") for i in members]
    a = payload(members=members, bets=bets, names=names)["acca"]
    assert len(a["legs"]) == devicestate.MAX_LEGS == 24
    assert a["legs_w"] + a["legs_l"] == n
    assert a["legs_p"] == 0
    assert a["picks_in"] == n
    assert a["members"] == n


def test_build_payload_unknown_username_is_question_mark():
    a = payload(members=(1, 2, 3, 7), bets=[bet(7)], names={})["acca"]
    assert a["legs"][0]["u"] == "?"


def test_build_payload_locks_in_null_when_no_locks_at():
    assert payload(a=acca(locks_at=None))["acca"]["locks_in"] is None


def test_build_payload_locks_in_positive_seconds():
    a = payload(a=acca(locks_at=NOW + timedelta(minutes=90)))["acca"]
    assert a["locks_in"] == 5400


def test_build_payload_locks_in_clamped_to_zero_when_past():
    a = payload(a=acca(locks_at=NOW - timedelta(hours=1)))["acca"]
    assert a["locks_in"] == 0


def test_build_payload_locks_in_zero_when_exactly_now():
    assert payload(a=acca(locks_at=NOW))["acca"]["locks_in"] == 0


def test_build_payload_week_passthrough_and_null_for_past_season():
    assert payload(week=4)["acca"]["week"] == 4
    assert payload(week=None)["acca"]["week"] is None


def test_build_payload_state_uses_current_members_only():
    """All three current members picked, plus an orphan: complete, not tripped by the orphan."""
    bets = [bet(1), bet(2), bet(3), bet(99)]
    a = payload(a=acca(locks_at=NOW + timedelta(hours=2)), bets=bets)["acca"]
    assert a["state"] == "complete"
    assert a["picks_in"] == 3


def test_build_payload_leaderboard_top_five_mapped():
    rows = [{"username": f"u{i}", "won": i, "lost": 10 - i, "rank": i, "extra": "x"}
            for i in range(1, 9)]
    lb = payload(lb=rows)["acca"]["lb"]
    assert len(lb) == devicestate.LB_SIZE == 5
    assert lb[0] == {"u": "u1", "w": 1, "l": 9, "rk": 1}
    assert [r["u"] for r in lb] == ["u1", "u2", "u3", "u4", "u5"]


def test_build_payload_leaderboard_short_list_and_empty():
    rows = [{"username": "a", "won": 1, "lost": 0, "rank": 1}]
    assert len(payload(lb=rows)["acca"]["lb"]) == 1
    assert payload(lb=[])["acca"]["lb"] == []
