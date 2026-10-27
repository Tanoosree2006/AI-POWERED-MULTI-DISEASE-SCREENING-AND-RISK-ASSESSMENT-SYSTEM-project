"""Mechanical tests for the image module. They use a SYNTHETIC toy dataset and untrained/lightly-trained networks:
they prove the code paths work, NOT that any medical image model is accurate."""
import base64
import io
import json

import numpy as np
import pytest

torch = pytest.importorskip("torch")
from PIL import Image  # noqa: E402

from imaging import service as svc  # noqa: E402
from imaging.gradcam import GradCAM  # noqa: E402
from imaging.preprocess import ImageValidationError, validate_image_bytes  # noqa: E402
from imaging.train_image import main as train_main  # noqa: E402


def png_bytes(w=64, h=64, color=(120, 30, 30), fmt="PNG"):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format=fmt)
    return buf.getvalue()


def make_toy_dataset(root, n=24, size=64):
    """class 'abnormal' = bright square on noise; class 'normal' = noise only. Purely synthetic."""
    rng = np.random.RandomState(0)
    for cls in ("abnormal", "normal"):
        (root / cls).mkdir(parents=True)
        for i in range(n):
            arr = rng.randint(0, 80, (size, size, 3)).astype("uint8")
            if cls == "abnormal":
                x, y = rng.randint(8, size - 24, 2)
                arr[y:y + 16, x:x + 16] = 230
            Image.fromarray(arr).save(root / cls / f"{i}.png")


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    root = tmp_path_factory.mktemp("toy")
    make_toy_dataset(root / "data")
    out, metrics = root / "model.pt", root / "metrics.json"
    train_main(["--data", str(root / "data"), "--positive", "abnormal", "--epochs", "2", "--image-size", "64",
                "--weights", "none", "--batch-size", "16", "--out", str(out), "--metrics-out", str(metrics),
                "--dataset-desc", "synthetic toy data (test only)"])
    return out, metrics


# ---- input validation -------------------------------------------------------------------------------------------
def test_valid_png_and_jpeg_accepted():
    assert validate_image_bytes(png_bytes()).size == (64, 64)
    assert validate_image_bytes(png_bytes(fmt="JPEG")).mode == "RGB"


@pytest.mark.parametrize("data,msg", [
    (b"", "Empty"),
    (b"this is plain text pretending to be a png", "not a valid"),
    (png_bytes()[:60], "not a valid"),                        # truncated file
    (png_bytes(fmt="GIF"), "Only PNG and JPEG"),
    (png_bytes(16, 16), "between"),                           # too small
    (png_bytes(5000, 10), "between"),                         # too large a side
])
def test_invalid_images_rejected(data, msg):
    with pytest.raises(ImageValidationError, match=msg):
        validate_image_bytes(data)


def test_size_limit_enforced():
    with pytest.raises(ImageValidationError, match="larger than"):
        validate_image_bytes(png_bytes(), max_bytes=100)


# ---- Grad-CAM mechanics -----------------------------------------------------------------------------------------
def test_gradcam_matches_reference_computation():
    torch.manual_seed(0)
    net = torch.nn.Sequential(torch.nn.Conv2d(3, 4, 3, padding=1), torch.nn.ReLU(),
                              torch.nn.Conv2d(4, 6, 3, padding=1, stride=2), torch.nn.ReLU(),
                              torch.nn.AdaptiveAvgPool2d(1), torch.nn.Flatten(), torch.nn.Linear(6, 2)).eval()
    x = torch.randn(1, 3, 16, 16)
    cam_gen = GradCAM(net, net[2])
    cam, probs = cam_gen(x, class_index=1)
    cam_gen.remove()
    # independent reference using autograd.grad
    store = {}
    h = net[2].register_forward_hook(lambda m, i, o: store.__setitem__("a", o))
    logits = net(x.clone().requires_grad_(True)); h.remove()
    g = torch.autograd.grad(logits[0, 1], store["a"])[0]
    ref = torch.relu((g.mean((2, 3), keepdim=True) * store["a"]).sum(1, keepdim=True))
    ref = torch.nn.functional.interpolate(ref, size=(16, 16), mode="bilinear", align_corners=False)[:, 0]
    ref = (ref - ref.min()) / (ref.max() - ref.min() + 1e-8)
    assert cam.shape == (1, 16, 16) and torch.allclose(cam, ref, atol=1e-5)
    assert torch.allclose(probs.sum(1), torch.ones(1)) and len(net[2]._forward_hooks) == 0


def test_gradcam_works_with_frozen_backbone_and_stays_in_range():
    from imaging.model import build_model, target_layer
    net = build_model("resnet18", 2, pretrained=False).eval()
    assert not net.layer1[0].conv1.weight.requires_grad            # backbone frozen, only layer4 + fc train
    g = GradCAM(net, target_layer(net))
    cam, _ = g(torch.randn(2, 3, 64, 64), class_index=0)
    g.remove()
    assert cam.shape == (2, 64, 64) and float(cam.min()) >= 0 and float(cam.max()) <= 1.0 + 1e-6


# ---- training and inference ---------------------------------------------------------------------------------------
def test_training_writes_checkpoint_and_metrics(trained):
    out, metrics = trained
    ck = torch.load(out, map_location="cpu", weights_only=False)
    assert ck["class_names"] == ["abnormal", "normal"] and ck["positive_class"] == "abnormal" and ck["positive_index"] == 0
    m = json.loads(metrics.read_text())
    assert sum(m["split"].values()) == 48 and "recall_sensitivity" in m["test"] and len(m["history"]) == 2
    assert "patient" in " ".join(m["limitations"])


def test_split_has_no_overlap():
    from imaging.train_image import make_splits
    tr, va, te = make_splits([0] * 40 + [1] * 40)
    assert not (set(tr) & set(va) or set(tr) & set(te) or set(va) & set(te)) and len(tr) + len(va) + len(te) == 80


def test_screen_image_returns_score_flag_and_heatmap(trained):
    ck = svc.load_checkpoint(str(trained[0]))
    out = svc.screen_image(png_bytes(), ck)
    assert 0 <= out["screening_score"] <= 1 and out["screening_flag"] in {"elevated", "lower"}
    ov = Image.open(io.BytesIO(base64.b64decode(out["gradcam"]["overlay_png_base64"])))
    assert ov.size == (64, 64) and "not proof of disease" in out["gradcam"]["caveat"]
    assert "gradcam" not in svc.screen_image(png_bytes(), ck, with_gradcam=False)


def test_screen_image_rejects_bad_input(trained):
    ck = svc.load_checkpoint(str(trained[0]))
    with pytest.raises(ImageValidationError):
        svc.screen_image(b"not an image", ck)


def test_missing_checkpoint_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        svc.load_checkpoint(str(tmp_path / "nope.pt"))
