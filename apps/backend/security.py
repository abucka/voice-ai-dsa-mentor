from collections import defaultdict
from datetime import timedelta, timezone, datetime
import hashlib
import os
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .db_models import AuthToken, User
\

load_dotenv()

_ITERATIONS = 100_000
TOKEN_TTL_HOURS = int(os.environ.get("AUTH_TOKEN_TTL_HOURS", "24"))
SIGNIN_RATE_LIMIT_ATTEMPTS = 5
SIGNIN_RATE_LIMIT_WINDOW_SECONDS = 60
_signin_attempts: dict[str, list[float]] = defaultdict(list)

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$")
    except ValueError:
        return False

    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return actual == expected

def require_authenticated_user(authorization: str | None, db: Session) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token")

    token = authorization[7:].strip()
    auth_token = db.get(AuthToken, token)
    if not auth_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    expires_at = auth_token.created_at + timedelta(hours=TOKEN_TTL_HOURS)
    if datetime.now(timezone.utc) > expires_at.replace(tzinfo=timezone.utc):
        db.delete(auth_token)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.get(User, auth_token.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user


def check_signin_rate_limit(email: str) -> None:
    now = time.monotonic()
    attempts = _signin_attempts[email]
    attempts[:] = [attempt for attempt in attempts if now - attempt < SIGNIN_RATE_LIMIT_WINDOW_SECONDS]
    if len(attempts) >= SIGNIN_RATE_LIMIT_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Please try again shortly.")
    attempts.append(now)