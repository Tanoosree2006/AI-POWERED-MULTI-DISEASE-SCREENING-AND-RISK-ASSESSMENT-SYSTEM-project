import hashlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import current_user, rate_limit
from app.api.routes.screening import DISCLAIMER
from app.database import get_db
from app.models import User
from app.schemas.screening import ImageScreeningResponse
from app.services import crud, image_service

router = APIRouter(prefix="/images", tags=["images"])
MAX_BYTES = 5 * 1024 * 1024


@router.post("/screening", response_model=ImageScreeningResponse, status_code=201, dependencies=[Depends(rate_limit)],
             summary="Screen a PNG/JPEG image (validated by content; the image itself is never stored)")
def screen_image(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    data = file.file.read(MAX_BYTES + 1)             # never read more than the limit + 1 byte
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image larger than 5 MB")
    try:
        result = image_service.screen(data)
    except image_service.ImageInputError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except image_service.ImageModelUnavailableError:
        raise HTTPException(status_code=503, detail="Image model temporarily unavailable")
    mv = crud.get_or_create_image_model_version(db)
    stored_input = {"type": "image", "width": result["image"]["width"], "height": result["image"]["height"],
                    "sha256": hashlib.sha256(data).hexdigest()}            # a fingerprint only; no pixels, no filename
    stored_expl = {"method": "grad-cam", "note": "Heat map is generated on request and is not stored."}
    rec = crud.create_screening(db, user, "image_screening", mv, stored_input,
                                {**result, "explanation": stored_expl})
    crud.add_audit(db, "image_screening_created", user.id, f"record {rec.id}")
    return ImageScreeningResponse(
        id=rec.id, disease="image_screening", model=result["model"], model_version=mv.version,
        screening_score=result["screening_score"], threshold=result["threshold"],
        screening_flag=result["screening_flag"], warnings=result["warnings"], explanation=stored_expl,
        disclaimer=DISCLAIMER, created_at=rec.created_at, gradcam=result.get("gradcam"), image=result["image"])
