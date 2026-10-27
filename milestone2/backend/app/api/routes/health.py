from fastapi import APIRouter

from app.services import ml_service

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service health")
def health():
    return {"status": "ok", "models": {d: ml_service.model_status(d) for d in ml_service.SUPPORTED_DISEASES}}
