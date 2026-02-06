from fastapi import APIRouter, Depends, Request
from .. import odds_api
from .auth import get_current_user
from ..limiter import limiter

router = APIRouter()


# Get available football matches with odds
@router.get("/odds/matches")
@limiter.limit("30/minute")
def get_matches(request: Request, sport: str = "soccer_epl", user_id: int = Depends(get_current_user)):
    """
    Get upcoming matches with odds
    Available sports: soccer_epl, soccer_spain_la_liga, soccer_germany_bundesliga, soccer_italy_serie_a
    """
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
    league_list = [l.strip() for l in leagues.split(",") if l.strip()]
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
