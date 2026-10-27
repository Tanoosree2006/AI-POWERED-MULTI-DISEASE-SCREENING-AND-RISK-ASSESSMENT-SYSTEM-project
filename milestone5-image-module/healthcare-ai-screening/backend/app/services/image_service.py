"""Image-screening service. Imports torch lazily so the API runs without it when no image model is installed."""
import json
import sys
from pathlib import Path

from app.core.config import settings


class ImageModelUnavailableError(RuntimeError):
    pass


class ImageInputError(ValueError):
    pass


def _svc():
    p = str(settings.ml_src_dir)
    if p not in sys.path:
        sys.path.insert(0, p)
    from imaging import service
    return service


def available() -> bool:
    if not Path(settings.image_model_path).exists():
        return False
    try:
        import torch  # noqa: F401
    except Exception:
        return False
    return True


def _ckpt():
    if not available():
        raise ImageModelUnavailableError("Image model is not installed")
    return _svc().load_checkpoint(str(settings.image_model_path))


def info() -> dict:
    stub = {"id": "image_screening", "name": "Image screening (transfer learning + Grad-CAM)",
            "description": "Classifies a supported medical image and shows a Grad-CAM attention map.",
            "data_type": "image", "status": "unavailable"}
    if not available():
        return stub
    c = _ckpt()
    return {**stub, "status": "available", "model": f"{c['arch']} (weights: {c['weights']})",
            "model_version": c["trained_at"], "threshold": c["threshold"], "dataset": c["dataset"],
            "positive_class": c["positive_class"], "image_size": c["image_size"],
            "accepted_types": ["image/png", "image/jpeg"], "max_bytes": 5 * 1024 * 1024}


def screen(data: bytes) -> dict:
    svc = _svc()
    ck = _ckpt()
    try:
        return svc.screen_image(data, ck)
    except svc.ImageValidationError as e:
        raise ImageInputError(str(e)) from e


def load_metrics() -> dict | None:
    path = settings.ml_eval_dir / "image_metrics.json"
    return json.loads(path.read_text()) if path.exists() else None
