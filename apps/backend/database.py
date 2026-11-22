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


def ensure_solved_problems_language_support() -> None:
    if not DATABASE_URL or not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        table_exists = connection.exec_driver_sql(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='solved_problems'"
        ).fetchone()
        if not table_exists:
            return

        columns = connection.exec_driver_sql("PRAGMA table_info(solved_problems)").fetchall()
        if any(column[1] == "language" for column in columns):
            return

        legacy_rows = connection.exec_driver_sql(
            "SELECT problem_id, solution, is_solved FROM solved_problems"
        ).fetchall()

        connection.exec_driver_sql("DROP TABLE IF EXISTS solved_problems_legacy")
        connection.exec_driver_sql("ALTER TABLE solved_problems RENAME TO solved_problems_legacy")
        connection.exec_driver_sql(
            """
            CREATE TABLE solved_problems (
                problem_id INTEGER NOT NULL,
                language TEXT NOT NULL DEFAULT 'python',
                solution TEXT NOT NULL DEFAULT '',
                is_solved BOOLEAN NOT NULL DEFAULT 0,
                PRIMARY KEY (problem_id, language)
            )
            """
        )

        for problem_id, solution, is_solved in legacy_rows:
            connection.exec_driver_sql(
                "INSERT INTO solved_problems (problem_id, language, solution, is_solved) VALUES (?, 'python', ?, ?)",
                (problem_id, solution, bool(is_solved)),
            )

        connection.exec_driver_sql("DROP TABLE solved_problems_legacy")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

