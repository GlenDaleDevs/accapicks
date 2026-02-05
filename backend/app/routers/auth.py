from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta, datetime, timezone
import secrets
from .. import models, schemas, auth
from ..database import get_db
from ..limiter import limiter
from ..email import send_verification_email


def generate_verification_code() -> str:
    """Generate a 6-digit verification code."""
    return str(secrets.randbelow(900000) + 100000)

router = APIRouter()


# Dependency to get current user from Authorization header
def get_current_user(authorization: Optional[str] = Header(None)) -> int:
    """Extract user_id from Bearer token in Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Authorization header format: "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication format"
        )

    token = parts[1]
    return auth.get_current_user_id(token)


# Signup endpoint
@router.post("/auth/signup", response_model=schemas.SignupResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def signup(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user account (requires email verification)"""

    # Check if email already exists
    existing_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Generate verification code
    verification_code = generate_verification_code()
    code_expires = datetime.now(timezone.utc) + timedelta(minutes=15)

    # Create new user with hashed password (unverified)
    hashed_password = auth.hash_password(user.password)
    new_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        email_verified=False,
        verification_code=verification_code,
        verification_code_expires=code_expires
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send verification email
    send_verification_email(user.email, verification_code, user.username)

    return {
        "message": "Account created. Please check your email for verification code.",
        "email": user.email,
        "requires_verification": True
    }


# Login endpoint
@router.post("/auth/login", response_model=schemas.Token)
@limiter.limit("10/minute")
def login(request: Request, credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login with email or username"""

    # Find user by email OR username
    user = db.query(models.User).filter(
        (models.User.email == credentials.identifier) |
        (models.User.username == credentials.identifier)
    ).first()

    # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not auth.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Block unverified users
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )

    # Create access token
    access_token = auth.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


# Verify email endpoint
@router.post("/auth/verify-email", response_model=schemas.Token)
@limiter.limit("10/minute")
def verify_email(request: Request, data: schemas.VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify email with 6-digit code"""

    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )

    # Check code
    if user.verification_code != data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    # Check expiry
    if user.verification_code_expires and datetime.now(timezone.utc) > user.verification_code_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Please request a new one."
        )

    # Mark as verified
    user.email_verified = True
    user.verification_code = None
    user.verification_code_expires = None
    db.commit()
    db.refresh(user)

    # Create access token
    access_token = auth.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


# Resend verification code endpoint
@router.post("/auth/resend-code", response_model=schemas.SignupResponse)
@limiter.limit("3/minute")
def resend_code(request: Request, data: schemas.ResendCodeRequest, db: Session = Depends(get_db)):
    """Resend verification code to email"""

    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )

    # Generate new code
    verification_code = generate_verification_code()
    code_expires = datetime.now(timezone.utc) + timedelta(minutes=15)

    user.verification_code = verification_code
    user.verification_code_expires = code_expires
    db.commit()

    # Send verification email
    send_verification_email(user.email, verification_code, user.username)

    return {
        "message": "Verification code sent. Please check your email.",
        "email": user.email,
        "requires_verification": True
    }


# Get current user profile
@router.get("/auth/me", response_model=schemas.UserResponse)
def get_me(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get current user profile based on JWT token"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
