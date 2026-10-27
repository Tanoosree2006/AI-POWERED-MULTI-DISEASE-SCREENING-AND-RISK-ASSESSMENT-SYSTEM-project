import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.models import AuditEvent, ScreeningRecord, User
from app.services import crud
from conftest import register_and_login

ROOT = Path(__file__).resolve().parents[1]


def test_password_is_hashed_in_db(client, db):
    register_and_login(client, "alice", "correct-horse-1")
    u = db.scalar(select(User).where(User.username == "alice"))
    assert u.password_hash != "correct-horse-1" and u.password_hash.startswith("$2")
    assert verify_password("correct-horse-1", u.password_hash) and not verify_password("wrong", u.password_hash)


def test_unique_username_constraint(db):
    crud.create_user(db, "zed", hash_password("password-123"))
    with pytest.raises(IntegrityError):
        crud.create_user(db, "ZED", hash_password("password-123"))
    db.rollback()


def test_audit_events_written_without_patient_data(client, db, profiles):
    h = register_and_login(client)
    client.post("/api/v1/auth/login", json={"username": "alice", "password": "bad-password"})
    client.post("/api/v1/screening/breast_cancer", json={"features": profiles["malignant"]}, headers=h)
    events = {e.event_type for e in db.scalars(select(AuditEvent))}
    assert {"user_registered", "login_success", "login_failed", "screening_created"} <= events
    assert all("radius" not in e.detail for e in db.scalars(select(AuditEvent)))


def test_model_version_reused_not_duplicated(client, db, profiles):
    h = register_and_login(client)
    for _ in range(3):
        client.post("/api/v1/screening/breast_cancer", json={"features": profiles["benign"]}, headers=h)
    assert len({r.model_version_id for r in db.scalars(select(ScreeningRecord))}) == 1


def test_model_version_stores_evaluation_metrics(client, db, profiles):
    h = register_and_login(client)
    rid = client.post("/api/v1/screening/breast_cancer", json={"features": profiles["benign"]}, headers=h).json()["id"]
    mv = db.get(ScreeningRecord, rid).model_version
    assert mv.metrics and "recall_sensitivity" in mv.metrics


def test_alembic_migration_creates_schema(tmp_path):
    db_file = tmp_path / "mig.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_file}"}
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    tables = {x[0] for x in sqlite3.connect(db_file).execute("select name from sqlite_master where type='table'")}
    assert {"users", "screening_records", "model_versions", "disease_modules", "audit_events"} <= tables
