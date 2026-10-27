"""Bridge between the API and the trained ML pipeline (ml/src)."""
import json
import sys

from app.core.config import settings


class ModelUnavailableError(RuntimeError):
    pass


class ScreeningInputError(ValueError):
    pass


SUPPORTED_DISEASES = {
    "breast_cancer": {
        "name": "Breast cancer screening (Wisconsin Diagnostic dataset)",
        "data_type": "tabular",
        "metrics_file": "breast_cancer_metrics.json",
    }
}


def _ensure_ml_path():
    p = str(settings.ml_src_dir)
    if p not in sys.path:
        sys.path.insert(0, p)


def is_supported(disease: str) -> bool:
    return disease in SUPPORTED_DISEASES


def _bundle():
    _ensure_ml_path()
    import explain
    try:
        return explain.load_bundle()
    except FileNotFoundError as e:
        raise ModelUnavailableError(str(e)) from e


def model_status(disease: str) -> str:
    try:
        _bundle()
        return "available"
    except ModelUnavailableError:
        return "unavailable"


def disease_info(disease: str) -> dict:
    b = _bundle()
    meta = SUPPORTED_DISEASES[disease]
    return {"id": disease, "name": meta["name"], "data_type": meta["data_type"],
            "status": "available", "model": b["model_name"], "model_version": b["trained_at"],
            "threshold": b["threshold"], "dataset": b["dataset"],
            "n_features": len(b["feature_names"]), "feature_names": b["feature_names"]}


def run_screening(disease: str, features: dict) -> dict:
    _ensure_ml_path()
    import predict
    try:
        return predict.predict(features, explain=True, top_k=5)
    except predict.InputValidationError as e:
        raise ScreeningInputError(str(e)) from e
    except FileNotFoundError as e:
        raise ModelUnavailableError(str(e)) from e


def load_metrics(disease: str) -> dict | None:
    path = settings.ml_eval_dir / SUPPORTED_DISEASES[disease]["metrics_file"]
    return json.loads(path.read_text()) if path.exists() else None


def example_record() -> dict:
    _ensure_ml_path()
    from data import load_data
    X, y = load_data()
    return {k: round(float(v), 5) for k, v in X[y == 1].iloc[0].items()}
