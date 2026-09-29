"""normalization.normalize: fuzzy team-name matching used by settlement."""

import pytest

from app.normalization import normalize


@pytest.mark.parametrize("empty", [None, "", ])
def test_empty_input_returns_empty_string(empty):
    assert normalize(empty) == ""


def test_whitespace_only_returns_empty_string():
    """Settlement compares normalized names, so blank must never become a
    non-empty key."""
    assert normalize("   ") == ""


def test_lowercases_and_strips_whitespace():
    assert normalize("  Arsenal ") == "arsenal"


@pytest.mark.parametrize("raw, expected", [
    ("Tottenham Hotspur FC", "tottenham hotspur"),
    ("Bournemouth AFC", "bournemouth"),
    ("Real Madrid CF", "real madrid"),
])
def test_strips_trailing_club_suffix(raw, expected):
    assert normalize(raw) == expected


def test_leading_afc_is_not_stripped():
    assert normalize("AFC Bournemouth") == "afc bournemouth"


def test_only_one_suffix_is_stripped():
    assert normalize("Foo FC AFC") == "foo fc"


def test_bare_suffix_word_is_left_alone():
    assert normalize("FC") == "fc"


@pytest.mark.parametrize("alias", ["Man Utd", "Man United", "man utd", "Manchester United"])
def test_manchester_united_variants_converge(alias):
    assert normalize(alias) == "manchester united"


@pytest.mark.parametrize("alias, canonical", [
    ("Wolves", "wolverhampton wanderers"),
    ("Spurs", "tottenham hotspur"),
    ("Nottm Forest", "nottingham forest"),
    ("Nott'm Forest", "nottingham forest"),
    ("PSG", "paris saint-germain"),
    ("Paris Saint Germain", "paris saint-germain"),
    ("Gladbach", "borussia monchengladbach"),
])
def test_abbreviations_map_to_canonical_name(alias, canonical):
    assert normalize(alias) == canonical


def test_suffix_is_stripped_before_alias_lookup():
    assert normalize("Man City FC") == "manchester city"
    assert normalize("Wolves FC") == "wolverhampton wanderers"


def test_canonical_names_are_stable():
    assert normalize("Manchester City") == "manchester city"
    assert normalize(normalize("Man City")) == "manchester city"


def test_short_alias_matches_full_api_name():
    """The odds feed says 'Brighton and Hove Albion'; scores may say 'Brighton'."""
    assert normalize("Brighton") == normalize("Brighton and Hove Albion")


def test_ampersand_variant_does_not_match_and_variant():
    """Current behaviour, a gap: '&' is not folded to 'and'."""
    assert normalize("Brighton & Hove Albion") != normalize("Brighton and Hove Albion")


def test_accents_are_not_folded():
    """Current behaviour, a gap: 'Atlético Madrid' misses the alias map."""
    assert normalize("Atlético Madrid") != normalize("Atletico Madrid")
