"""Evaluation metrics, including specificity and calibration error."""
import numpy as np
from sklearn.metrics import (accuracy_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)


def expected_calibration_error(y_true, proba, n_bins: int = 10) -> float:
    y_true, proba = np.asarray(y_true), np.asarray(proba)
    edges = np.linspace(0, 1, n_bins + 1)
    ids = np.clip(np.digitize(proba, edges[1:-1]), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        m = ids == b
        if m.any():
            ece += m.mean() * abs(y_true[m].mean() - proba[m].mean())
    return float(ece)


def compute_metrics(y_true, proba, threshold: float = 0.5) -> dict:
    y_true, proba = np.asarray(y_true), np.asarray(proba)
    pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall_sensitivity": float(recall_score(y_true, pred, zero_division=0)),
        "specificity": float(tn / (tn + fp)) if (tn + fp) else float("nan"),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "brier_score": float(brier_score_loss(y_true, proba)),
        "ece_10bin": expected_calibration_error(y_true, proba),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }
