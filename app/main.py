"""
FastAPI メインアプリケーション
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import api, pages

# アプリケーションのベースパス
BASE_DIR = Path(__file__).resolve().parent

# FastAPIアプリケーション
app = FastAPI(
    title="Machine Viz",
    description="機器情報可視化Webアプリケーション",
    version="0.1.0",
)

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# テンプレート設定
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ルーターの登録
app.include_router(pages.router)
app.include_router(api.router, prefix="/api")
