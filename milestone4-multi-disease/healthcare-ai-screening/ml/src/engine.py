"""Generic validated inference for any tabular module bundle (rules, missing values, explanation)."""
import math
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from config import DISCLAIMER
from explain import explain_one


class InputValidationError(ValueError):
    """Raised when a patient record is malformed."""


@lru_cache(maxsize=8)
def load_bundle(path: str):
    if not Path(path).exists():
        raise FileNotFoundError(f"Model not found: {path}. Train it first (see README).")
    return joblib.load(path)


def feature_rules(bundle) -> dict:
    """Per-feature rules; bundles without explicit rules (breast cancer) default to: required, non-negative."""
    stored = bundle.get("feature_rules") or {}
    default = {"min": 0.0, "max": None, "nullable": False, "allowed": None}
    return {f: {**default, **stored.get(f, {})} for f in bundle["feature_names"]}


def validate_record(record, bundle) -> dict:
    if not isinstance(record, dict):
        raise InputValidationError("Input must be a JSON object of feature: value pairs")
    feats, rules = bundle["feature_names"], feature_rules(bundle)
    missing = [f for f in feats if f not in record]
    if missing:
        raise InputValidationError(f"Missing features: {missing}")
    unknown = [k for k in record if k not in feats]
    if unknown:
        raise InputValidationError(f"Unknown features: {unknown}")
    clean = {}
    for f in feats:
        v, r = record[f], rules[f]
        if v is None:
            if not r["nullable"]:
                raise InputValidationError(f"Feature '{f}' is required")
            clean[f] = float("nan")
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise InputValidationError(f"Feature '{f}' must be a number, got {type(v).__name__}")
        if not math.isfinite(v):
            raise InputValidationError(f"Feature '{f}' must be finite")
        if r["min"] is not None and v < r["min"]:
            raise InputValidationError(f"Feature '{f}' must be at least {r['min']:g}")
        if r["max"] is not None and v > r["max"]:
            raise InputValidationError(f"Feature '{f}' must be at most {r['max']:g}")
        if r["allowed"] is not None and v not in r["allowed"]:
            raise InputValidationError(f"Feature '{f}' must be one of {r['allowed']}")
        clean[f] = float(v)
    return clean


def predict_with_bundle(bundle, record: dict, explain: bool = False, top_k: int = 5) -> dict:
    clean = validate_record(record, bundle)
    warnings = []
    for f, v in clean.items():
        if math.isnan(v):
            continue
        lo, hi = bundle["training_ranges"][f]
        if v < lo or v > hi:
            warnings.append(f"'{f}'={v:g} outside training range [{lo:g}, {hi:g}]; prediction may be unreliable")
    blanks = [f for f, v in clean.items() if math.isnan(v)]
    if blanks:
        warnings.append(f"{len(blanks)} value(s) left blank ({', '.join(blanks)}); the model filled them with "
                        "the training-data median, which lowers reliability")
    row = pd.DataFrame([clean])[bundle["feature_names"]]
    score = float(bundle["pipeline"].predict_proba(row)[0, 1])
    out = {"model": bundle["model_name"], "positive_class": bundle["positive_class"],
           "screening_score": round(score, 4), "threshold": bundle["threshold"],
           "screening_flag": "elevated" if score >= bundle["threshold"] else "lower",
           "warnings": warnings, "disclaimer": DISCLAIMER}
    if explain:
        out["explanation"] = explain_one(bundle, row, top_k=top_k)
    return out
