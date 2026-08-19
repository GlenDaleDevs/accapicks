import os
import math
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from .database import engine, Base, SessionLocal
from .timeutils import as_utc
from .fixturelist import refresh_fixture_list
from .standings import refresh_standings
from .autoweek import auto_create_weeks
from . import models
from .routers import auth, groups, accas, bets, odds, affiliate, notifications
from .limiter import limiter
from .logging_config import setup_logging

load_dotenv()

# Setup logging before anything else
setup_logging()
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app):
    logger.info("Starting background tasks")
    lock_task = asyncio.create_task(auto_lock_accas())
    settle_task = asyncio.create_task(auto_settle_bets())
    cleanup_task = asyncio.create_task(cleanup_verification_codes())
    blacklist_task = asyncio.create_task(cleanup_blacklisted_tokens())
    standings_task = asyncio.create_task(refresh_standings())
    fixtures_task = asyncio.create_task(refresh_fixture_list())
    week_task = asyncio.create_task(auto_create_weeks())
    yield
    logger.info("Shutting down background tasks")
    lock_task.cancel()
    settle_task.cancel()
    cleanup_task.cancel()
    blacklist_task.cancel()
    standings_task.cancel()
    fixtures_task.cancel()
    week_task.cancel()

# Custom rate limit handler
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    retry_after = 60  # default fallback
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please try again shortly.",
            "retry_after": retry_after
        },
        headers={"Retry-After": str(retry_after)}
    )

# Create the FastAPI app
is_production = os.getenv("ENVIRONMENT", "").lower() == "production"
app = FastAPI(
    title="AccaPicks API",
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.headers.get("x-forwarded-proto") == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' https://www.google-analytics.com https://www.googletagmanager.com; "
        "worker-src 'self'; "
        "frame-ancestors 'none'"
    )
    return response

# Request size limit middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        content_length = request.headers.get("content-length")
        try:
            if content_length and int(content_length) > 1_048_576:  # 1MB
                return JSONResponse(status_code=413, content={"detail": "Request body too large"})
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header"})
    return await call_next(request)

# CORS - allowed origins for frontend
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("FORCE_HTTPS", "").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)

# Include all routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(groups.router, prefix="/api", tags=["groups"])
app.include_router(accas.router, prefix="/api", tags=["accas"])
app.include_router(bets.router, prefix="/api", tags=["bets"])
app.include_router(odds.router, prefix="/api", tags=["odds"])
app.include_router(affiliate.router, prefix="/api", tags=["affiliate"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])

# Background task: auto-lock accas when locks_at time has passed
async def auto_lock_accas():
    while True:
        await asyncio.sleep(60)  # Check every 60 seconds
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            open_accas = db.query(models.Acca).filter(
                models.Acca.status == "open",
                models.Acca.locks_at.isnot(None),
            ).all()
            locked_count = 0
            deleted_low_participation = 0
            for acca in open_accas:
                if acca.locks_at and as_utc(acca.locks_at) <= now:
                    # Check participation before locking
                    member_count = db.query(models.GroupMember).filter(
                        models.GroupMember.group_id == acca.group_id
                    ).count()
                    bet_count = db.query(models.Bet).filter(
                        models.Bet.acca_id == acca.id
                    ).count()
                    threshold = math.ceil(member_count / 2)

                    if bet_count < threshold:
                        # Delete bets and acca — not enough participation
                        db.query(models.Bet).filter(models.Bet.acca_id == acca.id).delete()
                        db.delete(acca)
                        deleted_low_participation += 1
                        logger.info(
                            f"Deleted acca {acca.name} (group {acca.group_id}): "
                            f"{bet_count}/{member_count} members picked (<50%)"
                        )
                    else:
                        acca.status = "locked"
                        locked_count += 1

            # Cleanup: delete locked/settled accas that have 0 bets (orphaned by member removal)
            locked_accas = db.query(models.Acca).filter(
                models.Acca.status.in_(["locked", "settled"])
            ).all()
            deleted_count = 0
            for acca in locked_accas:
                bet_count = db.query(models.Bet).filter(models.Bet.acca_id == acca.id).count()
                if bet_count == 0:
                    db.delete(acca)
                    deleted_count += 1

            db.commit()
            if locked_count > 0:
                logger.info(f"Auto-locked {locked_count} acca(s)")
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} empty locked acca(s)")
            if deleted_low_participation > 0:
                logger.info(f"Deleted {deleted_low_participation} acca(s) with <50% participation")
        except Exception as e:
            logger.error(f"Auto-lock error: {e}")
            db.rollback()
        finally:
            db.close()

