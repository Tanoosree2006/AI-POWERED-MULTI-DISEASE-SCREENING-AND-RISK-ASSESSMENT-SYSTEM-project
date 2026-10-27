from fastapi import APIRouter

from app.services import ml_service

router = APIRouter(tags=["diseases"])


@router.get("/diseases", summary="Supported disease modules (only working modules are listed)")
def list_diseases():
    out = []
    for d in ml_service.SUPPORTED_DISEASES:
        try:
            out.append(ml_service.disease_info(d))
        except ml_service.ModelUnavailableError:
            m = ml_service.SUPPORTED_DISEASES[d]
            out.append({"id": d, "name": m["name"], "data_type": m["data_type"], "status": "unavailable"})
    return {"diseases": out}
