# Testing guide

## Run everything
```powershell
powershell -File scripts\run_all_tests.ps1
```
or run the suites separately:
| Suite | Command | Tests | What it covers |
|---|---|---|---|
| ML | `cd ml; python -m pytest -q` | 50 | data validation, split integrity, leakage (scaler/imputer fitted on training rows), metric correctness, saved-model reload, input validation, CLI codes, SHAP additivity for LR/RF/XGBoost, dataset loaders (label direction, zeros as missing, checksum), image validation, Grad-CAM vs reference, image training mechanics |
| Backend | `cd backend; python -m pytest -q` | 53 | auth, token tampering, role/isolation, all three modules, validation and error envelope, no value echo, pagination, dashboard, metrics, rate limit, hidden 500 details, CORS, migration, image endpoint (toy model) |
| Frontend | `cd frontend; npm test` | 48 | validators, API client (auth header, errors, 401, multipart), routing guard, forms, results, history, dashboard, metrics, image page |
| Build | `cd frontend; npm run build` | n/a | production bundle compiles |
| Live integration | start the backend, then `node frontend/scripts/integration.mjs http://127.0.0.1:8000` | 20 checks (22 with an image model) | the real API client against the real server |

Expected: every suite passes. The first ML/backend run trains missing models automatically (breast cancer) or downloads the two datasets (needs internet). The backend suite takes about 35 to 80 seconds; the image tests train a tiny synthetic model.

## What the tests prove, and what they do not
They prove the code behaves as designed. They do **not** prove medical accuracy, fairness, calibration, performance on other populations, or that the image heat maps highlight real lesions. Sanity floors in the model tests (AUC above 0.95 for breast cancer) are smoke checks, not clinical claims. Image tests use synthetic data.

## Manual browser checklist (never performed by the authors; do this before the review)
- [ ] Landing, login, register, dashboard, module list, form, result, history, metrics, about all render without overlapping text
- [ ] Resize to a phone width (about 375 px): navigation wraps, tables scroll, form is one column
- [ ] Keyboard only: Tab reaches every control, focus is visible, Enter submits forms
- [ ] Submit an empty form: error summary appears and the first error is announced
- [ ] Stop the backend: pages show "Cannot reach the server" instead of a blank screen
- [ ] Sign out: protected pages redirect to sign in
- [ ] Zoom to 200%: layout remains usable
- [ ] Charts show tooltips; the tables beside them contain the same numbers

## Reporting a failure
Copy the exact terminal output (the last 30 lines) and the command you ran. Do not paste secrets from `.env`.
