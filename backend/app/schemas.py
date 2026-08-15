from pydantic import BaseModel, EmailStr, Field, field_validator, PlainSerializer
from datetime import datetime, timezone, date
from typing import Optional, Annotated
import re
import math


def _serialize_utc(dt: Optional[datetime]) -> Optional[str]:
    """Always emit an explicit UTC offset.

    Postgres returns tz-aware datetimes, but SQLite has no timezone storage and
    returns naive ones, which Pydantic then serialises as "2026-08-15T14:00:00".
    An ISO datetime with no offset is ambiguous, and JavaScript parses that form
    as *local* time — so a 14:00 UTC kickoff displayed as 14:00 instead of 15:00
    in BST. Values are always stored as UTC, so stamping UTC is correct.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


# Use for every datetime that crosses the API boundary.
UtcDatetime = Annotated[datetime, PlainSerializer(_serialize_utc, return_type=Optional[str])]


def validate_password_strength(v):
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[a-zA-Z]", v):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    return v


# Schema for user registration (what we receive)
class UserCreate(BaseModel):
    email: EmailStr  # Validates it's a proper email format
    username: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)
    age_confirmed: bool = False

    @field_validator("age_confirmed")
    @classmethod
    def must_confirm_age(cls, v):
        if not v:
            raise ValueError("You must confirm you are 18 or over")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        return validate_password_strength(v)

# Schema for user login (what we receive)
class UserLogin(BaseModel):
    identifier: str = Field(min_length=1, max_length=254)  # Can be email or username
    password: str = Field(min_length=1, max_length=128)


# Schema for user response (what we send back, no password!)
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    email_verified: bool = False
    created_at: UtcDatetime

    class Config:
        from_attributes = True  # Allows SQLAlchemy models to work with Pydantic


# Schema for email verification request
class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


# Schema for resend verification code request
class ResendCodeRequest(BaseModel):
    email: EmailStr


# Schema for forgot password request
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


# Schema for reset password request
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        return validate_password_strength(v)


# Schema for change password request
class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        return validate_password_strength(v)


# Schema for signup response (requires verification)
class SignupResponse(BaseModel):
    message: str
    email: str
    requires_verification: bool = True

# Schema for token response (what we send after successful login)
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Schema for creating a group (what we receive)
class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v):
        v = re.sub(r"<[^>]+>", "", v).strip()
        if not v:
            raise ValueError("Name cannot be blank")
        return v

    @field_validator("description")
    @classmethod
    def strip_description(cls, v):
        if v is not None:
            v = re.sub(r"<[^>]+>", "", v).strip() or None
        return v

# Schema for group response (what we send back)
class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: int
    invite_code: str  # ADD THIS LINE
    created_at: UtcDatetime
    
    class Config:
        from_attributes = True

# Schema for creating a bet (what we receive)
class BetCreate(BaseModel):
    acca_id: int
    description: str = Field(min_length=1, max_length=200)
    odds: str = Field(min_length=1, max_length=20)
    event_id: Optional[str] = Field(default=None, max_length=64)
    home_team: Optional[str] = Field(default=None, max_length=100)
    away_team: Optional[str] = Field(default=None, max_length=100)
    pick_type: Optional[str] = None
    sport_key: Optional[str] = Field(default=None, max_length=50)
    commence_time: Optional[str] = Field(default=None, max_length=50)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v):
        # Strip HTML tags to prevent stored XSS
        cleaned = re.sub(r"<[^>]+>", "", v).strip()
        if not cleaned:
            raise ValueError("Description cannot be blank")
        return cleaned

    @field_validator("odds")
    @classmethod
    def odds_must_be_positive(cls, v):
        try:
            val = float(v)
        except (ValueError, TypeError):
            raise ValueError("Odds must be a valid number")
        if not math.isfinite(val) or val < 1.0 or val > 10000:
            raise ValueError("Odds must be between 1.0 and 10,000")
        return v

    @field_validator("pick_type")
    @classmethod
    def validate_pick_type(cls, v):
        if v is not None and v not in ("home", "away", "draw", "btts_yes", "btts_no", "over_2_5", "under_2_5"):
            raise ValueError("pick_type must be 'home', 'away', 'draw', 'btts_yes', 'btts_no', 'over_2_5', or 'under_2_5'")
        return v

    @field_validator("sport_key")
    @classmethod
    def validate_sport_key(cls, v):
        if v is not None and v not in VALID_SPORT_KEYS:
            raise ValueError(f"Unknown sport key: '{v}'")
        return v

# Schema for bet response (what we send back)
class BetResponse(BaseModel):
    id: int
    acca_id: int
    user_id: int
    description: str
    username: str  # Add username so we can display who made the bet!
    odds: str
    result: Optional[str]
    created_at: UtcDatetime
    event_id: Optional[str] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    pick_type: Optional[str] = None
    sport_key: Optional[str] = None
    commence_time: Optional[UtcDatetime] = None

    class Config:
        from_attributes = True

VALID_SPORT_KEYS = {
    "soccer_epl", "soccer_efl_champ", "soccer_england_league1",
    "soccer_england_league2", "soccer_spain_la_liga",
    "soccer_germany_bundesliga", "soccer_italy_serie_a",
    "soccer_france_ligue_one",
}

# Schema for creating an acca (what we receive)
class AccaCreate(BaseModel):
    group_id: int
    name: str = Field(min_length=1, max_length=100)
    match_dates: list[str]  # ["2026-02-08", "2026-02-09"]
    leagues: list[str]  # ["soccer_epl", "soccer_spain_la_liga"]
    bet_type: str = Field(default="h2h")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v):
        v = re.sub(r"<[^>]+>", "", v).strip()
        if not v:
            raise ValueError("Name cannot be blank")
        return v

    @field_validator("bet_type")
    @classmethod
    def validate_bet_type(cls, v):
        allowed = ("h2h", "spreads", "totals")
        if v not in allowed:
            raise ValueError(f"bet_type must be one of: {', '.join(allowed)}")
        return v

    @field_validator("match_dates")
    @classmethod
    def validate_match_dates(cls, v):
        if len(v) < 1:
            raise ValueError("At least 1 match date required")
        if len(v) > 7:
            raise ValueError("Maximum 7 match dates allowed")
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seen = set()
        cleaned = []
        for d in v:
            if not date_pattern.match(d):
                raise ValueError(f"Invalid date format: '{d}'. Use YYYY-MM-DD")
            # Validate it's a real calendar date
            try:
                datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Invalid date: '{d}'")
            # Check not in the past
            if d < today:
                raise ValueError(f"Date '{d}' is in the past")
            # Deduplicate
            if d not in seen:
                seen.add(d)
                cleaned.append(d)
        return cleaned

    @field_validator("leagues")
    @classmethod
    def validate_leagues(cls, v):
        if len(v) < 1:
            raise ValueError("At least 1 league required")
        if len(v) > 5:
            raise ValueError("Maximum 5 leagues allowed")
        for league in v:
            if league not in VALID_SPORT_KEYS:
                raise ValueError(f"Unknown league: '{league}'")
        # Deduplicate while preserving order
        seen = set()
        cleaned = []
        for league in v:
            if league not in seen:
                seen.add(league)
                cleaned.append(league)
        return cleaned

# Schema for acca response (what we send back)
class AccaResponse(BaseModel):
    id: int
    group_id: int
    name: str
    round_number: Optional[int] = None
    first_match_date: Optional[date] = None
    status: str
    match_dates: Optional[list[str]] = None
    leagues: Optional[list[str]] = None
    bet_type: Optional[str] = None
    locks_at: Optional[UtcDatetime] = None
    created_by: Optional[int] = None
    created_at: UtcDatetime

    class Config:
        from_attributes = True

# Schema for acca with bets (full details)
class AccaWithBets(BaseModel):
    id: int
    group_id: int
    name: str
    round_number: Optional[int] = None
    first_match_date: Optional[date] = None
    status: str
    match_dates: Optional[list[str]] = None
    leagues: Optional[list[str]] = None
    bet_type: Optional[str] = None
    locks_at: Optional[UtcDatetime] = None
    created_by: Optional[int] = None
    created_at: UtcDatetime
    bets: list[BetResponse] = []

    class Config:
        from_attributes = True

# Schema for bookmaker click tracking
class BookmakerClickRequest(BaseModel):
    bookmaker_key: str
    acca_id: Optional[int] = None
    source: Optional[str] = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, v):
        if v is not None and v not in ("comparison", "betslip"):
            raise ValueError("source must be 'comparison' or 'betslip'")
        return v


# Schema for account deletion
class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


# Schema for username availability check
class UsernameCheckResponse(BaseModel):
    username: str
    available: bool
    reason: Optional[str] = None

# Push notification schemas
class PushSubscriptionKeys(BaseModel):
    p256dh: str = Field(max_length=256)
    auth: str = Field(max_length=64)

class PushSubscriptionData(BaseModel):
    endpoint: str = Field(max_length=1024)
    expirationTime: Optional[int] = None
    keys: PushSubscriptionKeys

    @field_validator("endpoint")
    @classmethod
    def endpoint_must_be_https(cls, v):
        if not v.startswith("https://"):
            raise ValueError("Push endpoint must be HTTPS")
        return v

class PushSubscriptionCreate(BaseModel):
    subscription: PushSubscriptionData

class PushSubscriptionDelete(BaseModel):
    endpoint: str = Field(max_length=1024)