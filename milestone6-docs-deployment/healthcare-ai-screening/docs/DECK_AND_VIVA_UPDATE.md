# Update your slides and viva answers: the project has moved on

Your review deck (12-10-2026) and the "Review Presentation Pack" were written when only Milestone 1 existed. Several statements are now out of date. Use this list before any later review or viva. **Say only what you have run on your own machine.**

## Slides that need changing
| Slide | Old statement | New, accurate statement |
|---|---|---|
| 3 (abstract) | inputs: demographics, symptoms, vitals, labs, history, lifestyle | Now partly true: the diabetes and heart modules use clinical measurements (age, blood pressure, glucose, cholesterol...). Symptoms and lifestyle are not inputs. Do not claim them. |
| 7 (solution) | FastAPI, PostgreSQL, React dashboard, image module are dashed/planned | FastAPI + SQLAlchemy + Alembic (SQLite verified), React dashboard (tested, not visually inspected) and the image pipeline (code tested, **no trained medical model**) are implemented. PostgreSQL and Docker are configured but **not executed**. |
| 9 (modules) | 1 of 6 milestones complete | M1 to M4 complete; M5 code complete but no trained model; M6 documentation complete. Deployment untested. |
| 11 to 13 (results) | breast cancer only | add Diabetes (sensitivity 0.537, specificity 0.850, AUC 0.814) and Heart disease (0.714, 0.939, 0.917); see `docs/RESULTS.md` |
| 16 (tests) | 26 / 26 tests | 151 tests (50 ML, 53 backend, 48 frontend) plus a live integration run; frontend and backend image tests use synthetic data |
| 17 (conclusion) | Outcome 2 planned | Outcome 2 (history, dashboard, trends) implemented with SQLite; Objective 1 partly met (3 tabular modules; image model not trained); Objective 2 met for SHAP, Grad-CAM implemented but untrained |

## Corrected answers to the big questions
- **Which features are implemented?** Three tested tabular modules with SHAP; an authenticated API with stored history; a React dashboard; image-screening code with Grad-CAM. **Not done:** a trained medical image model, PostgreSQL/Docker execution, visual browser check, external validation.
- **What is unique versus the base paper?** Richer evaluation (sensitivity, specificity, AUC, calibration, repeated CV, a high-sensitivity operating point), SHAP explanations in a working app, and stored history and trends. Grad-CAM is implemented but has no trained model. None of the techniques is new; the contribution is careful, tested integration. We cannot claim higher accuracy than the base paper.
- **Comparison with the base paper's numbers:** the paper reports accuracy 0.82 (diabetes) and 0.88 (heart) for Random Forest; our leakage-safe test accuracies are 0.74 and 0.84 on different splits and dataset copies. Say: "These are not comparable, and I cannot tell what explains the difference; I make no claim either way."

## New viva questions (with answers)
1. **Why is diabetes sensitivity only 0.54 at the default threshold?** Diabetes in this dataset is hard to separate (AUC 0.81) and positives are a minority (35%). A validation-chosen threshold of 0.275 raises test sensitivity to 0.85 but cuts specificity to 0.62; choosing that trade-off is a clinical decision.
2. **What was wrong with the heart dataset?** The public file labels 1 as "no disease". We verified the direction from the data (patients coded 0 have lower maximum heart rate and more exercise angina), re-coded it, removed one duplicate and treated invalid codes as missing. A test fails if the direction check fails.
3. **Why impute inside the pipeline?** Medians are learned from training rows only; imputing on the whole dataset would leak test information. Tests check the stored medians equal the training medians.
4. **Why were Pima zeros treated as missing?** A glucose or blood pressure of zero is impossible; zeros there mean "not measured".
5. **How do you know your Grad-CAM implementation is correct?** A test compares it with an independent gradient computation of the same formula. That checks the arithmetic, not whether real heat maps highlight the right anatomy.
6. **Does the image module work?** The pipeline works mechanically. We have not trained a medical model, so we report no image performance.
7. **Is PostgreSQL used?** The code supports it through SQLAlchemy and Alembic, and a compose file exists, but we ran everything on SQLite and have not executed PostgreSQL or Docker.
8. **How is a user's data protected?** Hashed passwords, expiring tokens, per-user isolation, strict validation, no stack traces in errors, no patient inputs in audit logs, user-controlled deletion, uploaded images never stored. Missing: HTTPS, token revocation, formal compliance. Only public data should be entered.
9. **Why does the API reject extra or text values?** To avoid silent mistakes: unknown fields, strings and booleans are rejected rather than coerced.
10. **Why is the test set not used to choose the model, yet the chosen model is not the best on it (heart)?** Selection is on the validation set by design; with 61 test patients, small differences are noise. Changing the choice after seeing test results would make the test estimate optimistic.

## Fixing the Claude document
The "Review Presentation Pack" document still lists FastAPI, the database and the dashboard as planned (Part 0.4, Part 5 status tables, Part 7). Ask for an updated version once you have decided which parts you ran yourself.
