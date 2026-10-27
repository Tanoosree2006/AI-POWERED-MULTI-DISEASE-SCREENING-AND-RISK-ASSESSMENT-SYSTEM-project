"""Train the image-screening model by transfer learning.

Usage (from ml/):
  python src/imaging/train_image.py --data data/images/malaria --positive Parasitized --epochs 5 \
         --dataset-desc "NIH malaria cell images (Kaggle copy)"
Folder layout: <data>/<class_name>/*.png|jpg   (two classes). Test data is split off first and used ONCE.
WARNING: split by IMAGE unless you can split by PATIENT. Several images from one patient in train and test inflate
scores (patient-level leakage). Record this limitation in any report.
"""
import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms as T
from torchvision.datasets import ImageFolder

from config import EVAL_DIR, MODEL_DIR, ensure_dirs
from imaging.model import build_model
from imaging.preprocess import IMAGENET_MEAN, IMAGENET_STD
from metrics import compute_metrics

SEED = 42


class Subset(Dataset):
    def __init__(self, base, indices, transform):
        self.base, self.indices, self.transform = base, indices, transform

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, i):
        path, label = self.base.samples[self.indices[i]]
        img = self.base.loader(path).convert("RGB")
        return self.transform(img), label


def make_splits(targets, max_per_class=None, seed=SEED):
    idx = np.arange(len(targets))
    t = np.array(targets)
    if max_per_class:
        rng = np.random.RandomState(seed)
        idx = np.concatenate([rng.permutation(idx[t == c])[:max_per_class] for c in np.unique(t)])
        t = t[idx]
    tmp, te = train_test_split(idx, test_size=0.15, stratify=t, random_state=seed)
    t_tmp = np.array(targets)[tmp]
    tr, va = train_test_split(tmp, test_size=0.1765, stratify=t_tmp, random_state=seed)  # ~70/15/15
    return tr, va, te


def evaluate(net, loader, pos_index, device):
    net.eval()
    ys, ps = [], []
    with torch.no_grad():
        for x, y in loader:
            p = torch.softmax(net(x.to(device)), dim=1)[:, pos_index].cpu().numpy()
            ps.append(p); ys.append((y == pos_index).numpy().astype(int))
    return np.concatenate(ys), np.concatenate(ps)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--positive", required=True)
    ap.add_argument("--arch", default="resnet18", choices=["resnet18", "resnet50"])
    ap.add_argument("--epochs", type=int, default=5); ap.add_argument("--image-size", type=int, default=224)
    ap.add_argument("--batch-size", type=int, default=32); ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--weights", choices=["imagenet", "none"], default="imagenet")
    ap.add_argument("--max-per-class", type=int, default=None, help="subsample for quick CPU runs")
    ap.add_argument("--dataset-desc", default="unspecified image dataset")
    ap.add_argument("--out", default=str(MODEL_DIR / "image_model.pt"))
    ap.add_argument("--metrics-out", default=str(EVAL_DIR / "image_metrics.json"))
    a = ap.parse_args(argv)

    ensure_dirs()
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    base = ImageFolder(a.data)
    if len(base.classes) != 2 or a.positive not in base.classes:
        raise SystemExit(f"Need exactly 2 class folders including '{a.positive}'; found {base.classes}")
    pos = base.class_to_idx[a.positive]
    tr, va, te = make_splits(base.targets, a.max_per_class)
    print(f"classes={base.classes} positive={a.positive} train={len(tr)} val={len(va)} test={len(te)}")

    norm = T.Normalize(IMAGENET_MEAN, IMAGENET_STD)
    train_tf = T.Compose([T.Resize((a.image_size, a.image_size)), T.RandomHorizontalFlip(), T.RandomRotation(15),
                          T.ToTensor(), norm])
    eval_tf = T.Compose([T.Resize((a.image_size, a.image_size)), T.ToTensor(), norm])
    mk = lambda ids, tf, sh: DataLoader(Subset(base, ids, tf), batch_size=a.batch_size, shuffle=sh, num_workers=0)
    dl_tr, dl_va, dl_te = mk(tr, train_tf, True), mk(va, eval_tf, False), mk(te, eval_tf, False)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    net = build_model(a.arch, 2, pretrained=a.weights == "imagenet").to(device)
    opt = torch.optim.AdamW([p for p in net.parameters() if p.requires_grad], lr=a.lr)
    loss_fn = nn.CrossEntropyLoss()
    best_auc, best_state, history = -1.0, None, []
    for ep in range(1, a.epochs + 1):
        net.train(); total = 0.0
        for x, y in dl_tr:
            opt.zero_grad(); loss = loss_fn(net(x.to(device)), y.to(device)); loss.backward(); opt.step()
            total += loss.item() * len(y)
        yv, pv = evaluate(net, dl_va, pos, device)
        m = compute_metrics(yv, pv) if len(set(yv)) == 2 else {"roc_auc": float("nan")}
        history.append({"epoch": ep, "train_loss": round(total / len(tr), 4), "val_roc_auc": round(m["roc_auc"], 4)})
        print(history[-1])
        if m["roc_auc"] >= best_auc:   # selection on VALIDATION only
            best_auc, best_state = m["roc_auc"], {k: v.cpu().clone() for k, v in net.state_dict().items()}
    net.load_state_dict(best_state)
    yt, pt = evaluate(net, dl_te, pos, device)           # test set used once
    test = compute_metrics(yt, pt)
    print("TEST:", {k: round(v, 4) for k, v in test.items() if k != "confusion_matrix"}, test["confusion_matrix"])

    torch.save({"state_dict": best_state, "arch": a.arch, "class_names": base.classes, "positive_class": a.positive,
                "positive_index": pos, "image_size": a.image_size, "mean": IMAGENET_MEAN, "std": IMAGENET_STD,
                "threshold": 0.5, "weights": a.weights, "dataset": a.dataset_desc,
                "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}, a.out)
    Path(a.metrics_out).write_text(json.dumps(
        {"module": "image_screening", "dataset": a.dataset_desc, "arch": a.arch, "weights": a.weights,
         "split": {"train": len(tr), "val": len(va), "test": len(te)}, "history": history, "test": test,
         "limitations": ["Split by image, not by patient, unless the dataset provides patient IDs.",
                         "Not clinically validated; Grad-CAM shows model attention only."]}, indent=2))
    print("saved", a.out)


if __name__ == "__main__":
    main()
