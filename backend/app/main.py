"""FastAPI application entrypoint.

Responsibilities kept here on purpose:
- create the app and mount the versioned router
- attach a request-ID + access-log middleware
- translate domain exceptions (AppError) into HTTP responses in ONE place, so
  services never import FastAPI or set status codes themselves

Schema creation is NOT done here. Alembic migrations own the schema now (Stage
3). The temporary create_all shim from Stage 2 has been removed.
"""
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, request_id_ctx

settings = get_settings()
configure_logging(debug=settings.debug)
logger = logging.getLogger("app")

app = FastAPI(
    title=settings.app_name,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
)

# CORS is intentionally strict; the allowed origin is set per environment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = request.headers.get("x-request-id", str(uuid.uuid4()))
    request_id_ctx.set(rid)
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)
