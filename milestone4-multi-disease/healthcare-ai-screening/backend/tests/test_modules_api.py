"""API tests for the diabetes and heart-disease modules (real trained models, real held-out dataset rows)."""
import json

import pytest
from app.core.config import settings


@pytest.fixture()
def examples(client):
    return {d: client.get(f"/api/v1/diseases/{d}/examples").json() for d in ("diabetes", "heart_disease", "breast_cancer")}


def test_examples_are_real_rows_for_every_module(examples):
    for d, ex in examples.items():
        assert set(ex) == {"dataset_positive_example", "dataset_negative_example"} and ex["dataset_positive_example"] != ex["dataset_negative_example"]


def test_examples_unknown_module_404(client):
    assert client.get("/api/v1/diseases/lupus/examples").status_code == 404


@pytest.mark.parametrize("disease", ["diabetes", "heart_disease", "breast_cancer"])
def test_each_module_scores_and_explains(client, auth, examples, disease):
    r = client.post(f"/api/v1/screening/{disease}", json={"features": examples[disease]["dataset_positive_example"]}, headers=auth)
    assert r.status_code == 201, r.text
    b = r.json()
    assert b["disease"] == disease and 0 <= b["screening_score"] <= 1 and len(b["explanation"]["top_features"]) == 5
    assert b["explanation"]["unit"] in {"log-odds", "probability"}


def test_blank_nullable_values_are_imputed_with_warning(client, auth, examples):
    f = dict(examples["diabetes"]["dataset_positive_example"], insulin=None, skin_thickness=None)
    r = client.post("/api/v1/screening/diabetes", json={"features": f}, headers=auth)
    assert r.status_code == 201 and any("left blank" in w for w in r.json()["warnings"])


def test_required_value_cannot_be_blank_or_out_of_range(client, auth, examples):
    base = examples["diabetes"]["dataset_positive_example"]
    for patch in ({"age": None}, {"age": 5}, {"glucose": 9999}, {"bmi": -3}, {"pregnancies": "2"}):
        r = client.post("/api/v1/screening/diabetes", json={"features": {**base, **patch}}, headers=auth)
        assert r.status_code == 422, patch


def test_heart_categorical_codes_validated(client, auth, examples):
    base = examples["heart_disease"]["dataset_positive_example"]
    assert client.post("/api/v1/screening/heart_disease", json={"features": {**base, "cp": 7}}, headers=auth).status_code == 422
    assert client.post("/api/v1/screening/heart_disease", json={"features": {**base, "sex": 2}}, headers=auth).status_code == 422
    assert client.post("/api/v1/screening/heart_disease", json={"features": {**base, "thal": None, "ca": None}}, headers=auth).status_code == 201


def test_wrong_feature_set_for_module_rejected(client, auth, examples):
    r = client.post("/api/v1/screening/heart_disease", json={"features": examples["diabetes"]["dataset_positive_example"]}, headers=auth)
    assert r.status_code == 422


def test_metrics_endpoint_serves_all_modules(client):
    m = client.get("/api/v1/models/metrics").json()["metrics"]
    assert {"breast_cancer", "diabetes", "heart_disease"} <= set(m)
    for d in ("diabetes", "heart_disease"):
        assert m[d]["repeated_cv_train_plus_val"] and m[d]["high_sensitivity_operating_point"]
        disk = json.loads((settings.ml_eval_dir / f"{d}_metrics.json").read_text())
        assert m[d]["test"] == disk["test"]


def test_dashboard_counts_across_modules(client, auth, examples):
    for d in ("diabetes", "heart_disease"):
        client.post(f"/api/v1/screening/{d}", json={"features": examples[d]["dataset_negative_example"]}, headers=auth)
    s = client.get("/api/v1/dashboard/summary", headers=auth).json()
    assert s["by_disease"] == {"diabetes": 1, "heart_disease": 1}
