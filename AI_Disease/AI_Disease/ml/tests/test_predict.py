import json
import subprocess
import sys
from pathlib import Path

import pytest
from data import load_data
from predict import InputValidationError, predict

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def profiles():
    X, y = load_data()
    return X[y == 1].mean().to_dict(), X[y == 0].mean().to_dict()


def test_valid_prediction_structure(profiles):
    out = predict(profiles[0])
    assert 0 <= out["screening_score"] <= 1
    assert out["screening_flag"] in {"elevated", "lower"}
    assert "NOT a diagnosis" in out["disclaimer"]


def test_class_mean_profiles_ordered(profiles):
    mal, ben = predict(profiles[0]), predict(profiles[1])
    assert mal["screening_score"] > ben["screening_score"]
    assert mal["screening_flag"] == "elevated" and ben["screening_flag"] == "lower"


def test_deterministic(profiles):
    assert predict(profiles[0]) == predict(profiles[0])


def test_missing_feature(profiles):
    rec = dict(profiles[0]); rec.pop("mean radius")
    with pytest.raises(InputValidationError, match="Missing"):
        predict(rec)


def test_unknown_feature(profiles):
    with pytest.raises(InputValidationError, match="Unknown"):
        predict({**profiles[0], "age": 50})


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf"), "12.5", None, True])
def test_bad_values(profiles, bad):
    with pytest.raises(InputValidationError):
        predict({**profiles[0], "mean radius": bad})


def test_non_dict_rejected():
    with pytest.raises(InputValidationError):
        predict([1, 2, 3])


def test_out_of_range_warns_but_predicts(profiles):
    out = predict({**profiles[0], "mean radius": 500.0})
    assert out["warnings"] and 0 <= out["screening_score"] <= 1


def test_cli_success_and_failure(tmp_path):
    ok = subprocess.run([sys.executable, "src/predict.py", "--json", "examples/sample_malignant.json"],
                        cwd=ROOT, capture_output=True, text=True)
    assert ok.returncode == 0 and "screening_score" in json.loads(ok.stdout)
    bad = tmp_path / "bad.json"; bad.write_text('{"mean radius": 1}')
    fail = subprocess.run([sys.executable, "src/predict.py", "--json", str(bad)],
                          cwd=ROOT, capture_output=True, text=True)
    assert fail.returncode == 2 and "error" in json.loads(fail.stderr)
