"""Database operations. All queries are parameterised through SQLAlchemy."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditEvent, DiseaseModule, ModelVersion, ScreeningRecord, User
from app.services import image_service, ml_service


def get_user_by_username(db: Session, username: str):
    return db.scalar(select(User).where(User.username == username.lower()))


def create_user(db: Session, username: str, password_hash: str, role: str = "user") -> User:
    user = User(username=username.lower(), password_hash=password_hash, role=role)
    db.add(user)
    db.commit()
    return user


def add_audit(db: Session, event_type: str, user_id: int | None = None, detail: str = ""):
    db.add(AuditEvent(user_id=user_id, event_type=event_type, detail=detail[:200]))
    db.commit()


def get_or_create_model_version(db: Session, disease: str) -> ModelVersion:
    info = ml_service.disease_info(disease)
    if db.get(DiseaseModule, disease) is None:
        db.add(DiseaseModule(slug=disease, name=info["name"], data_type=info["data_type"]))
        db.commit()
    mv = db.scalar(select(ModelVersion).where(ModelVersion.disease_slug == disease,
                                              ModelVersion.version == info["model_version"]))
    if mv is None:
        metrics = ml_service.load_metrics(disease)
        selected = metrics["selected_model"] if metrics else None
        mv = ModelVersion(disease_slug=disease, model_name=info["model"], version=info["model_version"],
                          dataset=info["dataset"], metrics=metrics["test"][selected] if metrics else None)
        db.add(mv)
        db.commit()
    return mv


def create_screening(db: Session, user: User, disease: str, mv: ModelVersion, features: dict, result: dict):
    rec = ScreeningRecord(user_id=user.id, disease_slug=disease, model_version_id=mv.id,
                          input_features=features, screening_score=result["screening_score"],
                          screening_flag=result["screening_flag"], warnings=result["warnings"],
                          explanation=result.get("explanation"))
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def _scoped(user: User, scope: str):
    q = select(ScreeningRecord)
    if scope != "all":
        q = q.where(ScreeningRecord.user_id == user.id)
    return q


def list_screenings(db: Session, user: User, scope="own", disease=None, limit=20, offset=0):
    q = _scoped(user, scope)
    if disease:
        q = q.where(ScreeningRecord.disease_slug == disease)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.scalars(q.order_by(ScreeningRecord.created_at.desc(), ScreeningRecord.id.desc())
                      .limit(limit).offset(offset)).all()
    return total, rows


def get_screening(db: Session, record_id: int, user: User):
    rec = db.get(ScreeningRecord, record_id)
    if rec is None or (rec.user_id != user.id and user.role != "admin"):
        return None
    return rec


def delete_screening(db: Session, rec: ScreeningRecord):
    db.delete(rec)
    db.commit()


def get_or_create_image_model_version(db: Session) -> ModelVersion:
    info = image_service.info()
    if db.get(DiseaseModule, "image_screening") is None:
        db.add(DiseaseModule(slug="image_screening", name=info["name"], data_type="image"))
        db.commit()
    mv = db.scalar(select(ModelVersion).where(ModelVersion.disease_slug == "image_screening",
                                              ModelVersion.version == info["model_version"]))
    if mv is None:
        m = image_service.load_metrics()
        mv = ModelVersion(disease_slug="image_screening", model_name=info["model"], version=info["model_version"],
                          dataset=info["dataset"], metrics=m["test"] if m else None)
        db.add(mv)
        db.commit()
    return mv
