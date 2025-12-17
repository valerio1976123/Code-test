from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
def login(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/devices", response_class=HTMLResponse)
def devices(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("devices.html", {"request": request})


@router.get("/schedules", response_class=HTMLResponse)
def schedules(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("schedules.html", {"request": request})


@router.get("/history", response_class=HTMLResponse)
def history(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("history.html", {"request": request})
