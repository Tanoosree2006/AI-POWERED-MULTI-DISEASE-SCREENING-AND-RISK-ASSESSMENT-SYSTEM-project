"""Train Logistic Regression, Random Forest and XGBoost; select on VALIDATION;
evaluate once on TEST; save the fitted pipeline bundle.

Leakage control: every scaler lives INSIDE a sklearn Pipeline, so it is fitted
only on training folds. The test set is never used for tuning or selection.
"""
import json
from datetime import datetime, timezone

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import EVAL_DIR, FIG_DIR, MODEL_PATH, SEED, THRESHOLD, ensure_dirs
from data import load_data, split_data
from metrics import compute_metrics


def candidates():
    c = {
        "logistic_regression": (
            Pipeline([("scale", StandardScaler()),
                      ("clf", LogisticRegression(max_iter=5000, random_state=SEED))]),
            {"clf__C": [0.01, 0.1, 1, 10]}),
        "random_forest": (
            Pipeline([("clf", RandomForestClassifier(random_state=SEED))]),
            {"clf__n_estimators": [200, 400], "clf__max_depth": [None, 5, 10]}),
    }
    try:
        from xgboost import XGBClassifier
        c["xgboost"] = (
            Pipeline([("clf", XGBClassifier(eval_metric="logloss", random_state=SEED))]),
            {"clf__n_estimators": [100, 300], "clf__max_depth": [2, 4],
             "clf__learning_rate": [0.05, 0.1]})
    except ImportError:
        print("xgboost not installed - comparing the two required baselines only")
    return c


def main():
    ensure_dirs()
    X, y = load_data()
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
    print(f"train={len(X_train)} val={len(X_val)} test={len(X_test)}")

    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    fitted, val_res, cv_auc = {}, {}, {}
    for name, (pipe, grid) in candidates().items():
        gs = GridSearchCV(pipe, grid, scoring="roc_auc", cv=cv, n_jobs=-1).fit(X_train, y_train)
        fitted[name] = gs.best_estimator_
        cv_auc[name] = round(float(gs.best_score_), 4)
        val_res[name] = compute_metrics(y_val, gs.best_estimator_.predict_proba(X_val)[:, 1], THRESHOLD)
        val_res[name]["best_params"] = gs.best_params_
        val_res[name]["cv_roc_auc_train_folds"] = cv_auc[name]
        print(f"[val] {name:20s} AUC={val_res[name]['roc_auc']:.4f} "
              f"recall={val_res[name]['recall_sensitivity']:.4f} params={gs.best_params_}")

    # Selection uses VALIDATION only: AUC (4 d.p.), ties broken by recall, then Brier
    best = max(val_res, key=lambda n: (round(val_res[n]["roc_auc"], 4),
                                       val_res[n]["recall_sensitivity"], -val_res[n]["brier_score"]))
    print("SELECTED (by validation):", best)

    # Single look at the test set
    test_proba = {n: m.predict_proba(X_test)[:, 1] for n, m in fitted.items()}
    test_res = {n: compute_metrics(y_test, p, THRESHOLD) for n, p in test_proba.items()}

    bundle = {
        "pipeline": fitted[best], "model_name": best,
        "feature_names": list(X.columns), "threshold": THRESHOLD,
        "positive_class": "malignant",
        "training_ranges": {f: [float(X_train[f].min()), float(X_train[f].max())] for f in X.columns},
        "background": X_train.sample(100, random_state=SEED).reset_index(drop=True),
        "dataset": "UCI WDBC (id 17, CC BY 4.0) via scikit-learn",
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    joblib.dump(bundle, MODEL_PATH)

    out = {"split": {"train": len(X_train), "val": len(X_val), "test": len(X_test)},
           "selected_model": best, "threshold": THRESHOLD,
           "validation": val_res, "test": test_res}
    (EVAL_DIR / "breast_cancer_metrics.json").write_text(json.dumps(out, indent=2))

    # ---- markdown results table
    cols = ["accuracy", "precision", "recall_sensitivity", "specificity", "f1", "roc_auc",
            "brier_score", "ece_10bin"]
    tbl = pd.DataFrame({n: {c: r[c] for c in cols} for n, r in test_res.items()}).T.round(4)
    cms = {n: r["confusion_matrix"] for n, r in test_res.items()}
    tbl["TN/FP/FN/TP"] = [f"{c['tn']}/{c['fp']}/{c['fn']}/{c['tp']}" for c in cms.values()]
    (EVAL_DIR / "results_table.md").write_text(tbl.to_markdown() if _has_tabulate() else tbl.to_string())
    pd.set_option("display.width", 200); pd.set_option("display.max_columns", 20)
    print("\nTEST RESULTS (threshold 0.5):"); print(tbl)

    # ---- figures: ROC, confusion matrix of selected model, calibration of selected model
    fig, ax = plt.subplots(figsize=(5, 4.5))
    for n, p in test_proba.items():
        fpr, tpr, _ = roc_curve(y_test, p)
        ax.plot(fpr, tpr, label=f"{n} (AUC={test_res[n]['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=0.8); ax.set_xlabel("1 - specificity"); ax.set_ylabel("sensitivity")
    ax.set_title("ROC curves (test set)"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG_DIR / "roc_curves.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    cm = test_res[best]["confusion_matrix"]
    mat = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
    fig, ax = plt.subplots(figsize=(4, 3.6)); ax.imshow(mat, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, mat[i, j], ha="center", va="center", fontsize=14)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["pred benign", "pred malignant"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["true benign", "true malignant"])
    ax.set_title(f"Confusion matrix: {best}"); fig.tight_layout()
    fig.savefig(FIG_DIR / "confusion_matrix.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    frac, mean_pred = calibration_curve(y_test, test_proba[best], n_bins=5, strategy="quantile")
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.plot(mean_pred, frac, "o-", label=best); ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="perfect")
    ax.set_xlabel("mean predicted score"); ax.set_ylabel("observed malignant fraction")
    ax.set_title("Calibration (test, 5 quantile bins)"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG_DIR / "calibration_curve.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"Saved model -> {MODEL_PATH}")


def _has_tabulate():
    try:
        import tabulate  # noqa: F401
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    main()
