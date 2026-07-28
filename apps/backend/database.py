import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "app.db"

# Allow overriding the database (e.g. an in-memory or temp sqlite file for tests, or a
# real Postgres URL in production) without touching this module.
DATABASE_URL = os.environ.get("DATABASE_URL")

engine_kwargs: dict[str, object] = {}
if DATABASE_URL:
    if DATABASE_URL.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if DATABASE_URL in ("sqlite://", "sqlite:///:memory:"):
            # A single shared in-memory connection so all sessions see the same data.
            engine_kwargs["poolclass"] = StaticPool
else:
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH}"
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
