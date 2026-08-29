import os
import uuid
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import PyJWTError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import bcrypt  # kept for legacy hash migration only
from typing import Optional

# Load environment variables
load_dotenv()

# JWT (JSON Web Token) configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set. Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")
ALGORITHM = "HS256"
# 30 days — keeps people signed in between visits rather than every 30 minutes.
# Trade-off: a longer-lived token in localStorage is exposed for longer if ever
# leaked. Accepted for a no-money social app with no XSS vectors and a blacklist
# that revokes on logout/password change. A refresh-token scheme is the proper
# fix if this ever needs tightening (see whereweare.md backlog).
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

# Argon2id password hasher (OWASP recommended)
ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)


def hash_password(password: str) -> str:
    """Hash a password using argon2id"""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash. Supports both argon2 and legacy bcrypt."""
    if hashed_password.startswith(("$2b$", "$2a$")):
        # Legacy bcrypt hash — verify with bcrypt
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    # Argon2 hash
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Check if a password hash needs to be upgraded from bcrypt to argon2."""
    return hashed_password.startswith(("$2b$", "$2a$"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a JWT token that expires after a certain time"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """Decodes and verifies a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        return None
# Get current user from token (for FastAPI dependency injection)
def get_current_user_id(token: str) -> int:
    """Extracts user_id from JWT token. Raises exception if invalid."""
    from fastapi import HTTPException, status
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return int(user_id)
