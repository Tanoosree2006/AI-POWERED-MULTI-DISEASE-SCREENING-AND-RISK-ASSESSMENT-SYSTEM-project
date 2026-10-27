# Milestone 4: diabetes and heart-disease modules

Adds two real structured-data modules next to breast cancer, using the **same leakage-safe protocol**, the same explanation method and the same API. The web form and the model-performance page pick them up automatically (no frontend change needed).

## Run it (from the repository root, venv active, `pip install -r backend/requirements.txt` done)
```powershell
cd ml
python src/train_module.py diabetes         # downloads the dataset once, verifies its SHA-256, trains, evaluates, saves
python src/train_module.py heart_disease
python -m pytest -q tests/test_modules.py   # 9 tests specific to M4
cd ..\backend
python -m pytest -q tests/test_modules_api.py   # 11 API tests specific to M4
```
Outputs per module: `ml/models/<slug>_pipeline.joblib`, `ml/evaluation/<slug>_metrics.json`, `<slug>_shap_global.json`, and figures in `ml/evaluation/figures/` (ROC, confusion matrix, calibration, SHAP bar). `python scripts/make_results_md.py` rebuilds `docs/RESULTS.md`.

## Files added or changed for M4
| File | Purpose |
|---|---|
| `ml/src/datasets.py` | loaders with SHA-256 verification; Pima zeros-as-missing; heart label-direction check, duplicate removal, invalid-code cleaning |
| `ml/src/modules.py` | registry of modules: feature definitions (label, unit, range, allowed codes, optional) used for validation and for the web form |
| `ml/src/engine.py` | generic validated inference: ranges, allowed codes, optional blanks imputed with a warning, SHAP explanation |
| `ml/src/train_module.py` | generic trainer: 60/20/20 stratified split, imputation + scaling inside the pipeline, CV tuning on train, selection on validation, one test evaluation, repeated CV, high-sensitivity operating point, SHAP |
| `ml/tests/test_modules.py` | loader, label-direction, checksum, leakage (imputer medians and scaler means come from train rows), validation rules, SHAP additivity for Random Forest and XGBoost |
| `backend/app/services/ml_service.py` and routes | multi-module registry; `GET /api/v1/diseases` returns field metadata; `GET /api/v1/diseases/{d}/examples` |
| `backend/tests/test_modules_api.py` | every module scores and explains; blank/optional/invalid values; coded values; metrics for all modules |

## Data problems found and handled (worth explaining in your viva)
- **Pima diabetes:** physiologically impossible zeros (glucose 5, blood pressure 35, skin thickness 227, insulin 374, BMI 11) mean "missing". They are converted to blanks and imputed with **training-set medians inside the pipeline**; users may leave those fields blank, and the API warns that reliability drops.
- **Heart disease:** the public `heart.csv` labels `1 = no disease` (inverted compared with common documentation). The code **verifies the direction from the data** (patients coded 0 have a lower maximum heart rate and more exercise angina) and re-codes so 1 = disease; a test proves the check fails on flipped labels. One duplicate row is removed (303 to 302). Invalid codes (`ca = 4`, `thal = 0`) are treated as missing.
- **Heart categorical codes** are used as ordinal numbers so SHAP can attribute to the original features; this is a limitation for nominal variables. The clinical meaning of some codes is inconsistently documented, so the form labels them "code" instead of inventing meanings.

## Results (from `docs/RESULTS.md`; threshold 0.5; test sets are small)
| Module | Selected on validation | Accuracy | Sensitivity | Specificity | ROC-AUC | Test size (positives) |
|---|---|---|---|---|---|---|
| Diabetes | Random Forest | 0.7403 | 0.5370 | 0.8500 | 0.8141 | 154 (54) |
| Heart disease | Random Forest | 0.8361 | 0.7143 | 0.9394 | 0.9167 | 61 (28) |

- Repeated 5-fold CV (train+validation) ROC-AUC: diabetes 0.826 to 0.842 across the three models; heart disease 0.893 to 0.912.
- **Diabetes misses almost half of positives at 0.5.** Choosing a threshold on the validation set (0.2748) raises test sensitivity to 0.852 and drops specificity to 0.620. Heart disease at its validation-chosen threshold (0.2403): sensitivity 0.964, specificity 0.545.
- On heart disease the model chosen on validation (Random Forest, AUC 0.917) is not the best on the test set (Logistic Regression, 0.937). With 61 test patients this is noise; do not declare a winner.
- Top SHAP features: diabetes: glucose, bmi, age, diabetes_pedigree, insulin. Heart disease: cp, thal, exang, ca, slope.
- Not comparable with the base paper (it reports accuracy only, on its own splits and dataset versions).

## Limitations
Small datasets; Pima is one population (female patients of Pima heritage); no external validation; scores are uncalibrated (calibration error is visible in `RESULTS.md`, e.g. heart ECE 0.15 to 0.21); a third-party GitHub copy of each dataset is used, so confirm the original licences before redistributing; ordinal coding of nominal heart variables.

## Add another tabular module
Add a loader to `ml/src/datasets.py`, a `ModuleSpec` with its `FeatureSpec` list to `ml/src/modules.py`, run `python src/train_module.py <slug>`. The API, form, history and metrics page need no changes.

## Not verified
Executed only on Linux with SQLite. The M4 code paths ran in a clean-clone check (train, tests, migration), but PostgreSQL and Windows were not exercised.
