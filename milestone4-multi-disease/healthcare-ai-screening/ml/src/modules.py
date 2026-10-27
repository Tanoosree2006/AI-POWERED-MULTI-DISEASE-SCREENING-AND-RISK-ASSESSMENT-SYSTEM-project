"""Registry of disease modules: names, feature definitions (for validation and for the web form), file paths."""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from config import EVAL_DIR, MODEL_DIR, MODEL_PATH


@dataclass
class FeatureSpec:
    name: str
    label: str
    kind: str = "number"            # number | binary | category
    min: Optional[float] = None
    max: Optional[float] = None
    unit: str = ""
    help: str = ""
    allowed: Optional[list] = None  # allowed codes for binary / category
    nullable: bool = False          # may be left blank (imputed by the pipeline)


@dataclass
class ModuleSpec:
    slug: str
    name: str
    description: str
    positive_label: str
    source: str
    bundle_path: Path
    metrics_path: Path
    loader: Callable
    features: Optional[list] = None  # None = derive from the trained bundle


def _num(name, label, lo, hi, unit="", help="", nullable=False):
    return FeatureSpec(name, label, "number", lo, hi, unit, help, None, nullable)


def _bin(name, label, help=""):
    return FeatureSpec(name, label, "binary", 0, 1, "", help, [0, 1])


def _cat(name, label, codes, help=""):
    return FeatureSpec(name, label, "category", min(codes), max(codes), "", help, list(codes))


PIMA_FEATURES = [
    _num("pregnancies", "Pregnancies", 0, 20, "count", "Number of times pregnant"),
    _num("glucose", "Plasma glucose", 30, 400, "mg/dL", "2-hour oral glucose tolerance test. Leave blank if unknown.", True),
    _num("blood_pressure", "Diastolic blood pressure", 20, 140, "mmHg", "Leave blank if unknown.", True),
    _num("skin_thickness", "Triceps skin-fold thickness", 5, 100, "mm", "Leave blank if unknown.", True),
    _num("insulin", "2-hour serum insulin", 10, 900, "µU/mL", "Leave blank if unknown.", True),
    _num("bmi", "Body mass index", 10, 70, "kg/m²", "Leave blank if unknown.", True),
    _num("diabetes_pedigree", "Diabetes pedigree function", 0, 3, "", "Family-history score used in the source study"),
    _num("age", "Age", 18, 100, "years"),
]

CODE_NOTE = "Coded as in the public dataset file; the clinical meaning of some codes is inconsistently documented."
HEART_FEATURES = [
    _num("age", "Age", 20, 100, "years"),
    FeatureSpec("sex", "Sex", "binary", 0, 1, "", "0 = female, 1 = male", [0, 1]),
    _cat("cp", "Chest pain type (code)", [0, 1, 2, 3], CODE_NOTE),
    _num("trestbps", "Resting blood pressure", 80, 220, "mmHg"),
    _num("chol", "Serum cholesterol", 100, 600, "mg/dL"),
    _bin("fbs", "Fasting blood sugar above 120 mg/dL", "0 = no, 1 = yes"),
    _cat("restecg", "Resting ECG result (code)", [0, 1, 2], CODE_NOTE),
    _num("thalach", "Maximum heart rate achieved", 60, 220, "bpm"),
    _bin("exang", "Exercise-induced angina", "0 = no, 1 = yes"),
    _num("oldpeak", "ST depression (exercise vs rest)", 0, 7, "mm"),
    _cat("slope", "Slope of peak-exercise ST segment (code)", [0, 1, 2], CODE_NOTE),
    FeatureSpec("ca", "Major vessels coloured (0-3)", "category", 0, 3, "", "Leave blank if unknown.", [0, 1, 2, 3], True),
    FeatureSpec("thal", "Thalassemia test result (code 1-3)", "category", 1, 3, "", CODE_NOTE + " Leave blank if unknown.", [1, 2, 3], True),
]


def _bc_loader():
    from data import load_data
    return load_data()


def _pima():
    from datasets import load_pima
    return load_pima()


def _heart():
    from datasets import load_heart
    return load_heart()


REGISTRY = {
    "breast_cancer": ModuleSpec(
        "breast_cancer", "Breast cancer screening (Wisconsin Diagnostic dataset)",
        "Classifies a breast mass as malignant or benign from 30 cell-nucleus measurements.",
        "malignant", "UCI Breast Cancer Wisconsin (Diagnostic), id 17, CC BY 4.0",
        MODEL_PATH, EVAL_DIR / "breast_cancer_metrics.json", _bc_loader, None),
    "diabetes": ModuleSpec(
        "diabetes", "Diabetes risk screening (Pima Indians dataset)",
        "Estimates a screening score for diabetes from 8 clinical measurements.",
        "diabetes", "Pima Indians Diabetes Database (NIDDK), GitHub copy verified by SHA-256",
        MODEL_DIR / "diabetes_pipeline.joblib", EVAL_DIR / "diabetes_metrics.json", _pima, PIMA_FEATURES),
    "heart_disease": ModuleSpec(
        "heart_disease", "Heart disease screening (UCI Cleveland dataset)",
        "Estimates a screening score for heart disease from 13 clinical measurements.",
        "heart disease", "UCI Heart Disease, Cleveland subset, GitHub copy verified by SHA-256",
        MODEL_DIR / "heart_disease_pipeline.joblib", EVAL_DIR / "heart_disease_metrics.json", _heart, HEART_FEATURES),
}
