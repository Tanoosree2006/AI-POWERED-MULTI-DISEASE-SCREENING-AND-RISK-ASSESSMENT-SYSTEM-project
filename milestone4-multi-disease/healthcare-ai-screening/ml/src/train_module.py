"""Generic leakage-safe trainer for tabular disease modules.   Usage: python src/train_module.py diabetes|heart_disease

Protocol (same as the breast-cancer module): stratified 60/20/20 split; median imputation and scaling live INSIDE the
pipeline (fitted on training data only); hyperparameters tuned by 5-fold CV on the training set; the model is selected
on the VALIDATION set; the test set is used once. Extras for small datasets: repeated cross-validation on train+val,
and a validation-chosen high-sensitivity operating point.
"""
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import make_scorer, recall_score, roc_curve
from sklearn.model_selection import (GridSearchCV, RepeatedStratifiedKFold, StratifiedKFold, cross_validate,
                                     train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import EVAL_DIR, FIG_DIR, SEED, THRESHOLD, ensure_dirs
from metrics import compute_metrics
from modules import REGISTRY


def split(X, y):
    X_tmp, X_te, y_tmp, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    X_tr, X_va, y_tr, y_va = train_test_split(X_tmp, y_tmp, test_size=0.25, stratify=y_tmp, random_state=SEED)
    return X_tr, X_va, X_te, y_tr, y_va, y_te


def candidates():
    imp = ("impute", SimpleImputer(strategy="median"))
    c = {
        "logistic_regression": (Pipeline([imp, ("scale", StandardScaler()),
                                          ("clf", LogisticRegression(max_iter=5000, random_state=SEED))]),
                                {"clf__C": [0.01, 0.1, 1, 10]}),
        "random_forest": (Pipeline([imp, ("clf", RandomForestClassifier(random_state=SEED))]),
                          {"clf__n_estimators": [200, 400], "clf__max_depth": [3, 5, None],
                           "clf__min_samples_leaf": [1, 3]}),
    }
    try:
        from xgboost import XGBClassifier
        c["xgboost"] = (Pipeline([imp, ("clf", XGBClassifier(eval_metric="logloss", random_state=SEED))]),
                        {"clf__n_estimators": [100, 300], "clf__max_depth": [2, 3], "clf__learning_rate": [0.03, 0.1]})
    except ImportError:
        print("xgboost not installed: comparing two baselines only")
    return c


def data_report(X, y, label):
    return {"rows": int(len(X)), "features": int(X.shape[1]),
            "missing_values_by_column": {k: int(v) for k, v in X.isna().sum().items() if v},
            "duplicate_rows": int(X.duplicated().sum()),
            "class_counts": {"negative": int((y == 0).sum()), label: int((y == 1).sum())},
            "positive_fraction": round(float(y.mean()), 4)}


def high_sensitivity_threshold(y_val, p_val, target=0.90):
    fpr, tpr, thr = roc_curve(y_val, p_val)
    ok = np.where(tpr >= target)[0]
    return float(thr[ok[0]]) if len(ok) else None  # first (highest) threshold reaching the sensitivity target


def run(slug: str):
    spec = REGISTRY[slug]
    if spec.features is None:
        raise SystemExit("breast_cancer is trained with src/train.py")
    ensure_dirs()
    X, y = spec.loader()
    report = data_report(X, y, spec.positive_label)
    print(slug, json.dumps(report))
    X_tr, X_va, X_te, y_tr, y_va, y_te = split(X, y)
    print(f"train={len(X_tr)} val={len(X_va)} test={len(X_te)}  (test positives={int(y_te.sum())})")

    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    fitted, val_res, best_params = {}, {}, {}
    for name, (pipe, grid) in candidates().items():
        gs = GridSearchCV(pipe, grid, scoring="roc_auc", cv=cv, n_jobs=1).fit(X_tr, y_tr)
        fitted[name], best_params[name] = gs.best_estimator_, gs.best_params_
        val_res[name] = compute_metrics(y_va, gs.best_estimator_.predict_proba(X_va)[:, 1], THRESHOLD)
        val_res[name].update(best_params=gs.best_params_, cv_roc_auc_train_folds=round(float(gs.best_score_), 4))
        print(f"[val] {name:20s} AUC={val_res[name]['roc_auc']:.4f} recall={val_res[name]['recall_sensitivity']:.4f}")

    best = max(val_res, key=lambda n: (round(val_res[n]["roc_auc"], 4), val_res[n]["recall_sensitivity"],
                                       -val_res[n]["brier_score"]))
    print("SELECTED (validation):", best)

    test_proba = {n: m.predict_proba(X_te)[:, 1] for n, m in fitted.items()}
    test_res = {n: compute_metrics(y_te, p, THRESHOLD) for n, p in test_proba.items()}

    # Repeated CV on train+val only (test untouched): a steadier estimate than one small test split
    X_dev, y_dev = pd.concat([X_tr, X_va]), pd.concat([y_tr, y_va])
    rcv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
    scoring = {"roc_auc": "roc_auc", "recall": "recall",
               "specificity": make_scorer(recall_score, pos_label=0), "accuracy": "accuracy"}
    cv_est = {}
    for name, (pipe, _) in candidates().items():
        est = clone(pipe).set_params(**best_params[name])
        r = cross_validate(est, X_dev, y_dev, cv=rcv, scoring=scoring, n_jobs=1)
        cv_est[name] = {k: {"mean": round(float(r[f"test_{k}"].mean()), 4), "std": round(float(r[f"test_{k}"].std()), 4)}
                        for k in scoring}
        print(f"[repeated CV] {name:20s} AUC {cv_est[name]['roc_auc']['mean']:.3f}+/-{cv_est[name]['roc_auc']['std']:.3f}"
              f"  recall {cv_est[name]['recall']['mean']:.3f}")

    thr = high_sensitivity_threshold(y_va, fitted[best].predict_proba(X_va)[:, 1])
    hs = None
    if thr is not None:
        hs = {"threshold": round(thr, 4), "chosen_on": "validation set, first threshold with sensitivity >= 0.90",
              "test": compute_metrics(y_te, test_proba[best], thr)}

    bundle = {
        "pipeline": fitted[best], "model_name": best, "module": slug,
        "feature_names": list(X.columns), "threshold": THRESHOLD, "positive_class": spec.positive_label,
        "training_ranges": {f: [float(np.nanmin(X_tr[f])), float(np.nanmax(X_tr[f]))] for f in X.columns},
        "feature_rules": {f.name: {"min": f.min, "max": f.max, "nullable": f.nullable, "allowed": f.allowed}
                          for f in spec.features},
        "background": X_tr.sample(100, random_state=SEED, replace=len(X_tr) < 100).reset_index(drop=True),
        "dataset": spec.source, "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    joblib.dump(bundle, spec.bundle_path)

    out = {"module": slug, "data_report": report, "split": {"train": len(X_tr), "val": len(X_va), "test": len(X_te)},
           "test_positives": int(y_te.sum()), "selected_model": best, "threshold": THRESHOLD,
           "validation": val_res, "test": test_res, "repeated_cv_train_plus_val": cv_est,
           "high_sensitivity_operating_point": hs}
    spec.metrics_path.write_text(json.dumps(out, indent=2))

    # figures
    for tag in ("roc", "cm", "calib", "eda"):
        pass
    fig, ax = plt.subplots(figsize=(5, 4.5))
    for n, p in test_proba.items():
        fpr, tpr, _ = roc_curve(y_te, p)
        ax.plot(fpr, tpr, label=f"{n} (AUC={test_res[n]['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=0.8); ax.set_xlabel("1 - specificity"); ax.set_ylabel("sensitivity")
    ax.set_title(f"{slug}: ROC (test)"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG_DIR / f"{slug}_roc.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    cm = test_res[best]["confusion_matrix"]; mat = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
    fig, ax = plt.subplots(figsize=(4.4, 3.8)); ax.imshow(mat, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, mat[i, j], ha="center", va="center", fontsize=14)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["pred negative", "pred positive"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["true negative", "true positive"]); ax.set_title(f"{best}")
    fig.tight_layout(); fig.savefig(FIG_DIR / f"{slug}_confusion.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    frac, mean_pred = calibration_curve(y_te, test_proba[best], n_bins=5, strategy="quantile")
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.plot(mean_pred, frac, "o-", label=best); ax.plot([0, 1], [0, 1], "k--", lw=0.8)
    ax.set_xlabel("mean predicted score"); ax.set_ylabel("observed positive fraction"); ax.set_title(f"{slug}: calibration (test)")
    fig.tight_layout(); fig.savefig(FIG_DIR / f"{slug}_calibration.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # SHAP global importance on the actual saved model
    import shap
    from explain import shap_values
    vals, base, unit = shap_values(bundle, X_te.reset_index(drop=True))
    imp = pd.Series(np.abs(vals).mean(axis=0), index=bundle["feature_names"]).sort_values(ascending=False)
    (EVAL_DIR / f"{slug}_shap_global.json").write_text(json.dumps(
        {"model": best, "unit": unit, "n_test_samples": len(X_te), "mean_abs_shap": imp.round(5).to_dict()}, indent=2))
    plt.figure(); shap.summary_plot(vals, X_te.reset_index(drop=True), plot_type="bar", show=False)
    plt.xlabel(f"mean |SHAP value| ({unit})"); plt.title(f"{slug}: global importance (test)")
    plt.savefig(FIG_DIR / f"{slug}_shap_bar.png", dpi=150, bbox_inches="tight"); plt.close()

    cols = ["accuracy", "precision", "recall_sensitivity", "specificity", "f1", "roc_auc", "brier_score", "ece_10bin"]
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    tbl = pd.DataFrame({n: {c: r[c] for c in cols} for n, r in test_res.items()}).T.round(4)
    tbl["TN/FP/FN/TP"] = [f"{c['confusion_matrix']['tn']}/{c['confusion_matrix']['fp']}/{c['confusion_matrix']['fn']}/{c['confusion_matrix']['tp']}" for c in test_res.values()]
    print("\nTEST RESULTS (threshold 0.5):"); print(tbl)
    if hs:
        t = hs["test"]
        print(f"\nHigh-sensitivity operating point (threshold {hs['threshold']}): test recall={t['recall_sensitivity']:.3f} "
              f"specificity={t['specificity']:.3f}  TN/FP/FN/TP={t['confusion_matrix']}")
    print("SHAP top-5:", list(imp.head(5).index))
    print("saved", spec.bundle_path.name)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in REGISTRY:
        sys.exit(f"usage: python src/train_module.py {{{'|'.join(k for k, v in REGISTRY.items() if v.features)}}}")
    run(sys.argv[1])
