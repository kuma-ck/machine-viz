"""
ページルーティング
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """トップページ"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request):
    """機番検索ページ"""
    return templates.TemplateResponse("search.html", {"request": request})


@router.get("/timeseries", response_class=HTMLResponse)
async def timeseries(request: Request):
    """時系列表示ページ"""
    return templates.TemplateResponse("timeseries.html", {"request": request})


@router.get("/histogram", response_class=HTMLResponse)
async def histogram(request: Request):
    """断面データ表示ページ"""
    return templates.TemplateResponse("histogram.html", {"request": request})


@router.get("/table", response_class=HTMLResponse)
async def table(request: Request):
    """表形式表示ページ"""
    return templates.TemplateResponse("table.html", {"request": request})
