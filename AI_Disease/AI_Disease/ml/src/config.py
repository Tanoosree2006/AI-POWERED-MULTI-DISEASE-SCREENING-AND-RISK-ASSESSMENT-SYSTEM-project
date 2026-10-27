"""Central configuration: paths and constants shared by every script."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
EVAL_DIR = ROOT / "evaluation"
FIG_DIR = EVAL_DIR / "figures"
EXAMPLES_DIR = ROOT / "examples"
MODEL_PATH = MODEL_DIR / "breast_cancer_pipeline.joblib"

SEED = 42
THRESHOLD = 0.5          # decision threshold on the model score
TARGET = "malignant"     # positive class = 1 = malignant
DISCLAIMER = ("Model-estimated screening score from a research prototype. "
              "NOT a diagnosis and not clinically validated. Consult a qualified clinician.")


def ensure_dirs():
    for d in (DATA_DIR, MODEL_DIR, EVAL_DIR, FIG_DIR, EXAMPLES_DIR):
        d.mkdir(parents=True, exist_ok=True)
