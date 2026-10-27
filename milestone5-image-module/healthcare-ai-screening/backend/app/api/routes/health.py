from fastapi import APIRouter

from app.services import image_service, ml_service

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service health")
def health():
    models = {d: ml_service.model_status(d) for d in ml_service.supported_diseases()}
    models["image_screening"] = "available" if image_service.available() else "unavailable"
    return {"status": "ok", "models": models}
