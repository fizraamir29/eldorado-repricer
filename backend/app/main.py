"""
Application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

Or via Docker Compose (see docker-compose.yml at project root).
"""
import logging
from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import configure_logging
from app.database import engine, Base
from app.scheduler import start_scheduler, scheduler
from app.routers import auth, listings, rules, history, notifications, ws, analytics

configure_logging()
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.environment == "development":
        # Convenience for local dev only. In production, run
        # `alembic upgrade head` before starting the container instead —
        # see migrations/ and the README.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Development mode: tables created via create_all().")
    else:
        logger.info("Production mode: expecting schema to be managed by Alembic migrations.")

    start_scheduler()
    logger.info("App startup complete.")
    yield
    scheduler.shutdown(wait=False)
    logger.info("App shutdown complete.")


app = FastAPI(title="Eldorado Automated Repricing API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # set CORS_ALLOWED_ORIGINS in .env — no wildcard in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(listings.router)
app.include_router(rules.router)
app.include_router(history.router)
app.include_router(notifications.router)
app.include_router(analytics.router)
app.include_router(ws.router)


@app.get("/")
async def root():
    return {
        "name": "Eldorado Automated Repricing API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


