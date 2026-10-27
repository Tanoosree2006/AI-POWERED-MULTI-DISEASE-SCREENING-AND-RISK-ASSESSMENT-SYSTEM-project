import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

import datasets
import engine
from data import load_data, split_data
from explain import shap_values
from modules import REGISTRY


def test_pima_loader_treats_zeros_as_missing():
    X, y = datasets.load_pima()
    assert X.shape == (768, 8) and int(y.sum()) == 268
    assert X["insulin"].isna().sum() == 374 and X["glucose"].isna().sum() == 5
    assert (X.drop(columns=["pregnancies"]).fillna(1) > 0).all().all()  # no impossible zeros remain


def test_heart_loader_label_direction_and_cleaning():
    X, y = datasets.load_heart()
    assert X.shape == (302, 13) and int(y.sum()) == 138 and X.duplicated().sum() == 0
    # Positive class = disease: lower max heart rate, more exercise angina (verified from the data itself)
    assert X.loc[y == 1, "thalach"].mean() < X.loc[y == 0, "thalach"].mean()
    assert X.loc[y == 1, "exang"].mean() > X.loc[y == 0, "exang"].mean()
    assert X["ca"].max() == 3 and X["thal"].min() == 1


def test_label_direction_check_fails_on_flipped_labels():
    df = pd.read_csv(datasets.DATA_DIR / "heart_raw.csv", encoding="utf-8-sig")
    flipped = df.assign(target=1 - df.target)
    with pytest.raises(ValueError):
        datasets.check_heart_label_direction(flipped)


def test_checksum_mismatch_detected(tmp_path, monkeypatch):
    bad = tmp_path / "x.csv"; bad.write_text("tampered")
    monkeypatch.setattr(datasets, "DATA_DIR", tmp_path)
    with pytest.raises(ValueError, match="Checksum mismatch"):
        datasets._fetch("http://unused.invalid", "x.csv", "0" * 64)


@pytest.mark.parametrize("slug", ["diabetes", "heart_disease"])
def test_trained_bundles_have_rules_and_no_leakage(slug):
    spec = REGISTRY[slug]
    b = engine.load_bundle(str(spec.bundle_path))
    assert set(b["feature_rules"]) == set(b["feature_names"]) and b["positive_class"] == spec.positive_label
    X, y = spec.loader()
    from train_module import split
    Xtr, *_ = split(X, y)
    imp = b["pipeline"].named_steps["impute"]
    assert np.allclose(imp.statistics_, Xtr.median().values)   # medians learned from TRAIN rows only
    scaler = b["pipeline"].named_steps.get("scale")
    if scaler is not None:                                      # scaler fitted on imputed TRAIN data only
        assert np.allclose(scaler.mean_, Xtr.fillna(Xtr.median()).mean().values)


def test_engine_validation_rules():
    b = engine.load_bundle(str(REGISTRY["diabetes"].bundle_path))
    X, _ = REGISTRY["diabetes"].loader()
    ok = {k: (None if np.isnan(v) else float(v)) for k, v in X.iloc[0].items()}
    assert engine.predict_with_bundle(b, ok)["screening_flag"] in {"elevated", "lower"}
    for patch, msg in [({"age": None}, "required"), ({"age": 3}, "at least"), ({"glucose": 1e6}, "at most"),
                       ({"age": float("nan")}, "finite"), ({"age": "40"}, "number"), ({"age": True}, "number")]:
        with pytest.raises(engine.InputValidationError, match=msg):
            engine.predict_with_bundle(b, {**ok, **patch})
    with pytest.raises(engine.InputValidationError, match="Unknown"):
        engine.predict_with_bundle(b, {**ok, "extra": 1})


def test_blank_values_warn_and_still_predict():
    b = engine.load_bundle(str(REGISTRY["diabetes"].bundle_path))
    X, _ = REGISTRY["diabetes"].loader()
    rec = {k: float(v) for k, v in X.iloc[1].fillna(X.median()).items()}
    rec["insulin"] = None
    out = engine.predict_with_bundle(b, rec)
    assert any("left blank" in w for w in out["warnings"])


def test_shap_additivity_for_random_forest_and_xgboost():
    """Explanations must reconstruct the model output for tree models too (RF: probability, XGBoost: log-odds)."""
    from xgboost import XGBClassifier
    X, y = load_data()
    Xtr, _, Xte, ytr, _, yte = split_data(X, y)
    for est, unit in ((RandomForestClassifier(n_estimators=60, max_depth=5, random_state=0), "probability"),
                      (XGBClassifier(n_estimators=60, max_depth=3, eval_metric="logloss", random_state=0), "log-odds")):
        pipe = Pipeline([("impute", SimpleImputer()), ("clf", est)]).fit(Xtr, ytr)
        bundle = {"pipeline": pipe, "feature_names": list(X.columns), "background": Xtr.sample(60, random_state=0)}
        row = Xte.iloc[[0, 1, 2]]
        vals, base, u = shap_values(bundle, row)
        p = pipe.predict_proba(row)[:, 1]
        target = p if unit == "probability" else np.log(p / (1 - p))
        assert u == unit and np.allclose(base + vals.sum(axis=1), target, atol=1e-3)
