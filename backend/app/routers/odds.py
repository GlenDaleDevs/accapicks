import re
from fastapi import APIRouter, Depends, Request, HTTPException
from .. import fixturelist, h2h, odds_api, standings
from ..schemas import VALID_SPORT_KEYS
from .auth import get_current_user
from ..limiter import limiter

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DIVISION_PATTERN = re.compile(r"^E[0-3]$")
EVENT_ID_PATTERN = re.compile(r"^[a-f0-9]{1,64}$")
TEAM_NAME_MAX_LENGTH = 64

router = APIRouter()


# Get available football matches with odds
@router.get("/odds/matches")
@limiter.limit("30/minute")
def get_matches(request: Request, sport: str = "soccer_epl", user_id: int = Depends(get_current_user)):
    """
    Get upcoming matches with odds
    Available sports: soccer_epl, soccer_spain_la_liga, soccer_germany_bundesliga, soccer_italy_serie_a
    """
    if sport not in VALID_SPORT_KEYS:
        raise HTTPException(status_code=400, detail="Invalid sport key")
    matches = odds_api.get_football_matches(sport)

    # Format matches for easier display
    formatted_matches = []
    for match in matches:
        formatted = odds_api.format_match_for_display(match)
        if formatted:
            formatted_matches.append(formatted)

    return formatted_matches


# Get filtered matches for specific leagues and date range
@router.get("/odds/matches/filtered")
@limiter.limit("30/minute")
def get_filtered_matches(
    request: Request,
    leagues: str,
    date_from: str,
    date_to: str,
    user_id: int = Depends(get_current_user)
):
    """
    Get matches filtered by leagues and date range.
    leagues: comma-separated sport keys e.g. "soccer_epl,soccer_spain_la_liga"
    date_from/date_to: date strings e.g. "2026-02-08"
    """
    if not DATE_PATTERN.match(date_from) or not DATE_PATTERN.match(date_to):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    league_list = [l.strip() for l in leagues.split(",") if l.strip()]
    for league in league_list:
        if league not in VALID_SPORT_KEYS:
            raise HTTPException(status_code=400, detail="Invalid league")
    formatted_matches = []

    for league in league_list:
        matches = odds_api.get_football_matches(league)
        for match in matches:
            commence = match.get("commence_time", "")
            match_date = commence[:10]
            if date_from <= match_date <= date_to:
                formatted = odds_api.format_match_for_display(match, league=league)
                if formatted:
                    formatted_matches.append(formatted)

    # Sort by kickoff time
    formatted_matches.sort(key=lambda m: m["commence_time"])

    return formatted_matches


@router.get("/odds/standings")
@limiter.limit("30/minute")
def get_standings(request: Request, season: str = "current", user_id: int = Depends(get_current_user)):
    """League tables, served from the background-refreshed cache.

    `season` is "current" or "last" — the football-data season codes stay
    server-side so a caller can't ask for an arbitrary file.
    """
    if season not in standings.SEASONS:
        raise HTTPException(status_code=400, detail="Invalid season")
    return standings.get_cached(season)


@router.get("/odds/fixtures")
# Served from the in-memory cache, and the week stepper plus four league
# chips legitimately produce a request per tap — 30/min bricked browsers.
@limiter.limit("60/minute")
def get_fixture_list(request: Request, week: str = "", league: str = "", user_id: int = Depends(get_current_user)):
    """One week of fixtures and results across the four English divisions.

    `week` is the Monday of the week wanted, as returned in `weeks`. Omitted,
    it serves the current week. `league` is a division code (E0-E3); when the
    requested week is upcoming, that division's fixtures carry cached
    bookmaker odds — one division per request keeps a cold visit to at most
    one odds fetch.
    """
    if week and not DATE_PATTERN.match(week):
        raise HTTPException(status_code=400, detail="Invalid week format. Use YYYY-MM-DD")
    if league and not DIVISION_PATTERN.match(league):
        raise HTTPException(status_code=400, detail="Invalid league code")
    payload = fixturelist.get_week(week or None)
    if league:
        payload = fixturelist.attach_odds(payload, league)
    return payload


@router.get("/odds/team")
# Fixtures-tab tap-through -- served from a disk read, not the odds API, so
# it carries the same headroom as /odds/fixtures.
@limiter.limit("60/minute")
def get_team_detail(
    request: Request,
    division: str,
    name: str,
    season: str = "current",
    user_id: int = Depends(get_current_user),
):
    """One team's league position, results and form for a season.

    `name` is matched in-memory against the results rows (no SQL) -- it need
    not be a known club; an unrecognised name just renders an empty page,
    same as a club with no games yet. Always 200 for a valid division: a
    season-scoped 404 would reject every tap on opening weekend, when no club
    has rows yet.
    """
    if not DIVISION_PATTERN.match(division):
        raise HTTPException(status_code=400, detail="Invalid division code")
    if season not in standings.SEASONS:
        raise HTTPException(status_code=400, detail="Invalid season")

    name = name.strip()[:TEAM_NAME_MAX_LENGTH]
    season_code = standings.SEASONS[season]
    detail = fixturelist.team_detail_resolved(season_code, division, name)

    return {
        "team": name,
        "division": division,
        "season": season,
        **detail,
    }


@router.get("/odds/h2h")
# Served from the background-warmed in-memory cache, not a live fetch, so it
# carries the same headroom as /odds/fixtures and /odds/team.
@limiter.limit("60/minute")
def get_h2h_record(
    request: Request,
    home: str,
    away: str,
    user_id: int = Depends(get_current_user),
):
    """All-time head-to-head record between two teams.

    `home`/`away` are matched in-memory against the cached history rows (no
    SQL) -- either can be any string; unresolved names just render an empty
    record, same as a club with no games yet. Always 200: while the
    background warm-up is still loading (cold start after a deploy), the
    cache isn't ready yet and the response comes back zeroed with
    `ready: false` so the client can show a warming state instead of an
    error.
    """
    home = home.strip()[:TEAM_NAME_MAX_LENGTH]
    away = away.strip()[:TEAM_NAME_MAX_LENGTH]
    return h2h.h2h_record(home, away)


@router.get("/odds/matches/{event_id}/btts")
@limiter.limit("30/minute")
def get_btts_odds(event_id: str, sport_key: str, request: Request, user_id: int = Depends(get_current_user)):
    """Get BTTS odds for a specific event (lazy-fetched, 24h cache)"""
    if sport_key not in VALID_SPORT_KEYS:
        raise HTTPException(status_code=400, detail="Invalid sport key")
    if not EVENT_ID_PATTERN.match(event_id):
        raise HTTPException(status_code=400, detail="Invalid event ID format")
    return odds_api.get_btts_for_event(sport_key, event_id)
