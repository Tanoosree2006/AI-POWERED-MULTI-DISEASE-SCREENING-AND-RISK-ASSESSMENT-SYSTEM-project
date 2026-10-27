"""Image endpoint tests. A tiny synthetic-data model (test fixture only) exercises upload handling, validation,
privacy (nothing stored but a fingerprint) and the response contract. They do NOT measure medical accuracy."""
import io
import sys

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("torch")
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.api.deps import limiter  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.database import get_db  # noqa: E402
from app.models import AuditEvent, ScreeningRecord  # noqa: E402
from conftest import register_and_login  # noqa: E402


def png(w=64, h=64, fmt="PNG"):
    arr = np.random.RandomState(1).randint(0, 255, (h, w, 3)).astype("uint8")
    buf = io.BytesIO(); Image.fromarray(arr).save(buf, format=fmt); return buf.getvalue()


@pytest.fixture(scope="module")
def toy_model(tmp_path_factory):
    root = tmp_path_factory.mktemp("imgmodel")
    rng = np.random.RandomState(0)
    for cls in ("abnormal", "normal"):
        (root / "data" / cls).mkdir(parents=True)
        for i in range(24):
            arr = rng.randint(0, 80, (64, 64, 3)).astype("uint8")
            if cls == "abnormal": arr[10:26, 10:26] = 230
            Image.fromarray(arr).save(root / "data" / cls / f"{i}.png")
    from imaging.train_image import main
    out = root / "m.pt"
    main(["--data", str(root / "data"), "--positive", "abnormal", "--epochs", "1", "--image-size", "64",
          "--weights", "none", "--batch-size", "16", "--out", str(out), "--metrics-out", str(root / "m.json"),
          "--dataset-desc", "synthetic toy data (test only)"])
    return out


@pytest.fixture()
def img_client(toy_model, session_factory, monkeypatch):
    monkeypatch.setattr(settings, "image_model_path", toy_model)
    from app.main import create_app
    app = create_app()                                     # route is mounted because a model is now installed
    def override():
        db = session_factory()
        try: yield db
        finally: db.close()
    app.dependency_overrides[get_db] = override
    limiter.reset()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def up(client, headers, data, name="scan.png", ctype="image/png"):
    return client.post("/api/v1/images/screening", files={"file": (name, data, ctype)}, headers=headers)


def test_route_absent_without_model(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "image_model_path", tmp_path / "missing.pt")
    from app.main import create_app
    spec = create_app().openapi()
    assert "/api/v1/images/screening" not in spec["paths"]


def test_image_listed_as_available_with_model(img_client):
    d = [x for x in img_client.get("/api/v1/diseases").json()["diseases"] if x["id"] == "image_screening"][0]
    assert d["status"] == "available" and d["max_bytes"] == 5 * 1024 * 1024


def test_requires_auth(img_client):
    assert up(img_client, {}, png()).status_code == 401


def test_success_returns_score_and_heatmap_but_stores_no_pixels(img_client, session_factory):
    h = register_and_login(img_client)
    r = up(img_client, h, png())
    assert r.status_code == 201, r.text
    b = r.json()
    assert 0 <= b["screening_score"] <= 1 and b["gradcam"]["overlay_png_base64"] and "not proof of disease" in b["gradcam"]["caveat"]
    db = session_factory()
    rec = db.get(ScreeningRecord, b["id"])
    assert set(rec.input_features) == {"type", "width", "height", "sha256"}           # fingerprint only
    assert "overlay" not in str(rec.explanation) and "scan.png" not in str(rec.input_features)
    assert "image_screening_created" in {e.event_type for e in db.scalars(select(AuditEvent))}
    assert img_client.get("/api/v1/screening/history", headers=h).json()["items"][0]["disease"] == "image_screening"


@pytest.mark.parametrize("data,name,ctype,code", [
    (b"not an image at all", "a.png", "image/png", 422),
    (b"", "a.png", "image/png", 422),
    (png(fmt="GIF"), "a.png", "image/png", 422),                 # content is GIF although named .png
    (png(16, 16), "tiny.png", "image/png", 422),
    (b"MZ\x90\x00 executable bytes", "evil.png", "image/png", 422),
    (b"x" * (5 * 1024 * 1024 + 10), "big.png", "image/png", 413),
])
def test_rejects_bad_uploads(img_client, data, name, ctype, code):
    h = register_and_login(img_client)
    r = up(img_client, h, data, name, ctype)
    assert r.status_code == code and set(r.json()) == {"error"}


def test_missing_file_field_is_422(img_client):
    h = register_and_login(img_client)
    assert img_client.post("/api/v1/images/screening", headers=h).status_code == 422


def test_filename_with_path_traversal_is_harmless(img_client):
    h = register_and_login(img_client)
    assert up(img_client, h, png(), name="../../etc/passwd.png").status_code == 201


def test_model_unavailable_503(img_client, monkeypatch):
    from app.services import image_service
    def gone(*a, **k): raise image_service.ImageModelUnavailableError("x")
    monkeypatch.setattr(image_service, "screen", gone)
    h = register_and_login(img_client)
    assert up(img_client, h, png()).status_code == 503
