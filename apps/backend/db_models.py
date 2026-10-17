from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    last_problem_id: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

class SolvedProblems(Base):
    __tablename__ = "solved_problems"

    problem_id: Mapped[int] = mapped_column(Integer, default=0, primary_key=True)
    solution: Mapped[str] = mapped_column(String, default="", nullable=False)
    is_solved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
