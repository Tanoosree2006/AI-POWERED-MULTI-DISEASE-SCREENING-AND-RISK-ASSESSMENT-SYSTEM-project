# Submission checklist

**Verify yourself (the authors could not):**
- [ ] Follow README setup on **your Windows machine** from a fresh clone; note every error
- [ ] Run `scripts\run_all_tests.ps1`; all suites pass (expect 50, 53, 48 tests)
- [ ] Open the app in a browser and complete the manual checklist in `docs/TESTING.md`
- [ ] Take screenshots (dashboard, result with SHAP, history, metrics) for the report
- [ ] Optional: `docker compose up --build` (untested) and PostgreSQL
- [ ] Optional: train the image model (`docs/colab_train_image.ipynb`), regenerate `docs/RESULTS.md`

**Content checks:**
- [ ] `docs/PROJECT_REPORT_DRAFT.md`: replace bracketed text, add references you have actually read, insert screenshots
- [ ] Author order of the base-paper citation checked on the journal page
- [ ] Number of papers reviewed in the literature survey form is the true number
- [ ] Slides and viva answers updated using `docs/DECK_AND_VIVA_UPDATE.md`
- [ ] Each team member can explain: the data-leakage controls, why accuracy is insufficient, what SHAP and Grad-CAM show and do not show, and what is not done

**Safety and licences:**
- [ ] No real patient data anywhere; the app only ever shows public research data
- [ ] Dataset licences confirmed (the CSV files are downloaded by the scripts, not redistributed)
- [ ] `.env` and databases are not in the zip or on GitHub; `SECRET_KEY` is random
- [ ] The disclaimer is visible in the app and in the report
- [ ] No claim of clinical validation, regulatory approval, hospital integration or superiority over the base paper
