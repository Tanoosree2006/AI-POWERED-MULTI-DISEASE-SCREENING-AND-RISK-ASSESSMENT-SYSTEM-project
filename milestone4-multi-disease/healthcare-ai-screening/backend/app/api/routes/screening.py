from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user, rate_limit
from app.core.config import settings  # noqa: F401
from app.database import get_db
from app.models import ScreeningRecord, User
from app.schemas.screening import HistoryItem, HistoryPage, ScreeningRequest, ScreeningResponse
from app.services import crud, ml_service

router = APIRouter(prefix="/screening", tags=["screening"])
DISCLAIMER = ("Model-estimated screening score from a research prototype. NOT a diagnosis and not "
              "clinically validated. Consult a qualified clinician.")


def _response(rec: ScreeningRecord) -> ScreeningResponse:
    return ScreeningResponse(
        id=rec.id, disease=rec.disease_slug, model=rec.model_version.model_name,
        model_version=rec.model_version.version, screening_score=rec.screening_score, threshold=0.5,
        screening_flag=rec.screening_flag, warnings=rec.warnings or [], explanation=rec.explanation,
        disclaimer=DISCLAIMER, created_at=rec.created_at)


def _item(rec: ScreeningRecord) -> HistoryItem:
    return HistoryItem(id=rec.id, user_id=rec.user_id, disease=rec.disease_slug,
                       model=rec.model_version.model_name, model_version=rec.model_version.version,
                       screening_score=rec.screening_score, screening_flag=rec.screening_flag,
                       created_at=rec.created_at)


def _scope(scope: str, user: User) -> str:
    if scope == "all" and user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required for scope=all")
    return scope


@router.get("/history", response_model=HistoryPage, summary="Screening history of the signed-in user")
def history(disease: Optional[str] = None, scope: str = Query("own", pattern="^(own|all)$"),
            limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
            user: User = Depends(current_user), db: Session = Depends(get_db)):
    total, rows = crud.list_screenings(db, user, _scope(scope, user), disease, limit, offset)
    return HistoryPage(total=total, limit=limit, offset=offset, items=[_item(r) for r in rows])


@router.get("/record/{record_id}", response_model=ScreeningResponse)
def get_record(record_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rec = crud.get_screening(db, record_id, user)
    if rec is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return _response(rec)


@router.delete("/record/{record_id}", status_code=204, summary="Delete a stored screening record")
def delete_record(record_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rec = crud.get_screening(db, record_id, user)
    if rec is None:
        raise HTTPException(status_code=404, detail="Record not found")
    crud.delete_screening(db, rec)
    crud.add_audit(db, "screening_deleted", user.id, f"record {record_id}")


@router.post("/{disease}", response_model=ScreeningResponse, status_code=201,
             dependencies=[Depends(rate_limit)], summary="Run a structured-data screening")
def create_screening(disease: str, body: ScreeningRequest,
                     user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not ml_service.is_supported(disease):
        raise HTTPException(status_code=404, detail="Unsupported disease module")
    if disease == "image":
        raise HTTPException(status_code=404, detail="Use /api/v1/images/screening for image modules")
    try:
        result = ml_service.run_screening(disease, body.features)
    except ml_service.ScreeningInputError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ml_service.ModelUnavailableError:
        raise HTTPException(status_code=503, detail="Model temporarily unavailable")
    mv = crud.get_or_create_model_version(db, disease)
    rec = crud.create_screening(db, user, disease, mv, body.features, result)
    crud.add_audit(db, "screening_created", user.id, f"{disease} record {rec.id}")
    return _response(rec)
