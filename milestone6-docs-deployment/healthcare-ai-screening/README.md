# AI-Powered Multi-Disease Screening and Risk Assessment System
*An Explainable AI-Based Healthcare Screening and Clinical Decision-Support Platform* (Aditya University, CSE, 2026-27)

> **Research prototype, not a medical device.** Outputs are model-estimated screening scores, not diagnoses, and are not clinically validated. Use public, de-identified research data only.

## What it is
One web application with three structured-data screening modules (breast cancer, diabetes, heart disease), SHAP explanations, authenticated screening history, a dashboard, a model-performance page, and an image-screening pipeline (transfer learning + Grad-CAM) whose **code is complete but whose medical model is not trained** (see `docs/IMAGE_MODULE.md`).

| Layer | Stack |
|---|---|
| ML | Python, pandas, NumPy, scikit-learn (Logistic Regression, Random Forest), XGBoost, SHAP, joblib |
| Images | PyTorch, torchvision ResNet transfer learning, Grad-CAM, Pillow |
| Backend | FastAPI, Pydantic, SQLAlchemy 2, Alembic, JWT, bcrypt (SQLite default, PostgreSQL configurable) |
| Frontend | React 18, Vite, Tailwind CSS 3, React Router, Axios, Recharts, Lucide |
| Tests | pytest (ML + backend), Vitest + Testing Library (frontend), a live API integration script |

Honest status of every feature (including what was **not** executed): **`docs/STATUS.md`**. Results: **`docs/RESULTS.md`** (generated from the evaluation files). Architecture: `docs/ARCHITECTURE.md`. Report draft: `docs/PROJECT_REPORT_DRAFT.md`. API spec: `docs/openapi.json`.

## Repository layout
```
ml/        src/ (data, datasets, modules, train.py, train_module.py, engine, explain, predict, imaging/)  tests/  evaluation/  models/
backend/   app/ (api, core, models, schemas, services)  alembic/  tests/  scripts/create_admin.py
frontend/  src/ (pages, components, hooks, services, utils, test)  scripts/integration.mjs
docs/  scripts/  docker-compose.yml  .env.example
```

## Setup on Windows 11 (PowerShell, VS Code terminal)
Install Python 3.12 and Node.js 20+ first.
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1                       # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r backend/requirements.txt          # includes the ml requirements
# 1) Train the models (the diabetes and heart datasets are downloaded once and verified by SHA-256)
cd ml
python src/train.py                               # breast cancer
python src/train_module.py diabetes
python src/train_module.py heart_disease
cd ..\backend
copy ..\.env.example .env                         # edit SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000         # API docs: http://127.0.0.1:8000/docs
# 2) In a second terminal
cd frontend
copy .env.example .env
npm install
npm run dev                                       # http://localhost:5173
```
Register an account in the browser and start a screening. Optional admin: `cd backend; python scripts/create_admin.py yourname`.

## Run all tests
```powershell
powershell -File scripts\run_all_tests.ps1        # ml, backend, frontend tests + production build
```
Counts at the time of writing: ML 50, backend 53, frontend 48 tests (all passing in the build environment), plus a live integration run (`node frontend/scripts/integration.mjs http://127.0.0.1:8000`) that exercised registration, login, all three modules, history, dashboard, metrics, deletion and (with a toy model installed) image upload. Image tests use synthetic data and prove mechanics only.

## Headline results (test sets, threshold 0.5; see docs/RESULTS.md for all metrics)
| Module | Selected model | Sensitivity | Specificity | ROC-AUC | Test size (positives) |
|---|---|---|---|---|---|
| Breast cancer | Logistic Regression | 0.952 | 0.986 | 0.995 | 114 (42) |
| Diabetes | Random Forest | 0.537 | 0.850 | 0.814 | 154 (54) |
| Heart disease | Random Forest | 0.714 | 0.939 | 0.917 | 61 (28) |

The test sets are small, so differences between models are within noise. Diabetes at the default threshold misses almost half of positives; a validation-chosen threshold raises sensitivity to 0.852 at the cost of specificity 0.620. Scores are uncalibrated and are not probabilities. These results cannot be compared with the base paper's accuracy figures (different splits and possibly dataset versions).

## Datasets
- Breast cancer: UCI Breast Cancer Wisconsin (Diagnostic), id 17, CC BY 4.0 (bundled with scikit-learn).
- Diabetes: Pima Indians Diabetes Database (NIDDK), GitHub copy; zeros that are physiologically impossible are treated as missing.
- Heart disease: UCI Heart Disease (Cleveland), GitHub copy; the public file's label is inverted and is verified and re-coded in code (`datasets.py`, tested).
The CSVs are downloaded on first use and are **not** redistributed here; confirm each licence before sharing them.

## API summary (full spec: docs/openapi.json, live at /docs)
`GET /health` · `GET /api/v1/diseases` · `GET /api/v1/diseases/{d}/examples` · `POST /api/v1/auth/register|login` · `GET /api/v1/auth/me` · `POST /api/v1/screening/{disease}` · `GET /api/v1/screening/history` · `GET|DELETE /api/v1/screening/record/{id}` · `GET /api/v1/dashboard/summary` · `GET /api/v1/models/metrics` · `POST /api/v1/images/screening` (only when an image model is installed). Errors always use `{"error": {"code", "message"}}`.

## Security and privacy (implemented)
bcrypt hashing, JWT with expiry, per-user isolation, admin scope, strict validation, CORS allow-list, rate limiting (in-memory), no stack traces or submitted values in errors, secrets from environment variables, audit trail without inputs, user-controlled deletion, images analysed in memory and never stored. **Not implemented:** HTTPS termination, password reset, token revocation, distributed rate limiting, formal privacy compliance.

## Troubleshooting
| Problem | Fix |
|---|---|
| `/health` shows a module `unavailable` | Train it: `python src/train.py` or `python src/train_module.py diabetes|heart_disease` in `ml/` |
| Dataset download fails or "Checksum mismatch" | Check internet access; delete `ml/data/*_raw.csv` and retry; a mismatch means the source file changed |
| `no such table` | `alembic upgrade head` in `backend/` |
| Frontend shows "Cannot reach the server" | Start the backend; check `VITE_API_URL` and `CORS_ORIGINS` |
| 401 everywhere | Sign in again (tokens expire after 60 minutes) |
| 429 Too many requests | Wait a minute or raise `RATE_LIMIT_PER_MINUTE` |
| Image page says unavailable | Train and install an image model (`docs/IMAGE_MODULE.md`) and restart the backend |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

## Docker (written, not executed)
`docker compose up --build` after copying `.env.example` to `.env` and setting `SECRET_KEY` and `POSTGRES_PASSWORD`. Treat it as untested until you run it.
