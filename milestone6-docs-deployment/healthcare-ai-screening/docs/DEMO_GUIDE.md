# Live demo guide (about 6 to 8 minutes)

**Before the review (do this the evening before, on the laptop you will present from):**
1. Activate the venv; in `ml/` confirm the three models exist (`ml/models/*.joblib`). If not: `python src/train.py`, `python src/train_module.py diabetes`, `python src/train_module.py heart_disease`.
2. `cd backend; alembic upgrade head; uvicorn app.main:app --port 8000` (keep running). In another terminal `cd frontend; npm run dev`.
3. Register a demo user in the browser (e.g. `demo` / a throwaway password) and run one screening so history is not empty.
4. **Take screenshots** of the dashboard, a result page with the SHAP chart, and the metrics page, as a backup if the laptop fails. (The UI has never been visually inspected by the authors; look for layout problems now.)
5. Know your fallback: `cd ml; python src/predict.py --sample malignant --explain` works without the backend or browser.

## Script
| Step | You do | You say (simple English) | Expected on screen |
|---|---|---|---|
| 1. Landing | Open http://localhost:5173 | "This is a research prototype, not a medical device. It supports screening demonstrations." | Prototype and disclaimer text visible |
| 2. Sign in | Log in as the demo user | "Accounts keep each person's history private." | Dashboard with your earlier screening counted |
| 3. Choose module | Screening page | "Three modules are available because their models are trained; modules without a trained model are shown as unavailable, never as working." | Breast cancer, Diabetes, Heart disease available; Image screening marked not available unless you installed a model |
| 4. Breast cancer | Open it; click "Fill with a real example labelled positive in the dataset"; Run screening | "The form comes from the backend. This example is a real held-out row from the public dataset, not patient data." | Result page: score near 1.000, "Elevated screening score" |
| 5. Explain | Point at the SHAP chart and table | "These are the inputs that pushed the score up. Here: radius error, mean concave points, mean concavity. SHAP explains the model, not the cause of disease." | Three top features positive (raises score) |
| 6. Be honest | Open Diabetes; fill the positive example; run | "The model can disagree with the dataset label. This is why we report sensitivity: at the default threshold it misses almost half of diabetes cases." | Likely a lower score for this example (it scored 0.36 in our test run) |
| 7. Validation | In the form, enter age 5 and submit | "Input is validated in the browser and again on the server." | Error summary and inline message |
| 8. History | History page; open a record; (optionally delete one) | "Every record is stored per user; users can delete their own records." | Table with scores and flags |
| 9. Performance | Model performance page | "All numbers here are read from the evaluation files written by training. Test sets are small, so differences between models are noise." | Tables, confusion matrix, repeated-CV, high-sensitivity point |
| 10. Limits | About page | "Limitations are stated in the app itself." | Limitations list |

**If asked about images:** "The image pipeline with Grad-CAM is implemented and tested for correctness. A medical image model has not been trained yet, so the app says the module is unavailable and we claim no image results."

## API demo without the browser (PowerShell; written but not run on Windows)
```powershell
$B = "http://localhost:8000"
Invoke-RestMethod "$B/health"
Invoke-RestMethod "$B/api/v1/diseases" | Select-Object -ExpandProperty diseases | Select-Object id, status
Invoke-RestMethod -Method Post "$B/api/v1/auth/register" -ContentType "application/json" -Body '{"username":"apidemo","password":"demo-pass-123"}'
$t = (Invoke-RestMethod -Method Post "$B/api/v1/auth/login" -ContentType "application/json" -Body '{"username":"apidemo","password":"demo-pass-123"}').access_token
Invoke-RestMethod "$B/api/v1/models/metrics" | ConvertTo-Json -Depth 3 | Select-Object -First 30
```
Swagger UI at http://localhost:8000/docs lets you try every endpoint with the "Authorize" button.

## Things not to claim during the demo
Clinical validation; diagnosis; that the model beats the base paper; that scores are probabilities; that the image module works on medical images; that PostgreSQL or Docker deployment was tested.
