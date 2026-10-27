"""Loaders for the diabetes and heart-disease modules.

Both files are third-party GitHub copies of public datasets. Downloads are verified with a SHA-256 checksum, so
every run of the project uses byte-identical data. Original sources: Pima Indians Diabetes Database (NIDDK;
Smith et al. 1988) and UCI Heart Disease, Cleveland subset (Detrano et al. 1989). Check each licence before
redistributing the files; this repository does NOT redistribute them (see .gitignore).
"""
import hashlib
import urllib.request

import numpy as np
import pandas as pd

from config import DATA_DIR

PIMA_URL = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
PIMA_SHA256 = "6bfe5d0f379d17a0e0819b996407e3c09bf80febd4287f2ed212190dfff154af"
HEART_URL = "https://raw.githubusercontent.com/sharmaroshan/Heart-UCI-Dataset/master/heart.csv"
HEART_SHA256 = "7c3014365675306819510a49ff289efbec1d1a6a666a2dc7652f1547b383d859"

PIMA_COLUMNS = ["pregnancies", "glucose", "blood_pressure", "skin_thickness", "insulin", "bmi",
                "diabetes_pedigree", "age", "outcome"]
PIMA_ZERO_MEANS_MISSING = ["glucose", "blood_pressure", "skin_thickness", "insulin", "bmi"]


def _fetch(url: str, filename: str, sha256: str):
    path = DATA_DIR / filename
    if not path.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=30) as r:  # nosec: fixed https URL
            path.write_bytes(r.read())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != sha256:
        raise ValueError(f"Checksum mismatch for {filename}: expected {sha256[:12]}..., got {digest[:12]}... "
                         "Delete the file to re-download, or verify the source changed.")
    return path


def load_pima():
    """Pima Indians Diabetes: 768 rows. Physiologically impossible zeros are treated as MISSING (NaN) and
    imputed later inside the pipeline (fitted on training data only). outcome 1 = diabetes."""
    df = pd.read_csv(_fetch(PIMA_URL, "pima_raw.csv", PIMA_SHA256), header=None, names=PIMA_COLUMNS)
    df[PIMA_ZERO_MEANS_MISSING] = df[PIMA_ZERO_MEANS_MISSING].replace(0, np.nan)
    y = df.pop("outcome").astype(int).rename("diabetes")
    return df.astype(float), y


def check_heart_label_direction(df: pd.DataFrame):
    """The public heart.csv labels 1 = NO disease (inverted vs. common documentation). Verify from the data,
    using medically expected directions: patients WITH disease reach a lower maximum heart rate and have more
    exercise-induced angina."""
    g = df.groupby("target")
    if not (g.thalach.mean()[1] > g.thalach.mean()[0] and g.exang.mean()[1] < g.exang.mean()[0]):
        raise ValueError("Heart label direction check failed: target coding differs from the expected file.")


def load_heart():
    """UCI Cleveland heart disease: 303 rows -> 302 after removing 1 duplicate. 'disease' = (target == 0).
    Invalid codes (ca == 4, thal == 0) are treated as missing and imputed inside the pipeline."""
    df = pd.read_csv(_fetch(HEART_URL, "heart_raw.csv", HEART_SHA256), encoding="utf-8-sig")
    check_heart_label_direction(df)
    df = df.drop_duplicates().reset_index(drop=True)
    y = (df.pop("target") == 0).astype(int).rename("heart_disease")
    df["ca"] = df["ca"].replace(4, np.nan)
    df["thal"] = df["thal"].replace(0, np.nan)
    return df.astype(float), y
