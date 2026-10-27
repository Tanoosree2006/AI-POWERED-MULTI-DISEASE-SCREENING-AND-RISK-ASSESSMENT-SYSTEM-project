"""Bridge between the API and the trained ML pipelines (ml/src), for every tabular disease module."""
import json
import sys

from app.core.config import settings


class ModelUnavailableError(RuntimeError):
    pass


class ScreeningInputError(ValueError):
    pass


def _ensure_ml_path():
    p = str(settings.ml_src_dir)
    if p not in sys.path:
        sys.path.insert(0, p)


def _registry():
    _ensure_ml_path()
    import modules
    return modules.REGISTRY


# Public: slugs of tabular modules known to the platform (a module is "available" only once its model is trained).
def supported_diseases() -> list:
    return list(_registry())


def is_supported(disease: str) -> bool:
    return disease in _registry()


def _bundle(disease: str):
    _ensure_ml_path()
    import engine
    spec = _registry()[disease]
    try:
        return engine.load_bundle(str(spec.bundle_path))
    except FileNotFoundError as e:
        raise ModelUnavailableError(str(e)) from e


def model_status(disease: str) -> str:
    try:
        _bundle(disease)
        return "available"
    except ModelUnavailableError:
        return "unavailable"


def _features_meta(spec, bundle) -> list:
    if spec.features:
        return [{"name": f.name, "label": f.label, "kind": f.kind, "min": f.min, "max": f.max, "unit": f.unit,
                 "help": f.help, "allowed": f.allowed, "nullable": f.nullable} for f in spec.features]
    rng = bundle["training_ranges"]
    return [{"name": n, "label": n, "kind": "number", "min": 0, "max": None, "unit": "",
             "help": f"Typical range in training data: {rng[n][0]:g} to {rng[n][1]:g}", "allowed": None,
             "nullable": False} for n in bundle["feature_names"]]


def disease_info(disease: str) -> dict:
    spec, b = _registry()[disease], _bundle(disease)
    return {"id": disease, "name": spec.name, "description": spec.description, "data_type": "tabular",
            "status": "available", "model": b["model_name"], "model_version": b["trained_at"],
            "threshold": b["threshold"], "dataset": b["dataset"], "positive_class": b["positive_class"],
            "n_features": len(b["feature_names"]), "feature_names": b["feature_names"],
            "features": _features_meta(spec, b)}


def disease_stub(disease: str) -> dict:
    spec = _registry()[disease]
    return {"id": disease, "name": spec.name, "description": spec.description, "data_type": "tabular",
            "status": "unavailable"}


def run_screening(disease: str, features: dict) -> dict:
    _ensure_ml_path()
    import engine
    try:
        return engine.predict_with_bundle(_bundle(disease), features, explain=True, top_k=5)
    except engine.InputValidationError as e:
        raise ScreeningInputError(str(e)) from e


def load_metrics(disease: str) -> dict | None:
    path = _registry()[disease].metrics_path
    return json.loads(path.read_text()) if path.exists() else None


def example_records(disease: str) -> dict:
    """Two real held-out test rows from the public dataset (one per class) for demos. Not patient data."""
    _ensure_ml_path()
    import numpy as np
    spec = _registry()[disease]
    X, y = spec.loader()
    if disease == "breast_cancer":
        from data import split_data
        *_, X_te, _, _, y_te = split_data(X, y)
    else:
        from train_module import split
        _, _, X_te, _, _, y_te = split(X, y)
    def row(label):
        r = X_te[y_te == label].iloc[0]
        return {k: (None if np.isnan(v) else round(float(v), 5)) for k, v in r.items()}
    return {"dataset_positive_example": row(1), "dataset_negative_example": row(0)}


def example_record() -> dict:  # used for OpenAPI documentation
    return example_records("breast_cancer")["dataset_positive_example"]
