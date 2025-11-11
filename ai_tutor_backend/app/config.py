import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv, find_dotenv


# Load .env if present (development); Render uses environment variables directly.
load_dotenv(find_dotenv(), override=False)


def _normalize_database_url(raw_url: str | None) -> str | None:
    """
    Ensure DATABASE_URL uses the SQLAlchemy psycopg3 driver.
    Render supplies URLs in the form postgres://... which need to become
    postgresql+psycopg://... for SQLAlchemy 2.x + psycopg 3.
    """
    if not raw_url:
        return None

    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = "postgresql+psycopg://" + url[len("postgresql://") :]

    return url


class Config:
    # Flask config
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

    # Database config
    _default_sqlite_path = Path(__file__).resolve().parent.parent / "instance" / "ai_tutor.db"
    SQLALCHEMY_DATABASE_URI = (
        _normalize_database_url(os.getenv("DATABASE_URL"))
        or f"sqlite:///{_default_sqlite_path}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {}
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "pool_size": 5,
            "max_overflow": 10,
        }

    # JWT config
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

