# AI-Powered Multi-Disease Screening and Risk Assessment System
*An Explainable AI-Based Healthcare Screening and Clinical Decision-Support Platform*
Aditya University, CSE, 2026-27. Base paper: Din et al., "Multi-Disease Prediction Using ML and DL Models", Kashf J. Multidisciplinary Research 1(12), 2024, DOI 10.71146/kjmr176.

> **Disclaimer.** Research/academic prototype. Outputs are model-estimated screening scores,
> NOT diagnoses, and the model is NOT clinically validated. Never use it to start, stop or change treatment.

## Stage 1 scope (first ~30%): machine-learning core
Implemented: dataset validation, EDA, preprocessing pipeline, Logistic Regression / Random Forest / XGBoost
comparison, metrics (incl. specificity and calibration), saved model, validated prediction CLI, SHAP
explanations, 26 automated tests.
Not yet implemented (later milestones): FastAPI, PostgreSQL history, React dashboard, additional disease
modules, image module + Grad-CAM, authentication, LLM/RAG.

## Dataset (verified)
**Breast Cancer Wisconsin (Diagnostic), UCI ML Repository, dataset id 17**, https://archive.ics.uci.edu/dataset/17
- License: CC BY 4.0 (stated on the UCI page). Donated 1995 (Street, Wolberg, Mangasarian).
- 569 samples, 30 numeric features, no missing values; 212 malignant (37.3%) and 357 benign.
- Features: 10 properties of cell nuclei (radius, texture, perimeter, area, smoothness, compactness,
  concavity, concave points, symmetry, fractal dimension), each as mean, standard error ("error") and
  "worst" (mean of the 3 largest) = 30. Computed from a digitised fine-needle-aspirate image.
- Target: diagnosis. **We code 1 = malignant (positive class), 0 = benign** (scikit-learn codes it the other way).
- Access: we use the identical copy bundled with scikit-learn, so no download or internet is needed.
  `python src/prepare_data.py` also exports it to `ml/data/wdbc.csv`.
- Limitations: small (569), one institution, features derived from images (not raw clinical data), no patient
  IDs (patient-level leakage cannot be excluded), strong feature multicollinearity, 1990s data. Results will
  not transfer to other populations without validation.

