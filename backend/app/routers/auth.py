from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import timedelta, datetime, timezone
import secrets
import re
import logging
import hmac
from .. import models, schemas, auth
from ..database import get_db
from ..limiter import limiter
from ..email import send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)


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
    existing_email = db.query(models.User).filter(func.lower(models.User.email) == user.email.lower()).first()
    if existing_email:
        if existing_email.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email or username already exists"
            )
        else:
            # Overwrite unverified account — prevents squatting
            db.delete(existing_email)
            db.flush()

    # Check if username already exists (case-insensitive)
    existing_username = db.query(models.User).filter(func.lower(models.User.username) == user.username.lower()).first()
    if existing_username:
        if existing_username.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email or username already exists"
            )
        else:
            # Overwrite unverified account — prevents squatting
            db.delete(existing_username)
            db.flush()

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
    try:
        send_verification_email(user.email, verification_code, user.username)
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again."
        )

    return {
        "message": "Account created. Please check your email for verification code.",
        "email": user.email,
        "requires_verification": True
    }


# Check username availability endpoint
@router.get("/auth/check-username", response_model=schemas.UsernameCheckResponse)
@limiter.limit("20/minute")
def check_username(request: Request, username: str, db: Session = Depends(get_db)):
    """Check if a username is available"""

    # Validate username format
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return {
            "username": username,
            "available": False,
            "reason": "Username must be 3-20 characters using letters, numbers, and underscores only"
        }

    if len(username) < 3 or len(username) > 20:
        return {
            "username": username,
            "available": False,
            "reason": "Username must be 3-20 characters using letters, numbers, and underscores only"
        }

    # Case-insensitive database lookup (only verified users)
    existing = db.query(models.User).filter(
        func.lower(models.User.username) == username.lower(),
        models.User.email_verified == True
    ).first()

    return {
        "username": username,
        "available": existing is None
    }


# Login endpoint
@router.post("/auth/login", response_model=schemas.Token)
@limiter.limit("10/minute")
def login(request: Request, credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login with email or username"""

    # Find user by email OR username (case-insensitive)
    identifier_lower = credentials.identifier.lower()
    user = db.query(models.User).filter(
        (func.lower(models.User.email) == identifier_lower) |
        (func.lower(models.User.username) == identifier_lower)
    ).first()

    # Check if user exists
    if not user:
        # Constant-time: always run bcrypt to prevent timing-based user enumeration
        auth.verify_password("dummy", "$2b$12$LJ3m4ys3Lg2HvSSvfOEqWOsonRUKDSCMIYPSYzPF1vFfGo/MlJl5e")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check account lockout (reset counter if lockout has expired)
    if user.locked_until:
        if datetime.now(timezone.utc) < user.locked_until:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account temporarily locked. Try again later."
            )
        else:
            # Lockout expired — reset counter
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()

    # Verify password
    if not auth.verify_password(credentials.password, user.hashed_password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 10:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.commit()
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

    # Reset failed login attempts on success
    if user.failed_login_attempts:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

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
@limiter.limit("5/minute")
def verify_email(request: Request, data: schemas.VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify email with 6-digit code"""

    user = db.query(models.User).filter(func.lower(models.User.email) == data.email.lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification request"
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification request"
        )

    # Check account lockout
    if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account temporarily locked. Try again later."
        )

    # Brute-force protection: max 5 attempts
    if user.verification_attempts >= 5:
        # Invalidate the code entirely
        user.verification_code = None
        user.verification_code_expires = None
        user.verification_attempts = 0
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many failed attempts. Please request a new verification code."
        )

    # Check expiry BEFORE code comparison
    if user.verification_code_expires and datetime.now(timezone.utc) > user.verification_code_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Please request a new one."
        )

    # Check code (constant-time comparison)
    if not hmac.compare_digest(user.verification_code or "", data.code):
        user.verification_attempts = (user.verification_attempts or 0) + 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    # Mark as verified
    user.email_verified = True
    user.verification_code = None
    user.verification_code_expires = None
    user.verification_attempts = 0
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

    user = db.query(models.User).filter(func.lower(models.User.email) == data.email.lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request"
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request"
        )

    # Check account lockout
    if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account temporarily locked. Try again later."
        )

    # Generate new code
    verification_code = generate_verification_code()
    code_expires = datetime.now(timezone.utc) + timedelta(minutes=15)

    user.verification_code = verification_code
    user.verification_code_expires = code_expires
    # Don't reset verification_attempts — persist across resends
    db.commit()

    # Send verification email
    try:
        send_verification_email(user.email, verification_code, user.username)
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again."
        )

    return {
        "message": "Verification code sent. Please check your email.",
        "email": user.email,
        "requires_verification": True
    }


