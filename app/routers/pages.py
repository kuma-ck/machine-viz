"""
ページルーティング

認証が必要なページは認証チェックを行い、未ログインの場合はログインページにリダイレクト。
"""

from fastapi import APIRouter, Cookie, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional

from app.auth.service import auth_service
from app.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter(tags=["pages"])


async def check_auth(session_token: Optional[str] = Cookie(default=None)) -> bool:
    """認証状態をチェック"""
    if not session_token:
        return False
    user_id = auth_service.verify_session_token(session_token)
    return user_id is not None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, session_token: Optional[str] = Cookie(default=None)):
    """ログインページ"""
    # 既にログイン済みの場合はトップページにリダイレクト
    if session_token and auth_service.verify_session_token(session_token):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, is_authenticated: bool = Depends(check_auth)):
    """トップページ"""
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, is_authenticated: bool = Depends(check_auth)):
    """機番検索ページ"""
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("search.html", {"request": request})


@router.get("/timeseries", response_class=HTMLResponse)
async def timeseries(request: Request, is_authenticated: bool = Depends(check_auth)):
    """時系列表示ページ"""
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("timeseries.html", {"request": request})


@router.get("/histogram", response_class=HTMLResponse)
async def histogram(request: Request, is_authenticated: bool = Depends(check_auth)):
    """断面データ表示ページ"""
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("histogram.html", {"request": request})


@router.get("/table", response_class=HTMLResponse)
async def table(request: Request, is_authenticated: bool = Depends(check_auth)):
    """表形式表示ページ"""
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("table.html", {"request": request})

