"""
FastAPI メインアプリケーション
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db, close_db
from app.error_handlers import register_exception_handlers
from app.routers import api, pages, auth

# ログ設定
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# アプリケーションのベースパス
BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # スタートアップ
    logger.info(f"Starting Machine Viz in {settings.app_env} mode")
    logger.info(f"Debug: {settings.app_debug}")
    logger.info(f"Using dummy data: {settings.use_dummy_data}")
    
    if not settings.use_dummy_data:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized")
    
    yield
    
    # シャットダウン
    if not settings.use_dummy_data:
        logger.info("Closing database connection...")
        await close_db()
        logger.info("Database connection closed")


# FastAPIアプリケーション
app = FastAPI(
    title="Machine Viz",
    description="機器情報可視化Webアプリケーション",
    version="0.1.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)

# エラーハンドラーの登録
register_exception_handlers(app)

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# テンプレート設定
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ルーターの登録
app.include_router(pages.router)
app.include_router(api.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

