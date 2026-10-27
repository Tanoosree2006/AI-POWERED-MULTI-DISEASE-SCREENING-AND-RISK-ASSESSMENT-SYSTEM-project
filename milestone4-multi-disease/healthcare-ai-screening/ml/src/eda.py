"""Exploratory data analysis: writes evaluation/eda_report.json and figures."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import EVAL_DIR, FIG_DIR, ensure_dirs
from data import load_data


def main():
    ensure_dirs()
    X, y = load_data()
    df = X.assign(malignant=y)

    corr = X.corr()
    upper = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1))
    high_pairs = [(a, b, round(float(upper.loc[a, b]), 3))
                  for a in upper.index for b in upper.columns
                  if pd.notna(upper.loc[a, b]) and abs(upper.loc[a, b]) >= 0.9]
    target_corr = X.corrwith(y).sort_values(key=abs, ascending=False)

    report = {
        "shape": list(X.shape),
        "missing_values_total": int(X.isna().sum().sum()),
        "duplicate_rows": int(X.duplicated().sum()),
        "class_counts": {"benign": int((y == 0).sum()), "malignant": int((y == 1).sum())},
        "malignant_fraction": round(float(y.mean()), 4),
        "feature_min": X.min().round(5).to_dict(),
        "feature_max": X.max().round(5).to_dict(),
        "n_feature_pairs_abs_corr_ge_0.9": len(high_pairs),
        "example_highly_correlated_pairs": high_pairs[:8],
        "top10_abs_corr_with_target": target_corr.head(10).round(3).to_dict(),
        "notes": [
            "No missing values or duplicates were found.",
            "Strong multicollinearity (radius/perimeter/area and mean/worst variants): "
            "coefficients and SHAP credit can be split arbitrarily among correlated features.",
            "Features are computed from one digitised fine-needle-aspirate image per sample; "
            "patient identifiers are not provided, so patient-level leakage cannot be ruled out.",
        ],
    }
    (EVAL_DIR / "eda_report.json").write_text(json.dumps(report, indent=2))

    # 1. class balance
    fig, ax = plt.subplots(figsize=(4, 3.5))
    counts = y.map({0: "benign", 1: "malignant"}).value_counts()
    ax.bar(counts.index, counts.values, color=["#4c78a8", "#e45756"])
    for i, v in enumerate(counts.values):
        ax.text(i, v + 5, str(v), ha="center")
    ax.set_title("Class balance"); ax.set_ylabel("samples")
    fig.tight_layout(); fig.savefig(FIG_DIR / "eda_class_balance.png", dpi=150); plt.close(fig)

    # 2. distributions of the 6 features most correlated with the target
    top6 = list(target_corr.index[:6])
    fig, axes = plt.subplots(2, 3, figsize=(11, 6))
    for ax, f in zip(axes.ravel(), top6):
        ax.hist(df.loc[df.malignant == 0, f], bins=25, alpha=0.6, label="benign", color="#4c78a8")
        ax.hist(df.loc[df.malignant == 1, f], bins=25, alpha=0.6, label="malignant", color="#e45756")
        ax.set_title(f, fontsize=9)
    axes[0, 0].legend()
    fig.suptitle("Top-6 target-correlated features by class"); fig.tight_layout()
    fig.savefig(FIG_DIR / "eda_feature_distributions.png", dpi=150); plt.close(fig)

    # 3. correlation heatmap
    fig, ax = plt.subplots(figsize=(10, 8.5))
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr))); ax.set_yticks(range(len(corr)))
    ax.set_xticklabels(corr.columns, rotation=90, fontsize=6)
    ax.set_yticklabels(corr.columns, fontsize=6)
    fig.colorbar(im, ax=ax, fraction=0.04); ax.set_title("Feature correlation matrix")
    fig.tight_layout(); fig.savefig(FIG_DIR / "eda_correlation_heatmap.png", dpi=150); plt.close(fig)

    # 4. target correlation bar
    fig, ax = plt.subplots(figsize=(7, 4.5))
    t = target_corr.head(10)[::-1]
    ax.barh(t.index, t.values, color="#e45756"); ax.set_title("Top-10 |correlation| with malignant")
    fig.tight_layout(); fig.savefig(FIG_DIR / "eda_target_correlation.png", dpi=150); plt.close(fig)

    print(json.dumps({k: report[k] for k in list(report)[:7]}, indent=2))
    print("Highly correlated pairs (|r|>=0.9):", len(high_pairs))
    print("Top-5 target correlations:", target_corr.head(5).round(3).to_dict())
    print(f"Saved report + 4 figures to {EVAL_DIR}")


if __name__ == "__main__":
    main()
