from fastapi import APIRouter

from app.api.routes import auth, dashboard, diseases, models, screening

api_router = APIRouter()
for r in (diseases.router, auth.router, screening.router, dashboard.router, models.router):
    api_router.include_router(r)
