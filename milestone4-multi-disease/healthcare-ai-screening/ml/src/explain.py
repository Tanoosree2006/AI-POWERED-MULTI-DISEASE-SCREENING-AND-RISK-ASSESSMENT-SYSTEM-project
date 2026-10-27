"""SHAP explanations computed from the ACTUAL saved model (nothing hard-coded).

Units of SHAP values depend on the model: log-odds for Logistic Regression and
XGBoost, probability for Random Forest. Explanations describe how the MODEL
uses features, not biological causes.
"""
import json

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from config import EVAL_DIR, FIG_DIR, MODEL_PATH, ensure_dirs
from data import load_data, split_data


def load_bundle(path=MODEL_PATH):
    if not path.exists():
        raise FileNotFoundError("Model not found. Run: python src/train.py")
    return joblib.load(path)


def _parts(pipeline):
    pre = pipeline[:-1] if len(pipeline.steps) > 1 else None
    return pre, pipeline.steps[-1][1]


def _transform(pre, X):
    return pre.transform(X) if pre is not None else np.asarray(X, dtype=float)


def _explainer(bundle):
    pre, model = _parts(bundle["pipeline"])
    bg = _transform(pre, bundle["background"][bundle["feature_names"]])
    if isinstance(model, LogisticRegression):
        return shap.LinearExplainer(model, bg), "log-odds"
    if isinstance(model, RandomForestClassifier):
        return shap.TreeExplainer(model), "probability"
    return shap.TreeExplainer(model), "log-odds"


def _positive(vals):
    if isinstance(vals, list):
        return np.asarray(vals[1])
    vals = np.asarray(vals)
    return vals[:, :, 1] if vals.ndim == 3 else vals


def shap_values(bundle, X: pd.DataFrame):
    """Returns (values[n, f], base_value, unit) for the positive (malignant) class."""
    explainer, unit = _explainer(bundle)
    pre, _ = _parts(bundle["pipeline"])
    Xt = _transform(pre, X[bundle["feature_names"]])
    vals = _positive(explainer.shap_values(Xt))
    ev = np.atleast_1d(np.asarray(explainer.expected_value, dtype=float))
    base = float(ev[-1] if ev.size > 1 else ev[0])
    return vals, base, unit


def explain_one(bundle, row: pd.DataFrame, top_k: int = 5) -> dict:
    vals, base, unit = shap_values(bundle, row)
    v = vals[0]
    order = np.argsort(-np.abs(v))
    feats = bundle["feature_names"]
    contrib = [{"feature": feats[i], "value": float(row.iloc[0][feats[i]]),
                "shap": round(float(v[i]), 5),
                "effect": "raises score" if v[i] > 0 else "lowers score"} for i in order[:top_k]]
    return {"unit": unit, "base_value": round(base, 5),
            "sum_of_all_shap": round(float(v.sum()), 5), "top_features": contrib,
            "caveat": ("SHAP shows how the model used each input for this record. "
                       "Correlated features share credit; it is not evidence of biological causation.")}


def main():
    ensure_dirs()
    bundle = load_bundle()
    X, y = load_data()
    *_, X_test, _, _, y_test = split_data(X, y)  # unpack: X_train,X_val,X_test,y_train,y_val,y_test
    X_test = X_test.reset_index(drop=True); y_test = y_test.reset_index(drop=True)
    vals, base, unit = shap_values(bundle, X_test)

    imp = pd.Series(np.abs(vals).mean(axis=0), index=bundle["feature_names"]).sort_values(ascending=False)
    (EVAL_DIR / "shap_global_importance.json").write_text(json.dumps(
        {"model": bundle["model_name"], "unit": unit, "n_test_samples": len(X_test),
         "mean_abs_shap": imp.round(5).to_dict()}, indent=2))

    plt.figure(); shap.summary_plot(vals, X_test, plot_type="bar", show=False, max_display=15)
    plt.title("Global importance: mean |SHAP| (test set)"); plt.xlabel(f"mean |SHAP value| ({unit})"); plt.tight_layout()
    plt.savefig(FIG_DIR / "shap_global_bar.png", dpi=150, bbox_inches="tight"); plt.close()
    plt.figure(); shap.summary_plot(vals, X_test, show=False, max_display=15); plt.tight_layout()
    plt.savefig(FIG_DIR / "shap_beeswarm.png", dpi=150, bbox_inches="tight"); plt.close()

    # Local explanations for one malignant and one benign test sample
    for label, idx in (("malignant", int(np.where(y_test == 1)[0][0])), ("benign", int(np.where(y_test == 0)[0][0]))):
        e = explain_one(bundle, X_test.iloc[[idx]], top_k=8)
        names = [t["feature"] for t in e["top_features"]][::-1]
        sv = [t["shap"] for t in e["top_features"]][::-1]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.barh(names, sv, color=["#e45756" if s > 0 else "#4c78a8" for s in sv])
        ax.axvline(0, color="k", lw=0.8)
        score = float(bundle["pipeline"].predict_proba(X_test.iloc[[idx]])[0, 1])
        ax.set_title(f"Local SHAP ({label} test sample #{idx}, score={score:.3f}; {unit})", fontsize=9)
        fig.tight_layout(); fig.savefig(FIG_DIR / f"shap_local_{label}.png", dpi=150); plt.close(fig)
        print(f"\nLocal explanation, true {label} sample #{idx}, score={score:.4f}")
        for t in e["top_features"][:5]:
            print(f"  {t['feature']:25s} value={t['value']:<10.4g} shap={t['shap']:+.4f}  {t['effect']}")

    print("\nGlobal top-10 (mean |SHAP|, %s units):" % unit)
    print(imp.head(10).round(4).to_string())


if __name__ == "__main__":
    main()
