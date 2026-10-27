"""FastAPI application factory."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.api.routes import health
from app.core.config import settings

log = logging.getLogger("screening")


def _error(status: int, message: str, details=None, headers=None):
    body = {"error": {"code": status, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body, headers=headers)


def create_app() -> FastAPI:
    settings.validate_for_environment()
    app = FastAPI(
        title=settings.app_name, version="1.0.0",
        description="Research prototype for explainable healthcare screening. Outputs are model-estimated "
                    "screening scores, not diagnoses, and are not clinically validated.")
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=False,
                       allow_methods=["GET", "POST", "DELETE"], allow_headers=["Authorization", "Content-Type"])

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        return _error(exc.status_code, str(exc.detail), headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Report field and message only; never echo submitted values back.
        details = [{"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
                   for e in exc.errors()]
        return _error(422, "Invalid request", details)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        log.error("Unhandled error on %s %s: %s", request.method, request.url.path, type(exc).__name__)
        return _error(500, "Internal server error")

    app.include_router(health.router)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