## Setup (Windows 11, VS Code, PowerShell)
```powershell
cd healthcare-ai-screening\ml
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If activation is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. In VS Code choose the `.venv` interpreter (Ctrl+Shift+P, "Python: Select Interpreter").

## Run each stage (from `ml/`)
```powershell
python src/prepare_data.py     # exports CSV + examples/sample_*.json
python src/eda.py              # evaluation/eda_report.json + 4 figures
python src/train.py            # trains, selects on validation, tests once, saves model
python src/explain.py          # SHAP global + local explanations and figures
python src/predict.py --json examples/sample_malignant.json --explain
python src/predict.py --sample benign
python -m pytest -v            # 26 tests
```
Outputs: `models/breast_cancer_pipeline.joblib`, `evaluation/breast_cancer_metrics.json`,
`evaluation/results_table.md`, `evaluation/shap_global_importance.json`, `evaluation/figures/*.png`.

## Method
1. 60/20/20 stratified split (341/114/114), fixed seed 42.
2. Scalers sit inside sklearn `Pipeline`s, so they are fitted on training data only (tested).
3. Each model is tuned with 5-fold stratified CV (ROC-AUC) on the TRAINING set only.
4. The model is **selected on the validation set** (AUC, ties by recall, then Brier score).
5. The **test set is used once** for the final report. Threshold fixed at 0.5.

## Actual results (test set, n=114: 72 benign, 42 malignant; threshold 0.5)
Produced by `python src/train.py` in my run (Linux, Python 3.12). Your Windows run should match
closely for Logistic Regression; tree models can differ slightly across library versions.

| Model | Acc | Precision | Recall (sens.) | Specificity | F1 | ROC-AUC | Brier | ECE | TN/FP/FN/TP |
|---|---|---|---|---|---|---|---|---|---|
| **Logistic Regression (selected)** | 0.9737 | 0.9756 | 0.9524 | 0.9861 | 0.9639 | 0.9954 | 0.0214 | 0.0308 | 71/1/2/40 |
| Random Forest | 0.9561 | 0.9744 | 0.9048 | 0.9861 | 0.9383 | 0.9960 | 0.0307 | 0.0591 | 71/1/4/38 |
| XGBoost | 0.9737 | 1.0000 | 0.9286 | 1.0000 | 0.9630 | 0.9934 | 0.0214 | 0.0238 | 72/0/3/39 |

Validation ROC-AUC (used for selection): LR 0.9957, RF 0.9920, XGB 0.9954.

**Interpretation and honesty notes**
- With 42 malignant test cases, one patient changes sensitivity by about 2.4 points. The differences
  between models are within noise; do not claim one is truly better.
- Accuracy alone misleads on imbalanced medical data (37% positive here; a model that says "benign"
  for everyone scores 63%). Sensitivity (missed cancers) and specificity (false alarms) matter more.
- Scores are **not calibrated probabilities** (ECE 0.03 on a tiny test set; many scores sit near 0 or 1).
  Call them "model-estimated screening scores".
- This is a very clean, well-separated dataset; results are optimistic compared with real screening.

## Explainability (SHAP)
Computed on the actual saved model (`src/explain.py`). Units are log-odds for LR/XGBoost, probability for RF.
- **Global** (mean |SHAP| on test): top features were worst texture, mean concave points, worst symmetry,
  radius error, worst radius. See `evaluation/figures/shap_global_bar.png` and `shap_beeswarm.png`.
- **Local**: `predict.py --explain` returns the top-k features pushing one record's score up or down;
  tests verify base value + sum(SHAP) reconstructs the model output.
- Caveats: SHAP explains the MODEL, not biology. Correlated features (radius/perimeter/area) share credit,
  so importance rankings are unstable. Global importance differs from individual explanations.

## Tests (26, all passing in my run)
Data validation, split integrity, leakage check (scaler stats equal train means), metric correctness,
model reload, input validation (missing/unknown/negative/NaN/inf/string/None/bool), out-of-range warning,
CLI success and failure exit codes, SHAP additivity. Sanity floors in the model test (AUC > 0.95,
recall > 0.85) are smoke checks, not clinical claims.

## Folder structure
```
healthcare-ai-screening/
|-- README.md, .gitignore
`-- ml/
    |-- requirements.txt, pytest.ini
    |-- src/   config.py data.py metrics.py eda.py train.py explain.py predict.py prepare_data.py
    |-- tests/ conftest.py test_data.py test_model.py test_predict.py test_explain.py
    |-- examples/  sample_malignant.json sample_benign.json
    |-- data/ models/ evaluation/ (generated)
```

## Troubleshooting
| Problem | Fix |
|---|---|
| `Model not found` | Run `python src/train.py` first |
| `ModuleNotFoundError: shap` | Activate the venv, then `pip install -r requirements.txt` |
| `ModuleNotFoundError: config` | Run scripts from the `ml/` folder as shown |
| PowerShell blocks activation | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `xgboost` fails to install | Training skips it automatically and compares LR and RF |
| JSON file rejected on Windows | Save as UTF-8; BOM is handled. Keys must match the 30 feature names exactly |
| Slightly different metrics | Library version differences; keep your own numbers and report them |

## Next milestones
2. FastAPI (`/health`, `/api/v1/diseases`, `/api/v1/screening/breast_cancer`) + PostgreSQL history.
3. React dashboard and form. 4. Diabetes and heart-disease modules (base-paper datasets).
5. Image module (transfer learning + Grad-CAM). 6. Docker, report, viva preparation.

---

# Milestone 2: FastAPI backend, database and authentication (implemented and tested)

**Status:** 29 backend tests pass, and the real server was exercised over HTTP against a database built by
Alembic (register, login, screening, history, dashboard, restart persistence). **Not yet verified by the authors:**
PostgreSQL, Docker/Compose, and the Windows setup below (tested on Linux with SQLite).

## Run it (Windows PowerShell, from the repository root)
```powershell
cd backend
pip install -r requirements.txt            # in the same venv as the ml/ module
copy ..\.env.example .env                  # then edit SECRET_KEY
alembic upgrade head                       # creates screening.db with all tables
uvicorn app.main:app --reload --port 8000  # Swagger UI: http://127.0.0.1:8000/docs
python -m pytest -q                        # 29 tests
```
Train the model first if `ml/models/breast_cancer_pipeline.joblib` is missing: `cd ml; python src/train.py`.
Create an admin (optional): `python scripts/create_admin.py yourname` (password prompt; roles cannot be chosen at registration).

## Endpoints (OpenAPI spec: `docs/openapi.json`, live at `/docs`)
| Method and path | Auth | Purpose |
|---|---|---|
| GET `/health` | none | Service and model availability |
| GET `/api/v1/diseases` | none | Working modules only (currently `breast_cancer`) |
| POST `/api/v1/auth/register`, `/login` | none (rate-limited) | Create account; get a JWT |
| GET `/api/v1/auth/me` | token | Current user |
| POST `/api/v1/screening/{disease}` | token | Validate, score, explain with SHAP, store the record |
| GET `/api/v1/screening/history` | token | Own records (`scope=all` for admins), paginated |
| GET/DELETE `/api/v1/screening/record/{id}` | token | Read or delete one record (owner or admin) |
| GET `/api/v1/dashboard/summary` | token | Totals, flagged counts, daily trend, recent records from real data |
| GET `/api/v1/models/metrics` | none | Evaluation results written by `ml/src/train.py` |

Errors always look like `{"error": {"code": 422, "message": "..."}}`. Stack traces and submitted values are never returned.
Image screening is intentionally **not exposed**, because that module does not exist yet.

## Security and privacy as implemented
bcrypt password hashing; JWT with expiry; role checks (own records only; admin for `scope=all`); strict numeric
input validation (strings and booleans rejected); CORS limited to configured origins; per-IP rate limiting
(in-memory, single-process prototype); secrets only from environment variables; audit events never contain patient
inputs; users can delete their own records. **Not implemented:** HTTPS termination, password reset, token refresh or
revocation, multi-process rate limiting, formal privacy compliance. Only de-identified public-dataset inputs should be sent.

## Database
Tables: `users`, `disease_modules`, `model_versions` (stores the evaluation metrics of the deployed model),
`screening_records` (inputs, score, flag, warnings, SHAP explanation), `audit_events`.
Migrations: `backend/alembic/versions/`. Default store is SQLite; set `DATABASE_URL` for PostgreSQL.

## Troubleshooting
| Problem | Fix |
|---|---|
| `Model not found` / `/health` shows `unavailable` | Run `python src/train.py` inside `ml/` |
| `no such table` | Run `alembic upgrade head` in `backend/` |
| 401 on every call | Send header `Authorization: Bearer <token>` from `/auth/login` |
| 429 Too many requests | Wait a minute or raise `RATE_LIMIT_PER_MINUTE` |
| CORS error in the browser | Add the frontend origin to `CORS_ORIGINS` |
