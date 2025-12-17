from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.scheduler.service import scheduler_service
from app.web.pages import router as web_router


def create_app() -> FastAPI:
    app = FastAPI(title="Crazynet Device Backup", version="0.1.0")
    backend_dir = Path(__file__).resolve().parents[1]

    app.add_middleware(
        CORSMiddleware,
        # UI is served by backend; keep CORS permissive for local dev tools.
        allow_origins=["http://localhost:5173", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_dir = backend_dir / "app" / "web" / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.include_router(web_router)
    app.include_router(api_router, prefix="/api")

    @app.on_event("startup")
    def _startup() -> None:
        scheduler_service.start()

    @app.on_event("shutdown")
    def _shutdown() -> None:
        scheduler_service.stop()

    return app


app = create_app()
