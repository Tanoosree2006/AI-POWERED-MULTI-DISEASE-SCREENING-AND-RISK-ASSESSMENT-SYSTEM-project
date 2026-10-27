"""Password hashing (bcrypt) and JWT access tokens."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = "HS256"
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str | None) -> bool:
    """Always performs a bcrypt check so unknown users cost the same time."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), (hashed or _DUMMY_HASH).encode()) and hashed is not None
    except ValueError:
        return False


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "exp": datetime.now(timezone.utc) + expires}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM), int(expires.total_seconds())


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
