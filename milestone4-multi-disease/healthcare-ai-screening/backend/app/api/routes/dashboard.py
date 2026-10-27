from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.api.routes.screening import _item
from app.database import get_db
from app.models import ScreeningRecord, User
from app.schemas.screening import DashboardSummary, TrendPoint

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Summary computed from stored records")
def summary(days: int = Query(90, ge=1, le=365), scope: str = Query("own", pattern="^(own|all)$"),
            user: User = Depends(current_user), db: Session = Depends(get_db)):
    if scope == "all" and user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required for scope=all")
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = select(ScreeningRecord).where(ScreeningRecord.created_at >= since.replace(tzinfo=None)
                                      if db.bind.dialect.name == "sqlite" else ScreeningRecord.created_at >= since)
    if scope != "all":
        q = q.where(ScreeningRecord.user_id == user.id)
    rows = db.scalars(q.order_by(ScreeningRecord.created_at.desc(), ScreeningRecord.id.desc())).all()

    by_day, by_disease = defaultdict(list), defaultdict(int)
    for r in rows:
        by_day[r.created_at.date().isoformat()].append(r)
        by_disease[r.disease_slug] += 1
    trend = [TrendPoint(date=d, count=len(rs), flagged=sum(x.screening_flag == "elevated" for x in rs),
                        mean_score=round(sum(x.screening_score for x in rs) / len(rs), 4))
             for d, rs in sorted(by_day.items())]
    flagged = sum(r.screening_flag == "elevated" for r in rows)
    return DashboardSummary(
        scope=scope, window_days=days, total_screenings=len(rows), flagged_elevated=flagged,
        flagged_lower=len(rows) - flagged,
        mean_score=round(sum(r.screening_score for r in rows) / len(rows), 4) if rows else None,
        by_disease=dict(by_disease), trend=trend, recent=[_item(r) for r in rows[:5]],
        note="Counts are model-flagged screening scores, not confirmed diagnoses.")
