# Image module: how to train and install a real model

**Status:** the code is implemented and its mechanics are tested (validation, Grad-CAM against an independent reference, training script, API upload) using a synthetic toy dataset. **No medical image model has been trained or evaluated.** No image results are claimed anywhere in this project.

## Recommended dataset
NIH malaria cell images (Rajaraman et al., 2018), widely mirrored on Kaggle as "Cell Images for Detecting Malaria" (about 27,558 images, two classes `Parasitized` and `Uninfected`; the base paper also uses a malaria image set). **Check the licence on the page you download from and accept its terms.** Other two-class image folders (for example a chest X-ray pneumonia set) work too.
Caveat for your report: these mirrors do not provide patient IDs, so a random split can put cells from one patient in both train and test (patient-level leakage). Report it as a limitation.

## Train (needs internet once to download ImageNet weights; a GPU or Google Colab is strongly recommended)
```powershell
cd ml
# place images as data/images/malaria/Parasitized/*.png and data/images/malaria/Uninfected/*.png
pip install torch torchvision          # see pytorch.org for the right command for your machine
python src/imaging/train_image.py --data data/images/malaria --positive Parasitized --epochs 5 --dataset-desc "NIH malaria cell images (Kaggle mirror)"
```
Quick CPU trial: add `--max-per-class 500 --image-size 128`.
Outputs: `models/image_model.pt` and `evaluation/image_metrics.json` (test set used once; model chosen on validation AUC).

## Install into the API
Restart the backend (`uvicorn app.main:app`). `/health` and `/api/v1/diseases` then report `image_screening` as available and `POST /api/v1/images/screening` appears. The React "Image" page becomes active automatically.

## Google Colab outline
1. Runtime > GPU. 2. Upload the repository `ml` folder and the dataset. 3. `pip install -r ml/requirements.txt torch torchvision`. 4. Run the training command. 5. Download `models/image_model.pt` and `evaluation/image_metrics.json` into your local `ml/` folders.

## What to say about Grad-CAM
It shows where the network looked for the positive class. It does not prove disease, and it can highlight artefacts (stain marks, borders, text). Always label it "attention, not proof".
