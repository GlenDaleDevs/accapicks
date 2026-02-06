import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from .database import engine, Base, SessionLocal
from . import models
from .routers import auth, groups, accas, bets, odds, users, affiliate
from .limiter import limiter

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app):
    lock_task = asyncio.create_task(auto_lock_accas())
    settle_task = asyncio.create_task(auto_settle_bets())
    yield
    lock_task.cancel()
    settle_task.cancel()

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
app = FastAPI(title="AccaPicks API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

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
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(affiliate.router, prefix="/api", tags=["affiliate"])

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
            for acca in open_accas:
                if acca.locks_at and acca.locks_at <= now:
                    acca.status = "locked"
            db.commit()
        except Exception as e:
            print(f"Auto-lock error: {e}")
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
            print(f"Error in auto settle: {e}")
        finally:
            db.close()

# Health check
@app.get("/api/health")
def health_check():
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
            return FileResponse(file_path)
        # Otherwise serve index.html for client-side routing
        return FileResponse(DIST_DIR / "index.html")


