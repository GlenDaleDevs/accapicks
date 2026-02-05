from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
import re

# Schema for user registration (what we receive)
class UserCreate(BaseModel):
    email: EmailStr  # Validates it's a proper email format
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

# Schema for user login (what we receive)
class UserLogin(BaseModel):
    identifier: str  # Can be email or username
    password: str


# Schema for user response (what we send back, no password!)
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    email_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True  # Allows SQLAlchemy models to work with Pydantic


# Schema for email verification request
class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


# Schema for resend verification code request
class ResendCodeRequest(BaseModel):
    email: EmailStr


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

# Schema for group response (what we send back)
class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: int
    invite_code: str  # ADD THIS LINE
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schema for creating a bet (what we receive)
class BetCreate(BaseModel):
    acca_id: int
    description: str = Field(min_length=1, max_length=200)
    odds: str = Field(min_length=1, max_length=20)

    @field_validator("odds")
    @classmethod
    def odds_must_be_positive(cls, v):
        try:
            val = float(v)
            if val <= 0:
                raise ValueError
        except ValueError:
            raise ValueError("Odds must be a positive number")
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
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schema for creating an acca (what we receive)
class AccaCreate(BaseModel):
    group_id: int
    name: str
    match_dates: list[str]  # ["2026-02-08", "2026-02-09"]
    leagues: list[str]  # ["soccer_epl", "soccer_spain_la_liga"]
    bet_type: str = "h2h"

# Schema for acca response (what we send back)
class AccaResponse(BaseModel):
    id: int
    group_id: int
    name: str
    status: str
    match_dates: Optional[list[str]] = None
    leagues: Optional[list[str]] = None
    bet_type: Optional[str] = None
    locks_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Schema for acca with bets (full details)
class AccaWithBets(BaseModel):
    id: int
    group_id: int
    name: str
    status: str
    match_dates: Optional[list[str]] = None
    leagues: Optional[list[str]] = None
    bet_type: Optional[str] = None
    locks_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    bets: list[BetResponse] = []

    class Config:
        from_attributes = True

# Schema for updating bet result (what we receive)
class BetResultUpdate(BaseModel):
    result: str

    @field_validator("result")
    @classmethod
    def result_must_be_valid(cls, v):
        if v not in ("won", "lost", "void"):
            raise ValueError("Result must be 'won', 'lost', or 'void'")
        return v