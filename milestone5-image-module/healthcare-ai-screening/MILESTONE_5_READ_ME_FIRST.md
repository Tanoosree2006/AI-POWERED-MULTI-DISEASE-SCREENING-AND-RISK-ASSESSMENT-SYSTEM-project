# Milestone 5 package: image screening (Grad-CAM + transfer learning)

Extract this zip **over** your project folder (it builds on M1 to M4). It adds the new image files and replaces the few
existing files that M5 changed (listed in docs/M5_IMAGE_MODULE.md and visible in this zip).

Read `docs/M5_IMAGE_MODULE.md` first. Key point: the code is complete and tested, but **no medical image model is trained yet**.
Train one with `docs/colab_train_image.ipynb` (GPU) or the command in the guide, then restart the backend.

Install for local image work: `pip install torch torchvision pillow` (see pytorch.org for the right command for your machine).
Tests: `cd ml && python -m pytest -q tests/test_image.py` (15), `cd backend && python -m pytest -q tests/test_images.py` (13).
