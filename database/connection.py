import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set.")

# pool_pre_ping : évite les erreurs sur des connexions coupées par Postgres
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> None:
    """Vérifie que la base répond. Le schéma est géré par Alembic
    (alembic upgrade head), plus par create_all au démarrage."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database connection failed")
        raise
    logger.info("Database connection OK")


def db_is_healthy() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - toute erreur = base indisponible
        return False
