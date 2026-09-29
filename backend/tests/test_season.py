"""season: week numbering. Accas are stubbed with namedtuples, no DB session."""

from collections import namedtuple
from datetime import date

from app import season

Acca = namedtuple("Acca", "id name group_id round_number first_match_date")


def acca(id, round_number, first_match_date, name="Old name"):
    return Acca(id, name, 1, round_number, first_match_date)


# --- chronological ------------------------------------------------------------

def test_chronological_orders_by_date_not_round_number():
    early_but_late_created = acca(1, 5, date(2026, 8, 15))
    late_but_early_created = acca(2, 3, date(2026, 8, 29))
    result = season.chronological([late_but_early_created, early_but_late_created])
    assert [a.id for a in result] == [1, 2]


def test_chronological_breaks_date_ties_by_round_number():
    a = acca(1, 7, date(2026, 8, 15))
    b = acca(2, 4, date(2026, 8, 15))
    assert [x.id for x in season.chronological([a, b])] == [2, 1]


def test_chronological_puts_undated_accas_last():
    undated = acca(1, 1, None)
    dated = acca(2, 9, date(2026, 8, 15))
    assert [x.id for x in season.chronological([undated, dated])] == [2, 1]


def test_chronological_treats_missing_round_number_as_zero():
    a = acca(1, 2, date(2026, 8, 15))
    b = acca(2, None, date(2026, 8, 15))
    assert [x.id for x in season.chronological([a, b])] == [2, 1]


def test_chronological_does_not_mutate_input():
    items = [acca(1, 2, date(2026, 8, 29)), acca(2, 1, date(2026, 8, 15))]
    season.chronological(items)
    assert [x.id for x in items] == [1, 2]


# --- week_numbers -------------------------------------------------------------

def test_week_numbers_empty():
    assert season.week_numbers([]) == {}


def test_week_numbers_are_one_based_positions():
    accas = [acca(10, 1, date(2026, 8, 15)), acca(11, 2, date(2026, 8, 22))]
    assert season.week_numbers(accas) == {10: 1, 11: 2}


def test_week_numbers_compact_over_round_number_gaps():
    """A deleted acca leaves a round_number gap; the season label must not."""
    accas = [acca(1, 1, date(2026, 8, 15)), acca(3, 3, date(2026, 8, 29))]
    assert season.week_numbers(accas) == {1: 1, 3: 2}


def test_week_numbers_follow_dates_when_created_out_of_order():
    midweek_one_off = acca(20, 9, date(2026, 8, 19))
    saturday = acca(19, 8, date(2026, 8, 22))
    assert season.week_numbers([saturday, midweek_one_off]) == {20: 1, 19: 2}


def test_week_numbers_number_undated_accas_after_dated_ones():
    accas = [acca(1, 1, None), acca(2, 2, date(2026, 8, 15))]
    assert season.week_numbers(accas) == {2: 1, 1: 2}


# --- label (week_numbers_for_group stubbed, so no DB) -------------------------

def _stub_numbers(monkeypatch, numbers):
    monkeypatch.setattr(season, "week_numbers_for_group", lambda db, gid: (numbers, None))


def test_label_uses_season_week_number(monkeypatch):
    _stub_numbers(monkeypatch, {1: 3})
    assert season.label(None, acca(1, 34, date(2026, 8, 15))) == "Week 3"


def test_label_falls_back_to_round_number_for_past_season(monkeypatch):
    _stub_numbers(monkeypatch, {})
    assert season.label(None, acca(1, 34, date(2025, 8, 15))) == "Week 34"


def test_label_falls_back_to_name_for_legacy_acca(monkeypatch):
    _stub_numbers(monkeypatch, {})
    assert season.label(None, acca(1, None, None, name="Opening day")) == "Opening day"
