"""
エラーハンドラー

グローバル例外ハンドラーとAPIエラーレスポンスを定義。
"""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.exceptions import AppException

logger = logging.getLogger(__name__)


class ErrorResponse:
    """統一されたエラーレスポンス"""
    
    @staticmethod
    def create(
        status_code: int,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        response = {
            "error": {
                "code": error_code,
                "message": message,
            }
        }
        if details:
            response["error"]["details"] = details
        if request_id:
            response["error"]["request_id"] = request_id
        return response


def register_exception_handlers(app: FastAPI) -> None:
    """例外ハンドラーをFastAPIアプリに登録"""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """アプリケーション例外のハンドラー"""
        logger.warning(
            f"AppException: {exc.error_code} - {exc.message}",
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "path": request.url.path,
                "details": exc.details,
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse.create(
                status_code=exc.status_code,
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details if settings.app_debug else None,
            ),
        )
    
    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
        """Pydanticバリデーションエラーのハンドラー"""
        logger.warning(
            f"Validation error: {exc.error_count()} errors",
            extra={"path": request.url.path}
        )
        
        # エラー詳細を整形
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        
        return JSONResponse(
            status_code=400,
            content=ErrorResponse.create(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message="入力値が不正です",
                details={"errors": errors} if settings.app_debug else None,
            ),
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """SQLAlchemy例外のハンドラー"""
        logger.error(
            f"Database error: {type(exc).__name__}",
            extra={
                "path": request.url.path,
                "error": str(exc),
            },
            exc_info=True,
        )
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse.create(
                status_code=500,
                error_code="DATABASE_ERROR",
                message="データベースエラーが発生しました",
                details={"type": type(exc).__name__} if settings.app_debug else None,
            ),
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """予期しない例外のハンドラー"""
        logger.error(
            f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
            extra={"path": request.url.path},
            exc_info=True,
        )
        
        # デバッグモードではスタックトレースを含める
        details = None
        if settings.app_debug:
            details = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse.create(
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="サーバーエラーが発生しました",
                details=details,
            ),
        )
