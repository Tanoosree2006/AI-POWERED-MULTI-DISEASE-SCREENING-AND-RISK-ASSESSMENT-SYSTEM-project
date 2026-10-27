from fastapi import APIRouter, HTTPException

from app.services import image_service, ml_service

router = APIRouter(tags=["diseases"])


@router.get("/diseases", summary="Disease modules and their input definitions")
def list_diseases():
    out = []
    for d in ml_service.supported_diseases():
        try:
            out.append(ml_service.disease_info(d))
        except ml_service.ModelUnavailableError:
            out.append(ml_service.disease_stub(d))  # shown as unavailable, never as a working feature
    out.append(image_service.info())  # "unavailable" until an image model has been trained and installed
    return {"diseases": out}


@router.get("/diseases/{disease}/examples", summary="Two real held-out rows from the public dataset for demos")
def examples(disease: str):
    if not ml_service.is_supported(disease):
        raise HTTPException(status_code=404, detail="Unsupported disease module")
    if ml_service.model_status(disease) != "available":
        raise HTTPException(status_code=503, detail="Model temporarily unavailable")
    return ml_service.example_records(disease)
