import pytest
from conftest import register_and_login
from app.core.config import settings


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["models"]["breast_cancer"] == "available"


def test_diseases_lists_only_working_modules(client):
    r = client.get("/api/v1/diseases")
    ds = {d["id"]: d for d in r.json()["diseases"]}
    tabular = {"breast_cancer", "diabetes", "heart_disease"}
    assert tabular <= set(ds) and all(ds[d]["status"] == "available" for d in tabular)
    assert ds["breast_cancer"]["n_features"] == 30 and ds["diabetes"]["n_features"] == 8 and ds["heart_disease"]["n_features"] == 13
    assert all("label" in f and "kind" in f for f in ds["diabetes"]["features"])
    # the image module is never advertised as working unless a model is installed
    assert ds["image_screening"]["status"] in {"available", "unavailable"}


def test_register_login_me(client):
    h = register_and_login(client)
    me = client.get("/api/v1/auth/me", headers=h)
    assert me.status_code == 200 and me.json()["username"] == "alice" and me.json()["role"] == "user"
    assert "password" not in me.text


def test_register_validation_and_duplicates(client):
    ok = {"username": "bob", "password": "longenough1"}
    assert client.post("/api/v1/auth/register", json=ok).status_code == 201
    assert client.post("/api/v1/auth/register", json={**ok, "username": "BOB"}).status_code == 409
    assert client.post("/api/v1/auth/register", json={"username": "x", "password": "longenough1"}).status_code == 422
    assert client.post("/api/v1/auth/register", json={"username": "carol", "password": "short"}).status_code == 422
    assert client.post("/api/v1/auth/register", json={"username": "bad name!", "password": "longenough1"}).status_code == 422


def test_register_cannot_choose_role(client):
    r = client.post("/api/v1/auth/register", json={"username": "eve", "password": "longenough1", "role": "admin"})
    assert r.status_code == 201 and r.json()["role"] == "user"


