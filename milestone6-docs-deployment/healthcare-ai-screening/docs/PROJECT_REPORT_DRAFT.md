# AI-Powered Multi-Disease Screening and Risk Assessment System
*An Explainable AI-Based Healthcare Screening and Clinical Decision-Support Platform*
Aditya University, Department of CSE, 2026-27. Draft built from executed results; replace bracketed items with your own text.

## Abstract
Healthcare AI tools are often limited to one disease or one data type, report only accuracy and do not explain predictions. We built a modular research prototype that serves three structured-data screening modules (breast cancer, diabetes, heart disease) behind one authenticated web application with SHAP explanations, stored screening history and a dashboard, plus an image-screening pipeline (transfer learning with Grad-CAM) whose code is implemented but not yet trained on medical images. Each tabular module follows a leakage-safe protocol (stratified 60/20/20 split, preprocessing inside the pipeline, cross-validated tuning, selection on validation data, a single test evaluation) and reports sensitivity, specificity, ROC-AUC and calibration, not accuracy alone. On held-out test sets the selected models reached ROC-AUC 0.995 (breast cancer, 114 samples), 0.814 (diabetes, 154) and 0.917 (heart disease, 61). The system is a screening-support prototype; it is not clinically validated and does not diagnose.

## 1. Introduction and motivation
Late or missed diagnosis harms patients, and published multi-disease systems tend to stop at accuracy figures. A clinician needs to know how often a tool misses disease, why it produced a score, and how reliable that score is.

## 2. Problem statement and objectives
Problem: healthcare AI is fragmented across diseases and data types and rarely explains itself. Objective 1: a unified platform integrating disease-specific ML and DL models for structured data and images. Objective 2: interpretable results (SHAP, Grad-CAM) with history and trends on a dashboard.

## 3. Literature review and base paper
Base paper: F. Din, A. U. Haq, M. Yaseen, A. Khan and A. Ali, "Multi-disease prediction using machine learning and deep learning models," Kashf J. Multidiscip. Res., vol. 1, no. 12, pp. 301-312, 2024, doi 10.71146/kjmr176. It trains Random Forest, XGBoost and a feed-forward network on five Kaggle tabular datasets and VGG16/ResNet50 on three image datasets, and reports accuracy only. We found no explanation method, history or trend feature, and no calibration or sensitivity/specificity reporting in its text. Explainability foundations: S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," NIPS 2017, pp. 4765-4774; R. R. Selvaraju et al., "Grad-CAM: Visual explanations from deep networks via gradient-based localization," ICCV 2017. [Add the further related studies you read in full.]

## 4. System architecture
See `docs/ARCHITECTURE.md` (diagram, data flow, training versus prediction pipelines, security controls).

## 5. Datasets and preprocessing
| Module | Source | Rows | Notes |
|---|---|---|---|
| Breast cancer | UCI WDBC (id 17, CC BY 4.0) | 569 | 30 numeric features, 37% malignant |
| Diabetes | Pima Indians Diabetes Database (NIDDK), GitHub copy, SHA-256 verified | 768 | 34.9% positive; physiologically impossible zeros (e.g. 374 insulin, 227 skin-thickness) treated as missing and imputed with training medians |
| Heart disease | UCI Cleveland, GitHub copy, SHA-256 verified | 302 (1 duplicate removed) | the public file's label is inverted (1 = no disease); verified from the data (patients coded 0 have lower maximum heart rate and more exercise angina) and re-coded; invalid codes (ca = 4, thal = 0) treated as missing |
Licences of the GitHub copies should be confirmed before redistribution; the repository does not ship them.

## 6. Methodology
Logistic Regression, Random Forest and XGBoost; stratified 60/20/20 split (seed 42); imputation and scaling inside scikit-learn pipelines; grid search with 5-fold stratified CV on the training set (ROC-AUC); model chosen on the validation set; one test evaluation; for the small datasets also 3x repeated 5-fold CV on train+validation and a high-sensitivity operating point chosen on validation data. SHAP: linear explainer for Logistic Regression, tree explainer for Random Forest and XGBoost; additivity is unit-tested.

## 7. Results
Full tables: `docs/RESULTS.md` (generated from the evaluation files). Highlights (threshold 0.5): 
- **Breast cancer** (selected: Logistic Regression): accuracy 0.974, sensitivity 0.952 (40/42), specificity 0.986 (71/72), ROC-AUC 0.995.
- **Diabetes** (selected: Random Forest): accuracy 0.740, sensitivity 0.537, specificity 0.850, ROC-AUC 0.814; repeated-CV ROC-AUC 0.83-0.84. At a validation-chosen threshold of 0.275, test sensitivity rises to 0.852 and specificity falls to 0.620.
- **Heart disease** (selected: Random Forest): accuracy 0.836, sensitivity 0.714, specificity 0.939, ROC-AUC 0.917 on only 61 test patients; repeated-CV ROC-AUC 0.89-0.91.
- **Image module**: no medical image model trained; no results claimed.

## 8. Discussion
Breast cancer is almost linearly separable, so near-ceiling scores are expected and optimistic. Diabetes is harder: at the default threshold the selected model misses nearly half of positives, which is why we report the threshold trade-off. Test sets are small (42, 54 and 28 positives), so differences between models are within noise and no model is declared best. Comparison with the base paper is not valid: it reports accuracy on different splits and may use different dataset versions (for example, 0.82 diabetes and 0.88 heart accuracy for Random Forest, against 0.74 and 0.84 here under a leakage-safe protocol); we could not determine the cause of the differences and make no claim either way.

## 9. Limitations and ethics
Small single-source datasets; no external validation; uncalibrated scores (not probabilities); SHAP explains the model, not the disease, and correlated features share credit; ordinal coding of nominal heart-disease variables; Pima data cover one population; no patient-level split for images; not clinically validated or regulated; only public de-identified data may be used; no claim that the system can replace clinicians.

## 10. Conclusion and future scope
Implemented: three tested tabular modules with explanations, an authenticated API with history, a React dashboard, and an image pipeline awaiting training. Future work: train and evaluate the image model with a patient-level split, external validation, probability calibration, threshold selection with clinicians, further disease modules, deployment hardening (HTTPS, token revocation, distributed rate limiting).

## References
[1] Din et al. 2024 (above). [2] Lundberg and Lee 2017. [3] Selvaraju et al. 2017. [4] UCI Machine Learning Repository, Breast Cancer Wisconsin (Diagnostic), dataset 17. [5] Smith et al. 1988, Pima Indians diabetes (verify citation details). [6] Detrano et al. 1989, UCI heart disease (verify citation details). [Add only papers you have actually read.]
