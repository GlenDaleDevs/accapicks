"""weekblocks: fixture list in, candidate week blocks out. Pure, no I/O."""

from datetime import date

import pytest

from app import weekblocks as wb

EPL = wb.PREMIER_LEAGUE
CHAMP = "soccer_efl_champ"

# Reference calendar (Autumn 2026, GMT/BST boundary is Sun 25 Oct).
TUE_TODAY = date(2026, 9, 29)
FRI, SAT, SUN, MON = (date(2026, 10, d) for d in (2, 3, 4, 5))
NEXT_SAT = date(2026, 10, 10)


def ev(day, hour=15):
    """A fixture kicking off at `hour`:00 UTC on `day` (an ISO string or date)."""
    return {"commence_time": f"{day}T{hour:02d}:00:00Z"}


def fixtures(league=EPL, *days):
    return {league: [ev(d) for d in days]}


# --- is_saturday / saturday_in ------------------------------------------------

def test_is_saturday():
    assert wb.is_saturday(SAT)
    assert not wb.is_saturday(FRI)
    assert not wb.is_saturday(SUN)


def test_saturday_in_finds_the_saturday():
    assert wb.saturday_in(["2026-10-02", "2026-10-03", "2026-10-04"]) == SAT


def test_saturday_in_returns_none_without_a_saturday():
    assert wb.saturday_in(["2026-10-06", "2026-10-07"]) is None


@pytest.mark.parametrize("empty", [None, [], ()])
def test_saturday_in_handles_empty_input(empty):
    assert wb.saturday_in(empty) is None


def test_saturday_in_skips_malformed_strings():
    assert wb.saturday_in(["not-a-date", "", "2026-13-45", "2026-10-03"]) == SAT


def test_saturday_in_none_mixed_with_strings_raises():
    """Current behaviour, arguably a bug: sorted() fails on None-vs-str before
    the per-item `except TypeError` can skip it."""
    with pytest.raises(TypeError):
        wb.saturday_in(["2026-10-03", None])


def test_saturday_in_returns_earliest_when_several():
    assert wb.saturday_in(["2026-10-10", "2026-10-03"]) == SAT


# --- count_by_date ------------------------------------------------------------

def test_count_by_date_splits_all_and_premier_league():
    events = {
        EPL: [ev(SAT), ev(SAT), ev(SUN)],
        CHAMP: [ev(SAT), ev(FRI)],
    }
    all_counts, pl_counts = wb.count_by_date(events)
    assert all_counts == {SAT: 3, SUN: 1, FRI: 1}
    assert pl_counts == {SAT: 2, SUN: 1}


@pytest.mark.parametrize("empty", [None, {}, {EPL: []}, {EPL: None}])
def test_count_by_date_empty(empty):
    assert wb.count_by_date(empty) == ({}, {})


def test_count_by_date_ignores_unparseable_kickoffs():
    events = {EPL: [{"commence_time": "garbage"}, {"commence_time": None}, {}, ev(SAT)]}
    assert wb.count_by_date(events) == ({SAT: 1}, {SAT: 1})


def test_bst_late_kickoff_lands_on_next_london_date():
    # 23:30 UTC on Sat 4 Jul is 00:30 BST on Sunday.
    all_counts, _ = wb.count_by_date({EPL: [ev("2026-07-04", hour=23)]})
    assert list(all_counts) == [date(2026, 7, 5)]


def test_gmt_late_kickoff_stays_on_same_date():
    # After the clocks go back UTC == London, so no shift.
    all_counts, _ = wb.count_by_date({EPL: [ev("2026-10-31", hour=23)]})
    assert list(all_counts) == [date(2026, 10, 31)]


def test_bst_boundary_day_before_clocks_go_back():
    # Sat 24 Oct is still BST: 23:00Z is already Sunday 00:00 London.
    all_counts, _ = wb.count_by_date({EPL: [ev("2026-10-24", hour=23)]})
    assert list(all_counts) == [date(2026, 10, 25)]


