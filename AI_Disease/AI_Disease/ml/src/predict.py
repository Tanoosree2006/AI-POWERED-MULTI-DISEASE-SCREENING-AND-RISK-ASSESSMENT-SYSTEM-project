"""Validated inference with the saved pipeline.

CLI (run from the ml/ folder):
  python src/predict.py --json examples/sample_malignant.json --explain
  python src/predict.py --sample benign
"""
import argparse
import json
import math
import sys

import pandas as pd

from config import DISCLAIMER, MODEL_PATH
from explain import explain_one, load_bundle as _load


class InputValidationError(ValueError):
    """Raised when a patient record is malformed."""


_BUNDLE = None


def get_bundle():
    global _BUNDLE
    if _BUNDLE is None:
        _BUNDLE = _load(MODEL_PATH)
    return _BUNDLE


def validate_record(record, bundle) -> dict:
    if not isinstance(record, dict):
        raise InputValidationError("Input must be a JSON object of feature: value pairs")
    feats = bundle["feature_names"]
    missing = [f for f in feats if f not in record]
    if missing:
        raise InputValidationError(f"Missing features: {missing}")
    unknown = [k for k in record if k not in feats]
    if unknown:
        raise InputValidationError(f"Unknown features: {unknown}")
    clean = {}
    for f in feats:
        v = record[f]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise InputValidationError(f"Feature '{f}' must be a number, got {type(v).__name__}")
        if not math.isfinite(v):
            raise InputValidationError(f"Feature '{f}' must be finite")
        if v < 0:
            raise InputValidationError(f"Feature '{f}' must be non-negative")
        clean[f] = float(v)
    return clean


def predict(record: dict, explain: bool = False, top_k: int = 5) -> dict:
    bundle = get_bundle()
    clean = validate_record(record, bundle)
    warnings = [f"'{f}'={v:g} outside training range [{lo:g}, {hi:g}]; prediction may be unreliable"
                for f, v in clean.items()
                for lo, hi in [bundle["training_ranges"][f]] if v < lo or v > hi]
    row = pd.DataFrame([clean])[bundle["feature_names"]]
    score = float(bundle["pipeline"].predict_proba(row)[0, 1])
    out = {"model": bundle["model_name"], "positive_class": bundle["positive_class"],
           "screening_score": round(score, 4), "threshold": bundle["threshold"],
           "screening_flag": "elevated" if score >= bundle["threshold"] else "lower",
           "warnings": warnings, "disclaimer": DISCLAIMER}
    if explain:
        out["explanation"] = explain_one(bundle, row, top_k=top_k)
    return out


def _sample(label: str) -> dict:
    from data import load_data, split_data
    X, y = load_data()
    *_, X_test, _, _, y_test = split_data(X, y)
    idx = y_test[y_test == (1 if label == "malignant" else 0)].index[0]
    return X.loc[idx].to_dict()


def main(argv=None):
    p = argparse.ArgumentParser(description="Breast cancer screening-score prediction")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--json", help="path to a JSON file with all 30 features")
    g.add_argument("--sample", choices=["malignant", "benign"], help="use a real held-out test record")
    p.add_argument("--explain", action="store_true"); p.add_argument("--top-k", type=int, default=5)
    a = p.parse_args(argv)
    try:
        if a.json:
            with open(a.json, encoding="utf-8-sig") as fh:
                record = json.load(fh)
        else:
            record = _sample(a.sample)
        print(json.dumps(predict(record, a.explain, a.top_k), indent=2))
        return 0
    except (InputValidationError, FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
