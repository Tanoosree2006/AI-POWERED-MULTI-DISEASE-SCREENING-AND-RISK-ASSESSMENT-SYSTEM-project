"""Inference: validate -> preprocess -> classify -> Grad-CAM overlay (nothing is written to disk)."""
import base64
import io
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from config import DISCLAIMER
from imaging.gradcam import GradCAM
from imaging.model import build_model, target_layer
from imaging.preprocess import ImageValidationError, to_tensor, validate_image_bytes  # noqa: F401

CAVEAT = ("Grad-CAM shows where the model focused for this image. It is a visualisation of model attention, "
          "not proof of disease and not a clinically validated explanation.")


@lru_cache(maxsize=2)
def load_checkpoint(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image model not found: {path}")
    ckpt = torch.load(p, map_location="cpu", weights_only=False)
    net = build_model(ckpt["arch"], len(ckpt["class_names"]), pretrained=False)
    net.load_state_dict(ckpt["state_dict"])
    net.eval()
    return {**ckpt, "net": net}


def _png_b64(arr_uint8) -> str:
    buf = io.BytesIO()
    Image.fromarray(arr_uint8).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def overlay(img: Image.Image, cam: np.ndarray, size: int, alpha: float = 0.45) -> np.ndarray:
    import matplotlib
    colored = (matplotlib.colormaps["jet"](cam)[..., :3] * 255).astype("uint8")
    base = np.asarray(img.resize((size, size), Image.BILINEAR), dtype="float32")
    return ((1 - alpha) * base + alpha * colored.astype("float32")).clip(0, 255).astype("uint8")


def screen_image(data: bytes, ckpt: dict, with_gradcam: bool = True) -> dict:
    img = validate_image_bytes(data)
    size = ckpt["image_size"]
    x = to_tensor(img, size, ckpt["mean"], ckpt["std"])
    net, pos = ckpt["net"], ckpt["positive_index"]
    if with_gradcam:
        cam_gen = GradCAM(net, target_layer(net))
        try:
            cam, probs = cam_gen(x, pos)
        finally:
            cam_gen.remove()
    else:
        with torch.no_grad():
            probs = torch.softmax(net(x), dim=1)
        cam = None
    score = float(probs[0, pos])
    out = {"model": f"{ckpt['arch']} (transfer learning, weights: {ckpt['weights']})",
           "positive_class": ckpt["positive_class"], "screening_score": round(score, 4),
           "threshold": ckpt["threshold"], "screening_flag": "elevated" if score >= ckpt["threshold"] else "lower",
           "warnings": [], "disclaimer": DISCLAIMER,
           "image": {"width": img.size[0], "height": img.size[1]}}
    if cam is not None:
        out["gradcam"] = {"method": "grad-cam", "target_class": ckpt["positive_class"], "caveat": CAVEAT,
                          "overlay_png_base64": _png_b64(overlay(img, cam[0].numpy(), size))}
    return out
