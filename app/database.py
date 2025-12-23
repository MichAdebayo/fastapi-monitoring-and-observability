"""Configuration de la base de données et gestion des sessions.

Ce module gère la connexion à la base de données PostgreSQL
et fournit une fonction générateur pour obtenir des sessions de base de données.
"""

from sqlmodel import create_engine, Session
from typing import Generator
import os
import logging

logger = logging.getLogger("db")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/items_db"
)

POOL_SIZE = 10

engine = create_engine(DATABASE_URL)
try:
    # Log engine creation without leaking credentials
    safe_url = str(getattr(engine, "url", "<unknown>")).replace("//", "//****:****@")
    logger.info("Database engine created (url=%s)", safe_url)
except Exception:
    logger.info("Database engine created (url=<masked>)")


def get_db() -> Generator[Session, None, None]:
    try:
        with Session(engine) as session:
            yield session
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to open DB session: %s", exc)
        raise
