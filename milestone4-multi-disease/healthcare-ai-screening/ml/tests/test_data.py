import numpy as np
import pytest
from data import load_data, split_data, validate_dataset


def test_shape_and_labels():
    X, y = load_data()
    assert X.shape == (569, 30)
    assert set(y.unique()) == {0, 1}
    assert int(y.sum()) == 212  # malignant count documented by UCI


def test_no_missing_or_duplicates():
    X, _ = load_data()
    assert X.isna().sum().sum() == 0
    assert X.duplicated().sum() == 0


def test_split_sizes_disjoint_and_stratified():
    X, y = load_data()
    Xtr, Xv, Xte, ytr, yv, yte = split_data(X, y)
    assert len(Xtr) + len(Xv) + len(Xte) == len(X)
    assert not (set(Xtr.index) & set(Xv.index) or set(Xtr.index) & set(Xte.index)
                or set(Xv.index) & set(Xte.index))
    for part in (ytr, yv, yte):
        assert abs(part.mean() - y.mean()) < 0.02


def test_validate_rejects_bad_data():
    X, y = load_data()
    bad = X.copy(); bad.iloc[0, 0] = np.nan
    with pytest.raises(ValueError):
        validate_dataset(bad, y)
    neg = X.copy(); neg.iloc[0, 0] = -1
    with pytest.raises(ValueError):
        validate_dataset(neg, y)
    with pytest.raises(ValueError):
        validate_dataset(X, y.replace({1: 2}))
