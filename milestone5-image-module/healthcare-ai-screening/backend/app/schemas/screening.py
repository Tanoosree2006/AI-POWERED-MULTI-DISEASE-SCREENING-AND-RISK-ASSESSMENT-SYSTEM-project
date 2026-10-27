from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt

Number = Union[StrictInt, StrictFloat]  # strict: rejects strings and booleans


def _example(schema: dict) -> None:
    from app.services import ml_service
    try:
        schema["example"] = {"features": ml_service.example_record()}
    except Exception:  # documentation only; never break schema generation
        pass


class ScreeningRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra=_example)
    features: Dict[str, Optional[Number]] = Field(
        ..., min_length=1,
        description="All feature values for the disease module, keyed by the exact feature names "
                    "returned by GET /api/v1/diseases. Numbers only; no patient identifiers.")


class ScreeningResponse(BaseModel):
    id: int
    disease: str
    model: str
    model_version: str
    screening_score: float
    threshold: float
    screening_flag: str
    warnings: List[str]
    explanation: Optional[Dict[str, Any]] = None
    disclaimer: str
    created_at: datetime


class ImageScreeningResponse(ScreeningResponse):
    gradcam: Optional[Dict[str, Any]] = None   # overlay is returned once and is NOT stored
    image: Optional[Dict[str, int]] = None


class HistoryItem(BaseModel):
    id: int
    user_id: int
    disease: str
    model: str
    model_version: str
    screening_score: float
    screening_flag: str
    created_at: datetime


class HistoryPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[HistoryItem]


class TrendPoint(BaseModel):
    date: str
    count: int
    flagged: int
    mean_score: float


class DashboardSummary(BaseModel):
    scope: str
    window_days: int
    total_screenings: int
    flagged_elevated: int
    flagged_lower: int
    mean_score: Optional[float]
    by_disease: Dict[str, int]
    trend: List[TrendPoint]
    recent: List[HistoryItem]
    note: str
