import numpy as np
import pandas as pd
from data import load_data, split_data
from explain import explain_one, load_bundle, shap_values
from predict import predict


def _row():
    X, y = load_data()
    *_, Xte, _, _, _ = split_data(X, y)
    return Xte.iloc[[0]]


def test_shap_shape_and_additivity_matches_model():
    """base + sum(SHAP) must reconstruct the model output (LR/XGB: log-odds, RF: probability)."""
    b = load_bundle(); row = _row()
    vals, base, unit = shap_values(b, row)
    assert vals.shape == (1, 30)
    p = b["pipeline"].predict_proba(row[b["feature_names"]])[0, 1]
    recon = base + vals.sum()
    target = np.log(p / (1 - p)) if unit == "log-odds" else p
    assert abs(recon - target) < 1e-3


def test_explain_one_sorted_and_top_k():
    e = explain_one(load_bundle(), _row(), top_k=4)
    mags = [abs(t["shap"]) for t in e["top_features"]]
    assert len(mags) == 4 and mags == sorted(mags, reverse=True)
    assert {t["effect"] for t in e["top_features"]} <= {"raises score", "lowers score"}


def test_predict_with_explanation():
    X, _ = load_data()
    out = predict(X.iloc[0].to_dict(), explain=True, top_k=3)
    assert len(out["explanation"]["top_features"]) == 3
    assert "caveat" in out["explanation"]
