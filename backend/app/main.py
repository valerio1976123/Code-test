from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.scheduler.service import scheduler_service


def create_app() -> FastAPI:
    app = FastAPI(title="Crazynet Device Backup", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    @app.on_event("startup")
    def _startup() -> None:
        scheduler_service.start()

    @app.on_event("shutdown")
    def _shutdown() -> None:
        scheduler_service.stop()

    return app


app = create_app()
