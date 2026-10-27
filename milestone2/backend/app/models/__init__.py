"""SQLAlchemy models. Only data needed by the application is stored."""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DiseaseModule(Base):
    __tablename__ = "disease_modules"
    slug: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    data_type: Mapped[str] = mapped_column(String(20))


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("disease_slug", "version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    disease_slug: Mapped[str] = mapped_column(ForeignKey("disease_modules.slug"))
    model_name: Mapped[str] = mapped_column(String(60))
    version: Mapped[str] = mapped_column(String(40))
    dataset: Mapped[str] = mapped_column(String(200))
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ScreeningRecord(Base):
    __tablename__ = "screening_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    disease_slug: Mapped[str] = mapped_column(ForeignKey("disease_modules.slug"), index=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"))
    input_features: Mapped[dict] = mapped_column(JSON)
    screening_score: Mapped[float] = mapped_column(Float)
    screening_flag: Mapped[str] = mapped_column(String(20))
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    model_version: Mapped[ModelVersion] = relationship(lazy="joined")


class AuditEvent(Base):
    """Security-relevant events. Never contains patient inputs."""
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    detail: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
