"""Password hashing and JWT helpers.

Uses the `bcrypt` package directly (compatible with bcrypt 4.x and 5.x).
Passlib is avoided: passlib 1.7.4 breaks on bcrypt 5.x (removed __about__).
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

_DEFAULT_SECRET = "change-me-in-production-use-openssl-rand-hex-32"
SECRET_KEY = os.getenv("JWT_SECRET", _DEFAULT_SECRET)
if SECRET_KEY == _DEFAULT_SECRET:
    logger.warning(
        "JWT_SECRET is not set — using insecure default. "
        "Set JWT_SECRET in your .env (run: openssl rand -hex 32)."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(sub: str, user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": sub, "uid": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
