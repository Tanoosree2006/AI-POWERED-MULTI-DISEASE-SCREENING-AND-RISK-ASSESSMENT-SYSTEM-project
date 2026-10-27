"""Shared dependencies: current user, admin check, in-memory rate limiter."""
import time
from collections import defaultdict, deque

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.database import get_db
from app.models import User

_bearer = HTTPBearer(auto_error=False)
_UNAUTH = {"WWW-Authenticate": "Bearer"}


class RateLimiter:
    """Sliding-window limiter per client IP and path. Prototype-grade: single process only."""

    def __init__(self):
        self.hits = defaultdict(deque)

    def allow(self, key: str, limit: int, window: float = 60.0) -> bool:
        now = time.monotonic()
        dq = self.hits[key]
        while dq and now - dq[0] > window:
            dq.popleft()
        if len(dq) >= limit:
            return False
        dq.append(now)
        return True

    def reset(self):
        self.hits.clear()


limiter = RateLimiter()


def rate_limit(request: Request):
    key = f"{request.client.host if request.client else 'unknown'}:{request.url.path}"
    if not limiter.allow(key, settings.rate_limit_per_minute):
        raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": "60"})


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
                 db: Session = Depends(get_db)) -> User:
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated", headers=_UNAUTH)
    try:
        payload = decode_access_token(creds.credentials)
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers=_UNAUTH)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers=_UNAUTH)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return user