def test_offset_timestamps_are_converted_not_truncated():
    events = {EPL: [{"commence_time": "2026-10-03T23:30:00+00:00"}]}
    # 23:30 UTC on 3 Oct is 00:30 BST on 4 Oct.
    assert list(wb.count_by_date(events)[0]) == [SUN]


# --- weekend_dates_for --------------------------------------------------------

def test_weekend_dates_keeps_only_days_with_fixtures():
    counts = {SAT: 5, SUN: 3}
    assert wb.weekend_dates_for(SAT, counts, TUE_TODAY) == ["2026-10-03", "2026-10-04"]


def test_weekend_dates_always_includes_anchor_even_without_fixtures():
    assert wb.weekend_dates_for(SAT, {}, TUE_TODAY) == ["2026-10-03"]


def test_weekend_dates_friday_opening():
    counts = {FRI: 1, SAT: 5, SUN: 3, MON: 1}
    assert wb.weekend_dates_for(SAT, counts, TUE_TODAY) == [
        "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05",
    ]


def test_weekend_dates_drops_friday_already_gone():
    counts = {FRI: 1, SAT: 5, SUN: 3}
    # Saturday morning: Friday's fixtures can no longer be picked.
    assert wb.weekend_dates_for(SAT, counts, today=SAT) == ["2026-10-03", "2026-10-04"]


def test_weekend_dates_ignores_midweek_neighbours():
    counts = {SAT: 5, date(2026, 10, 6): 4}  # Tuesday after
    assert wb.weekend_dates_for(SAT, counts, TUE_TODAY) == ["2026-10-03"]


def test_weekend_dates_zero_count_is_treated_as_no_fixtures():
    assert wb.weekend_dates_for(SAT, {SAT: 5, SUN: 0}, TUE_TODAY) == ["2026-10-03"]


# --- find_week_blocks: Saturday weeks -----------------------------------------

def test_empty_fixture_list_gives_no_blocks():
    assert wb.find_week_blocks({}, today=TUE_TODAY) == []
    assert wb.find_week_blocks(None, today=TUE_TODAY) == []
    assert wb.find_week_blocks({EPL: []}, today=TUE_TODAY) == []


def test_saturday_block_spreads_into_friday_sunday_monday():
    events = fixtures(EPL, FRI, SAT, SAT, SUN, MON)
    assert wb.find_week_blocks(events, today=TUE_TODAY) == [
        {"anchor": SAT, "dates": ["2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05"]},
    ]


def test_efl_only_saturday_still_anchors_a_week():
    blocks = wb.find_week_blocks(fixtures(CHAMP, SAT), today=TUE_TODAY)
    assert blocks == [{"anchor": SAT, "dates": ["2026-10-03"]}]


def test_sunday_only_fixtures_do_not_make_a_week():
    assert wb.find_week_blocks(fixtures(EPL, SUN), today=TUE_TODAY) == []


def test_saturdays_in_the_past_are_excluded():
    events = fixtures(EPL, SAT, NEXT_SAT)
    blocks = wb.find_week_blocks(events, today=date(2026, 10, 4))
    assert [b["anchor"] for b in blocks] == [NEXT_SAT]


def test_saturday_today_is_still_included():
    blocks = wb.find_week_blocks(fixtures(EPL, SAT), today=SAT)
    assert [b["anchor"] for b in blocks] == [SAT]


def test_saturday_beyond_lookahead_is_excluded():
    far = date(2026, 10, 24)  # 25 days after TUE_TODAY
    assert wb.find_week_blocks(fixtures(EPL, far), today=TUE_TODAY) == []


def test_saturday_on_horizon_edge_is_included():
    today = date(2026, 9, 19)
    edge = date(2026, 10, 10)
    assert (edge - today).days == wb.LOOKAHEAD_DAYS
    blocks = wb.find_week_blocks(fixtures(EPL, edge), today=today)
    assert [b["anchor"] for b in blocks] == [edge]


