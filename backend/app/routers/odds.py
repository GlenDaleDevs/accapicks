import re
from fastapi import APIRouter, Depends, Request, HTTPException
from .. import odds_api, favourable
from .auth import get_current_user
from ..limiter import limiter

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EVENT_ID_PATTERN = re.compile(r"^[a-f0-9]{1,64}$")

router = APIRouter()

VALID_SPORT_KEYS = {
    "soccer_epl", "soccer_efl_champ", "soccer_england_league1",
    "soccer_england_league2", "soccer_spain_la_liga",
    "soccer_germany_bundesliga", "soccer_italy_serie_a",
    "soccer_france_ligue_one",
}


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


@router.get("/odds/favourable")
@limiter.limit("30/minute")
def get_favourable_matchups(request: Request, user_id: int = Depends(get_current_user)):
    """Lopsided upcoming fixtures, served from the background-refreshed cache.

    An empty list is a valid answer, not a failure — a round with no strong
    mismatch is more credible than one that always finds something.
    """
    return favourable.get_cached()


@router.get("/odds/matches/{event_id}/btts")
@limiter.limit("30/minute")
def get_btts_odds(event_id: str, sport_key: str, request: Request, user_id: int = Depends(get_current_user)):
    """Get BTTS odds for a specific event (lazy-fetched, 24h cache)"""
    if sport_key not in VALID_SPORT_KEYS:
        raise HTTPException(status_code=400, detail="Invalid sport key")
    if not EVENT_ID_PATTERN.match(event_id):
        raise HTTPException(status_code=400, detail="Invalid event ID format")
    return odds_api.get_btts_for_event(sport_key, event_id)