def test_login_failures_are_generic(client):
    client.post("/api/v1/auth/register", json={"username": "dave", "password": "longenough1"})
    a = client.post("/api/v1/auth/login", json={"username": "dave", "password": "wrong-password"})
    b = client.post("/api/v1/auth/login", json={"username": "nobody", "password": "wrong-password"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


def test_screening_requires_auth_and_valid_token(client, profiles):
    body = {"features": profiles["malignant"]}
    assert client.post("/api/v1/screening/breast_cancer", json=body).status_code == 401
    bad = {"Authorization": "Bearer not.a.token"}
    assert client.post("/api/v1/screening/breast_cancer", json=body, headers=bad).status_code == 401


def test_tampered_token_rejected(client, auth):
    tok = auth["Authorization"].split()[1]
    forged = tok[:-3] + ("aaa" if not tok.endswith("aaa") else "bbb")
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_screening_success_is_saved(client, auth, profiles):
    r = client.post("/api/v1/screening/breast_cancer", json={"features": profiles["malignant"]}, headers=auth)
    assert r.status_code == 201
    b = r.json()
    assert b["screening_flag"] == "elevated" and 0 <= b["screening_score"] <= 1
    assert len(b["explanation"]["top_features"]) == 5 and "NOT a diagnosis" in b["disclaimer"]
    h = client.get("/api/v1/screening/history", headers=auth).json()
    assert h["total"] == 1 and h["items"][0]["id"] == b["id"]
    assert client.get(f"/api/v1/screening/record/{b['id']}", headers=auth).json()["screening_score"] == b["screening_score"]


def test_benign_profile_flagged_lower(client, auth, profiles):
    r = client.post("/api/v1/screening/breast_cancer", json={"features": profiles["benign"]}, headers=auth)
    assert r.json()["screening_flag"] == "lower"


def test_invalid_inputs_use_error_envelope(client, auth, profiles):
    url = "/api/v1/screening/breast_cancer"
    good = dict(profiles["malignant"])
    missing = {k: v for k, v in good.items() if k != "mean radius"}
    for payload, code in [({"features": missing}, 422), ({"features": {**good, "mean radius": -1}}, 422),
                          ({"features": {**good, "mean radius": "12.5"}}, 422),
                          ({"features": {**good, "mean radius": True}}, 422),
                          ({"features": {**good, "age": 50}}, 422), ({"features": {}}, 422), ({}, 422)]:
        r = client.post(url, json=payload, headers=auth)
        assert r.status_code == code and set(r.json()) == {"error"} and r.json()["error"]["code"] == code
    assert client.post(url, content="not json", headers={**auth, "Content-Type": "application/json"}).status_code == 422


def test_validation_errors_do_not_echo_values(client, auth, profiles):
    r = client.post("/api/v1/screening/breast_cancer",
                    json={"features": {**profiles["malignant"], "mean radius": "SECRET-123"}}, headers=auth)
    assert "SECRET-123" not in r.text


def test_unknown_disease_404(client, auth, profiles):
    r = client.post("/api/v1/screening/lupus", json={"features": profiles["malignant"]}, headers=auth)
    assert r.status_code == 404


def test_history_is_private_but_admin_can_see_all(client, db, profiles):
    from app.core.security import hash_password
    from app.services import crud
    a, b = register_and_login(client, "alice"), register_and_login(client, "bobby", "another-pass-1")
    rid = client.post("/api/v1/screening/breast_cancer", json={"features": profiles["malignant"]}, headers=a).json()["id"]
    assert client.get("/api/v1/screening/history", headers=b).json()["total"] == 0
    assert client.get(f"/api/v1/screening/record/{rid}", headers=b).status_code == 404
    assert client.delete(f"/api/v1/screening/record/{rid}", headers=b).status_code == 404
    assert client.get("/api/v1/screening/history?scope=all", headers=b).status_code == 403
    crud.create_user(db, "root", hash_password("admin-pass-123"), role="admin")
    t = client.post("/api/v1/auth/login", json={"username": "root", "password": "admin-pass-123"}).json()["access_token"]
    adm = {"Authorization": f"Bearer {t}"}
    assert client.get("/api/v1/screening/history?scope=all", headers=adm).json()["total"] == 1
    assert client.get(f"/api/v1/screening/record/{rid}", headers=adm).status_code == 200


def test_delete_own_record(client, auth, profiles):
    rid = client.post("/api/v1/screening/breast_cancer", json={"features": profiles["malignant"]}, headers=auth).json()["id"]
    assert client.delete(f"/api/v1/screening/record/{rid}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/screening/record/{rid}", headers=auth).status_code == 404
    assert client.get("/api/v1/screening/history", headers=auth).json()["total"] == 0


def test_history_pagination_and_limits(client, auth, profiles):
    for _ in range(3):
        client.post("/api/v1/screening/breast_cancer", json={"features": profiles["benign"]}, headers=auth)
    p = client.get("/api/v1/screening/history?limit=2&offset=0", headers=auth).json()
    assert p["total"] == 3 and len(p["items"]) == 2
    assert client.get("/api/v1/screening/history?limit=2&offset=2", headers=auth).json()["items"].__len__() == 1
    assert client.get("/api/v1/screening/history?limit=0", headers=auth).status_code == 422
    assert client.get("/api/v1/screening/history?limit=101", headers=auth).status_code == 422


def test_dashboard_summary_reflects_real_records(client, auth, profiles):
    empty = client.get("/api/v1/dashboard/summary", headers=auth).json()
    assert empty["total_screenings"] == 0 and empty["mean_score"] is None and empty["trend"] == []
    client.post("/api/v1/screening/breast_cancer", json={"features": profiles["malignant"]}, headers=auth)
    client.post("/api/v1/screening/breast_cancer", json={"features": profiles["benign"]}, headers=auth)
    s = client.get("/api/v1/dashboard/summary", headers=auth).json()
    assert s["total_screenings"] == 2 and s["flagged_elevated"] == 1 and s["flagged_lower"] == 1
    assert s["by_disease"] == {"breast_cancer": 2} and s["trend"][0]["count"] == 2 and len(s["recent"]) == 2
    assert client.get("/api/v1/dashboard/summary?scope=all", headers=auth).status_code == 403


def test_metrics_endpoint_matches_evaluation_file(client):
    import json
    r = client.get("/api/v1/models/metrics").json()["metrics"]["breast_cancer"]
    disk = json.loads((settings.ml_eval_dir / "breast_cancer_metrics.json").read_text())
    assert r["selected_model"] == disk["selected_model"] and r["test"] == disk["test"]


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 3)
    codes = [client.post("/api/v1/auth/login", json={"username": "x", "password": "y"}).status_code for _ in range(5)]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]


def test_internal_errors_hide_details(client, auth, profiles, monkeypatch):
    from app.services import ml_service
    def boom(*a, **k): raise RuntimeError("secret internal detail /etc/passwd")
    monkeypatch.setattr(ml_service, "run_screening", boom)
    r = client.post("/api/v1/screening/breast_cancer", json={"features": profiles["malignant"]}, headers=auth)
    assert r.status_code == 500 and r.json() == {"error": {"code": 500, "message": "Internal server error"}}
    assert "secret" not in r.text and "Traceback" not in r.text


def test_model_unavailable_returns_503(client, auth, profiles, monkeypatch):
    from app.services import ml_service
    def gone(*a, **k): raise ml_service.ModelUnavailableError("missing")
    monkeypatch.setattr(ml_service, "run_screening", gone)
    r = client.post("/api/v1/screening/breast_cancer", json={"features": profiles["malignant"]}, headers=auth)
    assert r.status_code == 503


def test_cors_restricted(client):
    ok = client.options("/api/v1/diseases", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    bad = client.options("/api/v1/diseases", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in bad.headers


def test_openapi_documents_endpoints(client):
    spec = client.get("/openapi.json").json()
    assert "/api/v1/screening/{disease}" in spec["paths"]
    image_ok = client.get("/api/v1/diseases").json()["diseases"][-1]["status"] == "available"
    assert ("/api/v1/images/screening" in spec["paths"]) == image_ok
