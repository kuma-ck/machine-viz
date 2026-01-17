"""
カスタム例外とエラーハンドリング

アプリケーション全体で使用する例外クラスとエラーレスポンスを定義。
"""

from typing import Any


class AppException(Exception):
    """アプリケーション基底例外"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """リソースが見つからない"""
    
    def __init__(self, message: str = "リソースが見つかりません", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class ValidationError(AppException):
    """入力値が不正"""
    
    def __init__(self, message: str = "入力値が不正です", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class DatabaseError(AppException):
    """データベースエラー"""
    
    def __init__(self, message: str = "データベースエラーが発生しました", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details,
        )


class AuthenticationError(AppException):
    """認証エラー"""
    
    def __init__(self, message: str = "認証に失敗しました", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationError(AppException):
    """認可エラー"""
    
    def __init__(self, message: str = "権限がありません", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )
