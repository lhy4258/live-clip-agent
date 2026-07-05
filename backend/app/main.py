from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import chain_runs, clips, jobs, publish_plans, videos
from app.core.config import get_settings
from app.core.database import init_database
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(videos.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")
    app.include_router(clips.router, prefix="/api/v1")
    app.include_router(publish_plans.router, prefix="/api/v1")
    app.include_router(chain_runs.router, prefix="/api/v1")

    @app.on_event("startup")
    def startup() -> None:
        init_database()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