# Background task: auto-settle locked accas
async def auto_settle_bets():
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        db = SessionLocal()
        try:
            from .settlement import settle_locked_accas
            settle_locked_accas(db)
        except Exception as e:
            logger.error(f"Error in auto settle: {e}")
            db.rollback()
        finally:
            db.close()

# Background task: cleanup expired verification codes and stale unverified accounts
async def cleanup_verification_codes():
    while True:
        await asyncio.sleep(3600)  # Every hour
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)

            # Expire old verification codes
            expired_codes = db.query(models.User).filter(
                models.User.verification_code.isnot(None),
                models.User.verification_code_expires < now
            ).update({
                "verification_code": None,
                "verification_code_expires": None
            }, synchronize_session=False)

            if expired_codes > 0:
                logger.info(f"Expired {expired_codes} verification code(s)")

            # Delete stale unverified accounts (24+ hours old, no activity)
            cutoff_time = now - timedelta(hours=24)
            stale_users = db.query(models.User).filter(
                models.User.email_verified == False,
                models.User.created_at < cutoff_time
            ).all()

            deleted_count = 0
            for user in stale_users:
                # Safety check: no bets and no group memberships
                has_bets = db.query(models.Bet).filter(models.Bet.user_id == user.id).count() > 0
                has_memberships = db.query(models.GroupMember).filter(models.GroupMember.user_id == user.id).count() > 0

                has_accas = db.query(models.Acca).filter(models.Acca.created_by == user.id).count() > 0

                if not has_bets and not has_memberships and not has_accas:
                    db.delete(user)
                    deleted_count += 1

            db.commit()

            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} stale unverified account(s)")

        except Exception as e:
            logger.error(f"Error in verification cleanup: {e}")
            db.rollback()
        finally:
            db.close()

# Background task: cleanup expired blacklisted tokens
async def cleanup_blacklisted_tokens():
    while True:
        await asyncio.sleep(3600)  # Every hour
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            deleted = db.query(models.BlacklistedToken).filter(
                models.BlacklistedToken.expires_at < now
            ).delete(synchronize_session=False)
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} expired blacklisted token(s)")

            # Cleanup stale push subscriptions (90+ days old: never used or abandoned)
            from sqlalchemy import or_
            stale_cutoff = now - timedelta(days=90)
            stale_subs = db.query(models.PushSubscription).filter(
                or_(
                    models.PushSubscription.last_used_at.is_(None),
                    models.PushSubscription.last_used_at < stale_cutoff,
                ),
                models.PushSubscription.created_at < stale_cutoff,
            ).delete(synchronize_session=False)
            if stale_subs > 0:
                logger.info(f"Cleaned up {stale_subs} stale push subscription(s)")

            db.commit()
        except Exception as e:
            logger.error(f"Error cleaning up blacklisted tokens: {e}")
            db.rollback()
        finally:
            db.close()

# Health check
@app.get("/api/health")
@limiter.limit("30/minute")
def health_check(request: Request):
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "unreachable"})

# Serve frontend static files
DIST_DIR = Path(__file__).resolve().parent.parent.parent / "dist"

if DIST_DIR.is_dir():
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    # SPA catch-all: serve index.html for all non-API, non-file routes
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        # If the path points to an actual file in dist, serve it
        file_path = DIST_DIR / path
        if file_path.is_file():
            media_type = None
            if path.endswith(".webp"):
                media_type = "image/webp"
            elif path.endswith(".webmanifest"):
                media_type = "application/manifest+json"
            return FileResponse(file_path, media_type=media_type)
        # Otherwise serve index.html for client-side routing
        return FileResponse(DIST_DIR / "index.html")


