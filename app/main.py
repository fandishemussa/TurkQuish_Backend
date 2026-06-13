from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.routes import feedback, health, predict
from app.core.config import get_settings
from app.core.exceptions import TurkQuishError, generic_exception_handler, turkquish_exception_handler
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.db.database import init_db
from app.services.artifact_loader import artifacts
from app.services.transformer_service import url_transformer_service

settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    artifacts.load()
    url_transformer_service.load(artifacts.artifact_dir)
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="URL-only TurkQuish inference backend with optional URL-Transformer confidence fallback.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    RequestContextMiddleware,
    max_requests_per_minute=settings.rate_limit_requests_per_minute,
)

app.add_exception_handler(TurkQuishError, turkquish_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(predict.router, prefix=settings.api_prefix)
app.include_router(feedback.router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"name": settings.app_name, "status": "ok", "docs": "/docs"}

