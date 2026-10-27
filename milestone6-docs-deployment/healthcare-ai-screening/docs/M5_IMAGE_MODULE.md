# Milestone 5: image screening with transfer learning and Grad-CAM

## Honest status in one paragraph
The **code is complete and tested mechanically**: image validation, a transfer-learning training script, Grad-CAM, a safe upload endpoint, and the React page. **No medical image model has been trained or evaluated**, because the build environment had no image dataset, no pretrained weights and no GPU. So there are **no image results**, and the app says "image module not available" until you train and install a model. The tests use a synthetic toy dataset and prove that the code runs correctly; they say nothing about medical accuracy.

## What was built
| Piece | File | What it does |
|---|---|---|
| Safe loading | `ml/src/imaging/preprocess.py` | validates by **content** (decodes with Pillow; PNG/JPEG only; 5 MB, 32 to 4096 px sides, 25-megapixel bomb limit); ignores file names and declared types |
| Model | `ml/src/imaging/model.py` | ImageNet-pretrained ResNet18/50; only the last block (`layer4`) and the new head are trained |
| Training | `ml/src/imaging/train_image.py` | image folders by class; stratified 70/15/15 split; best epoch chosen on **validation** AUC; test set used **once**; writes `models/image_model.pt` and `evaluation/image_metrics.json` including a leakage limitation note |
| Grad-CAM | `ml/src/imaging/gradcam.py` | hook-based implementation of Selvaraju et al. (ICCV 2017): gradient-weighted sum of the last block's feature maps, ReLU, upsample, normalise |
| Inference | `ml/src/imaging/service.py` | validate, preprocess, score, Grad-CAM overlay as PNG; nothing written to disk |
| API | `backend/app/api/routes/images.py`, `services/image_service.py` | `POST /api/v1/images/screening`; the route **exists only if a trained model is installed**; stores a SHA-256 fingerprint, size and score, never pixels or file names; heat map is returned once |
| UI | `frontend/src/pages/ImageScreening.jsx`, `components/GradCamView.jsx` | client-side type/size checks, preview, score, original beside overlay, mandatory "attention, not proof" caption |
| Colab | `docs/colab_train_image.ipynb` | step-by-step GPU training notebook (**written, not executed**) |

## How to get a real model (about 15 minutes on Colab GPU)
1. Pick a dataset and check its licence. Recommended: NIH malaria cell images (Kaggle mirror, about 27,558 images). Layout: `ml/data/images/malaria/Parasitized/` and `.../Uninfected/`.
2. Open `docs/colab_train_image.ipynb` in Google Colab (Runtime > GPU) and run the cells, **or** locally: `pip install torch torchvision`, then
   `python src/imaging/train_image.py --data data/images/malaria --positive Parasitized --epochs 5 --dataset-desc "NIH malaria cell images (Kaggle mirror)"`
3. Copy `image_model.pt` to `ml/models/` and `image_metrics.json` to `ml/evaluation/`.
4. Restart the backend. `GET /health` shows `image_screening: available`; the React Image page becomes active.
5. `python scripts/make_results_md.py` adds the real image results to `docs/RESULTS.md`.

## Tests (32)
- **ML (15):** validation rejects empty, text, truncated, GIF-as-PNG, tiny, oversized and over-limit files; **Grad-CAM equals an independent `autograd.grad` reference computation**; works with a frozen backbone and stays in [0,1]; hooks are removed; training writes the checkpoint and metrics; splits do not overlap; inference returns score, flag and overlay.
- **Backend (13):** route absent without a model; listed as available with one; auth required; success stores only a fingerprint (no pixels, no file name); rejects invalid uploads (422) and oversize (413); path-traversal file names are harmless; 503 when the model disappears.
- **Frontend (4):** unavailable state offers no upload; wrong file type rejected before upload; valid upload shows score, overlay and caveat; server rejection shown.
- **Live run:** the frontend's API client uploaded a real PNG to the running server (toy model) and received a score and overlay; a non-image upload was rejected.

## What is NOT verified (say this if asked)
- Any medical accuracy: nothing trained on real images.
- Whether Grad-CAM **highlights the right region** for a real model: the tests verify the algorithm's arithmetic, not the localisation quality. Grad-CAM can highlight artefacts.
- The pretrained-weights path (`weights=imagenet` downloads from the internet on first use) and GPU training: not executed here.
- Inference speed on a typical laptop CPU; the Colab notebook.

## Viva-ready explanation
"Transfer learning reuses a network already trained on millions of everyday images and retrains only its last block and a new output layer for our two classes, which works when medical image sets are small. Grad-CAM takes the gradients flowing into the last convolutional block, averages them per channel to weight the feature maps, sums them and keeps the positive part, giving a coarse heat map of regions that increased the positive-class score. It shows where the model looked; it does not prove disease or that the model is right. In our project this module is implemented and tested for correctness, but a medical model has not been trained yet, so we claim no image results."

## Limitations to state in the report
No patient-level split in common public mirrors (inflated scores); coarse resolution of Grad-CAM; scores uncalibrated; single institution datasets; not clinically validated; synthetic-data tests only.