def test_bst_late_saturday_kickoff_does_not_anchor_a_saturday():
    # Only fixture is 23:30 UTC Saturday in BST == Sunday London, so no week.
    events = {EPL: [ev("2026-07-04", hour=23)]}
    assert wb.find_week_blocks(events, today=date(2026, 6, 30)) == []


def test_late_friday_utc_kickoff_in_bst_becomes_saturday_anchor():
    # 23:30 UTC Friday 3 Jul (BST) is 00:30 Saturday 4 Jul London.
    events = {EPL: [ev("2026-07-03", hour=23)]}
    blocks = wb.find_week_blocks(events, today=date(2026, 6, 30))
    assert blocks == [{"anchor": date(2026, 7, 4), "dates": ["2026-07-04"]}]


def test_blocks_sorted_soonest_first_regardless_of_input_order():
    events = {EPL: [ev(NEXT_SAT), ev(SAT)]}
    blocks = wb.find_week_blocks(events, today=TUE_TODAY)
    assert [b["anchor"] for b in blocks] == [SAT, NEXT_SAT]


def test_dates_are_iso_strings_and_anchor_is_a_date():
    (block,) = wb.find_week_blocks(fixtures(EPL, SAT), today=TUE_TODAY)
    assert isinstance(block["anchor"], date)
    assert all(isinstance(d, str) for d in block["dates"])


# --- find_week_blocks: midweek rounds -----------------------------------------

TUE, WED, THU = date(2026, 10, 6), date(2026, 10, 7), date(2026, 10, 8)


def test_full_pl_midweek_round_makes_a_block():
    events = fixtures(EPL, TUE, TUE, WED, WED)
    assert wb.find_week_blocks(events, today=TUE_TODAY) == [
        {"anchor": TUE, "dates": ["2026-10-06", "2026-10-07"]},
    ]


def test_single_rearranged_pl_fixture_is_not_a_midweek_round():
    assert wb.find_week_blocks(fixtures(EPL, WED), today=TUE_TODAY) == []


def test_efl_midweek_never_triggers_a_block():
    events = fixtures(CHAMP, *([TUE] * 6 + [WED] * 6))
    assert wb.find_week_blocks(events, today=TUE_TODAY) == []


def test_midweek_threshold_is_inclusive():
    just_enough = fixtures(EPL, *([WED] * wb.MIN_PL_MIDWEEK))
    too_few = fixtures(EPL, *([WED] * (wb.MIN_PL_MIDWEEK - 1)))
    assert len(wb.find_week_blocks(just_enough, today=TUE_TODAY)) == 1
    assert wb.find_week_blocks(too_few, today=TUE_TODAY) == []


def test_midweek_run_splits_on_gap_days():
    # Tue and Thu with no Wednesday are two runs, neither big enough alone.
    events = fixtures(EPL, TUE, TUE, THU, THU)
    assert wb.find_week_blocks(events, today=TUE_TODAY) == []


def test_midweek_run_spans_tue_wed_thu():
    events = fixtures(EPL, TUE, TUE, WED, WED, THU)
    (block,) = wb.find_week_blocks(events, today=TUE_TODAY)
    assert block["dates"] == ["2026-10-06", "2026-10-07", "2026-10-08"]


def test_midweek_and_saturday_blocks_interleave_by_anchor():
    events = {EPL: [ev(SAT), ev(TUE), ev(TUE), ev(TUE), ev(TUE), ev(NEXT_SAT)]}
    blocks = wb.find_week_blocks(events, today=TUE_TODAY)
    assert [b["anchor"] for b in blocks] == [SAT, TUE, NEXT_SAT]


def test_dates_capped_at_max_dates(monkeypatch):
    monkeypatch.setattr(wb, "MAX_DATES", 2)
    events = fixtures(EPL, FRI, SAT, SUN, MON)
    (block,) = wb.find_week_blocks(events, today=TUE_TODAY)
    assert block["dates"] == ["2026-10-02", "2026-10-03"]
