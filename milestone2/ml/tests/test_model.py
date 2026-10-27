import joblib
import numpy as np
from config import MODEL_PATH
from data import load_data, split_data
from metrics import compute_metrics, expected_calibration_error


def test_metrics_on_known_example():
    y = [1, 1, 0, 0]
    p = [0.9, 0.4, 0.2, 0.6]  # TP=1 FN=1 TN=1 FP=1 at 0.5
    m = compute_metrics(y, p)
    assert m["recall_sensitivity"] == 0.5 and m["specificity"] == 0.5
    assert m["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}


def test_ece_perfect_and_bad():
    assert expected_calibration_error([0, 1], [0.0, 1.0]) == 0.0
    assert expected_calibration_error([0, 0], [1.0, 1.0]) == 1.0


def test_bundle_contents_and_reload():
    b = joblib.load(MODEL_PATH)
    for k in ("pipeline", "feature_names", "model_name", "threshold", "training_ranges", "background"):
        assert k in b
    assert len(b["feature_names"]) == 30


def test_scaler_fitted_on_training_data_only():
    """Leakage check: scaler statistics must equal TRAIN means, not full-data means."""
    b = joblib.load(MODEL_PATH)
    pipe = b["pipeline"]
    if "scale" not in pipe.named_steps:
        return  # tree models have no scaler
    X, y = load_data()
    Xtr, *_ = split_data(X, y)
    assert np.allclose(pipe.named_steps["scale"].mean_, Xtr.mean().values)
    assert not np.allclose(pipe.named_steps["scale"].mean_, X.mean().values)


def test_probabilities_valid_and_sane_performance_on_test():
    b = joblib.load(MODEL_PATH)
    X, y = load_data()
    *_, Xte, _, _, yte = split_data(X, y)
    p = b["pipeline"].predict_proba(Xte[b["feature_names"]])[:, 1]
    assert ((p >= 0) & (p <= 1)).all()
    m = compute_metrics(yte, p, b["threshold"])
    # sanity floors (not claims of clinical performance)
    assert m["roc_auc"] > 0.95 and m["recall_sensitivity"] > 0.85
