from fastapi import APIRouter, HTTPException

from app.services import image_service, ml_service

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/metrics", summary="Model evaluation results produced by ml/src/train.py")
def metrics():
    out = {}
    for d in ml_service.supported_diseases():
        m = ml_service.load_metrics(d)
        if m:
            out[d] = m
    im = image_service.load_metrics()
    if im:
        out["image_screening"] = im
    if not out:
        raise HTTPException(status_code=404, detail="No evaluation results available. Run the training script.")
    return {"metrics": out}
