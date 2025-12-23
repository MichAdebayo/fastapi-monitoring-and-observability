from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel
from app.database import engine
from app.routes import items_router
import os
from typing import AsyncGenerator
from prometheus_fastapi_instrumentator import Instrumentator
from app.monitoring.metrics import app_info

# Initialize central logging as early as possible so module logs go into the
# project `logs/app.log` file (rotating).
from app.logging_config import setup_logging
import logging
import asyncio
import time
from sqlalchemy import text

setup_logging()

# API logger for route-level contextual messages
logger = logging.getLogger("api")
db_logger = logging.getLogger("db")

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t")


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
    # Wait for Postgres to become ready (compose healthcheck helps, but
    # perform proactive retries so the app doesn't crash on cold start).
    def wait_for_db_sync(engine, timeout: int = 60, interval: float = 1.0):
        end = time.time() + timeout
        while True:
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                db_logger.info("Database is reachable")
                return
            except Exception as exc:
                if time.time() > end:
                    db_logger.error(
                        "Database not reachable after %s seconds: %s", timeout, exc
                    )
                    raise
                db_logger.info("Waiting for database to be ready: %s", exc)
                time.sleep(interval)

    async def wait_for_db(engine, timeout: int = 60, interval: float = 1.0):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, wait_for_db_sync, engine, timeout, interval)

    await wait_for_db(engine, timeout=60)

    SQLModel.metadata.create_all(engine)
    # Log an actionable startup message including database hint
    try:
        logger.info(
            "Application startup: DB tables ensured (url=%s)",
            getattr(engine, "url", "<unknown>"),
        )
    except Exception:
        logger.info("Application startup: DB tables ensured (url=<masked>)")
    yield


app = FastAPI(
    title="Items CRUD API",
    description="API for managing items with full CRUD operations and monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

# 📊 Instrumentation automatique
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
)
instrumentator.instrument(app).expose(app, endpoint="/metrics")

app.include_router(items_router)


@app.get("/")
def root() -> dict:
    logger.info("Root endpoint accessed")
    return {"message": "Items CRUD API"}


@app.get("/health")
def health() -> dict:
    logger.info("Health check OK")
    return {"status": "healthy"}