# Forgot password endpoint
@router.post("/auth/forgot-password")
@limiter.limit("3/minute")
def forgot_password(request: Request, data: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset code (anti-enumeration protection)"""

    search_email = data.email.strip().lower()
    user = db.query(models.User).filter(func.lower(models.User.email) == search_email).first()

    # Anti-enumeration: return success even if user not found or not verified
    if not user or not user.email_verified:
        return {"message": "If an account exists with that email, a reset code has been sent."}

    # Generate reset code
    reset_code = generate_verification_code()
    code_expires = datetime.now(timezone.utc) + timedelta(minutes=15)

    user.verification_code = reset_code
    user.verification_code_expires = code_expires
    # Don't reset verification_attempts — persist across new requests
    db.commit()

    # Send reset email
    try:
        send_password_reset_email(user.email, reset_code, user.username)
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email. Please try again."
        )

    return {"message": "If an account exists with that email, a reset code has been sent."}


# Reset password endpoint
@router.post("/auth/reset-password")
@limiter.limit("5/minute")
def reset_password(request: Request, data: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password with verification code"""

    user = db.query(models.User).filter(func.lower(models.User.email) == data.email.lower()).first()
    if not user or not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )

    # Check account lockout
    if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account temporarily locked. Try again later."
        )

    # Brute-force protection: max 5 attempts
    if user.verification_attempts >= 5:
        user.verification_code = None
        user.verification_code_expires = None
        user.verification_attempts = 0
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many failed attempts. Please request a new reset code."
        )

    # Check expiry BEFORE code comparison
    if not user.verification_code_expires or datetime.now(timezone.utc) > user.verification_code_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code expired. Please request a new one."
        )

    # Check code (constant-time comparison)
    if not hmac.compare_digest(user.verification_code or "", data.code):
        user.verification_attempts = (user.verification_attempts or 0) + 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )

    # Hash new password
    user.hashed_password = auth.hash_password(data.new_password)

    # Clear verification code
    user.verification_code = None
    user.verification_code_expires = None
    user.verification_attempts = 0
    db.commit()

    return {"message": "Password reset successful. You can now log in."}


# Change password endpoint
@router.put("/auth/change-password")
@limiter.limit("5/minute")
def change_password(
    request: Request,
    data: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Change password for authenticated user"""

    # Fetch user from database
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check account lockout
    if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account temporarily locked. Try again later."
        )

    # Verify current password
    if not auth.verify_password(data.current_password, user.hashed_password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 10:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Reset failed attempts on success
    if user.failed_login_attempts:
        user.failed_login_attempts = 0
        user.locked_until = None

    # Hash new password
    user.hashed_password = auth.hash_password(data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


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


# Delete account endpoint
@router.post("/auth/delete-account")
@limiter.limit("3/minute")
def delete_account(
    request: Request,
    data: schemas.DeleteAccountRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Delete user account and all associated data (irreversible)"""

    try:
        # Get user
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify password
        if not auth.verify_password(data.password, user.hashed_password):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 10:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )

        # Get all groups where user is a member
        memberships = db.query(models.GroupMember).filter(
            models.GroupMember.user_id == user_id
        ).all()

        # Process each membership
        for membership in memberships:
            group = db.query(models.Group).filter(models.Group.id == membership.group_id).first()
            if not group:
                continue

            # Count other members in the group
            other_members = db.query(models.GroupMember).filter(
                models.GroupMember.group_id == group.id,
                models.GroupMember.user_id != user_id
            ).all()

            if not other_members:
                # User is sole member - delete everything
                # Delete all bets in group's accas
                acca_ids = [a.id for a in group.accas]
                if acca_ids:
                    db.query(models.Bet).filter(models.Bet.acca_id.in_(acca_ids)).delete(synchronize_session=False)
                # Delete all accas
                db.query(models.Acca).filter(models.Acca.group_id == group.id).delete(synchronize_session=False)
                # Delete all memberships
                db.query(models.GroupMember).filter(models.GroupMember.group_id == group.id).delete(synchronize_session=False)
                # Delete group
                db.delete(group)
            else:
                # Other members exist
                # If user is admin, promote longest-serving member
                if membership.role == "admin":
                    new_admin = min(other_members, key=lambda m: m.joined_at)
                    new_admin.role = "admin"

                    # Transfer Group.created_by if needed
                    if group.created_by == user_id:
                        group.created_by = new_admin.user_id

                    # Transfer Acca.created_by for accas in this group
                    db.query(models.Acca).filter(
                        models.Acca.group_id == group.id,
                        models.Acca.created_by == user_id
                    ).update({"created_by": new_admin.user_id}, synchronize_session=False)

                # Delete user's bets from ALL accas in this group
                # Note: This includes locked/settled accas due to FK constraint (Bet.user_id NOT NULL)
                acca_ids = [a.id for a in group.accas]
                if acca_ids:
                    db.query(models.Bet).filter(
                        models.Bet.acca_id.in_(acca_ids),
                        models.Bet.user_id == user_id
                    ).delete(synchronize_session=False)

                # Delete the membership
                db.delete(membership)

        # Nullify BookmakerClick.user_id (no FK, just analytics cleanup)
        try:
            db.query(models.BookmakerClick).filter(
                models.BookmakerClick.user_id == user_id
            ).update({"user_id": None}, synchronize_session=False)
        except Exception:
            pass  # Non-critical cleanup — don't block account deletion

        # Delete the user (CASCADE will handle remaining relationships)
        db.delete(user)

        # Commit all changes in one transaction
        db.commit()

        return {"message": "Account deleted successfully"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete account for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )
