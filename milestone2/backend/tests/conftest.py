import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.api.deps import limiter  # noqa: E402
from app import models as _models  # noqa: E402,F401
from app.services import ml_service  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    """Ensure the ML artifact exists (train once on a fresh clone)."""
    ml_service._ensure_ml_path()
    import config
    if not config.MODEL_PATH.exists():
        import train
        train.main()


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def client(session_factory):
    def override():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()
    fastapi_app.dependency_overrides[get_db] = override
    limiter.reset()
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def db(session_factory):
    s = session_factory()
    yield s
    s.close()


@pytest.fixture(scope="session")
def profiles():
    ml_service._ensure_ml_path()
    from data import load_data
    X, y = load_data()
    return {"malignant": X[y == 1].mean().to_dict(), "benign": X[y == 0].mean().to_dict()}


def register_and_login(client, username="alice", password="correct-horse-1"):
    client.post("/api/v1/auth/register", json={"username": username, "password": password})
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth(client):
    return register_and_login(client)
