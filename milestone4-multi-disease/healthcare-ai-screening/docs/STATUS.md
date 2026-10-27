# Implementation status (honest)

| Area | Implemented | Verified how |
|---|---|---|
| ML core: breast cancer, diabetes, heart disease | yes | 50 ML tests; training runs; metrics in `docs/RESULTS.md` |
| Leakage control, CV, validation-based selection | yes | tests check imputer medians and scaler means come from training rows only |
| SHAP (LR, RF, XGBoost) | yes | tests check base value + sum(SHAP) equals the model output for each model type |
| FastAPI, auth, roles, rate limit, audit | yes | 53 backend tests + live HTTP run |
| Database + Alembic migration | yes (SQLite verified) | migration up/down/up; persistence across restart |
| React app (12 pages) | yes | 48 component/unit tests, production build, live API-client run against the real backend |
| Image module code (training, Grad-CAM, upload API, UI page) | yes | mechanics tested on a **synthetic toy model only** |
| **Trained medical image model** | **no** | needs a dataset download and GPU/Colab (see `docs/IMAGE_MODULE.md`) |
| PostgreSQL | configured | **not executed** (no Docker/Postgres in the build environment) |
| Docker Compose (db, backend, frontend) | written | **not executed** |
| Windows setup commands | written | **not executed on Windows** |
| Browser visual check of the UI | no | no browser was available; layout was not visually inspected |
| External validation, clinical validation | no | out of scope; not claimed |
| LLM / RAG module | no | optional; deliberately left out |

Unverified items must be tested on your own machine before you describe them as working.
