"""Safe image loading and preprocessing for the image-screening module."""
import io

from PIL import Image

Image.MAX_IMAGE_PIXELS = 25_000_000  # refuse decompression bombs
MAX_BYTES = 5 * 1024 * 1024
ALLOWED_FORMATS = ("PNG", "JPEG")
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


class ImageValidationError(ValueError):
    pass


def validate_image_bytes(data: bytes, max_bytes: int = MAX_BYTES, min_side: int = 32, max_side: int = 4096):
    """Validate by CONTENT (not file name or declared type). Returns an RGB PIL image."""
    if not data:
        raise ImageValidationError("Empty file")
    if len(data) > max_bytes:
        raise ImageValidationError(f"Image larger than {max_bytes // (1024 * 1024)} MB")
    try:
        probe = Image.open(io.BytesIO(data))
        fmt = probe.format
        probe.verify()                       # structural check
        img = Image.open(io.BytesIO(data))   # re-open: verify() invalidates the object
        img.load()
    except Exception:                        # corrupt data, unsupported format, decompression bomb ...
        raise ImageValidationError("File is not a valid PNG or JPEG image")
    if fmt not in ALLOWED_FORMATS:
        raise ImageValidationError("Only PNG and JPEG images are supported")
    w, h = img.size
    if min(w, h) < min_side or max(w, h) > max_side:
        raise ImageValidationError(f"Image sides must be between {min_side} and {max_side} pixels")
    return img.convert("RGB")


def to_tensor(img, size: int, mean=IMAGENET_MEAN, std=IMAGENET_STD):
    import numpy as np
    import torch
    arr = np.asarray(img.resize((size, size), Image.BILINEAR), dtype="float32") / 255.0
    arr = (arr - np.array(mean, dtype="float32")) / np.array(std, dtype="float32")
    return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).contiguous()
