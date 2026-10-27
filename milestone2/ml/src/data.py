"""Data loading, validation and splitting for the WDBC breast cancer module.

Source: UCI ML Repository, Breast Cancer Wisconsin (Diagnostic), dataset id 17,
CC BY 4.0. We read the identical copy bundled with scikit-learn, so no download
is needed. Label coding: 1 = malignant (positive class), 0 = benign.
"""
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

from config import SEED


def validate_dataset(X: pd.DataFrame, y: pd.Series) -> bool:
    if len(X) != len(y):
        raise ValueError("X and y have different lengths")
    if X.isna().any().any():
        raise ValueError("Dataset contains missing values")
    if not all(pd.api.types.is_numeric_dtype(t) for t in X.dtypes):
        raise ValueError("All features must be numeric")
    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError("Dataset contains infinite values")
    if (X < 0).any().any():
        raise ValueError("Negative values found; all WDBC features are non-negative")
    if not set(pd.unique(y)).issubset({0, 1}):
        raise ValueError("Target must be binary 0/1")
    return True


def load_data():
    raw = load_breast_cancer(as_frame=True)
    X = raw.data.copy()
    y = (raw.target == 0).astype(int).rename("malignant")  # sklearn codes malignant as 0
    validate_dataset(X, y)
    return X, y


def split_data(X, y, seed: int = SEED):
    """Stratified 60/20/20 train/validation/test split."""
    X_tmp, X_test, y_tmp, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=seed)
    X_train, X_val, y_train, y_val = train_test_split(
        X_tmp, y_tmp, test_size=0.25, stratify=y_tmp, random_state=seed)
    return X_train, X_val, X_test, y_train, y_val, y_test
