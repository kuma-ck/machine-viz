"""
アプリケーション設定モジュール

環境変数から設定を読み込み、アプリケーション全体で利用可能にする。
pydantic-settings を使用して型安全な設定管理を実現。
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # アプリケーション設定
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    
    # データベース設定
    database_url: str = "sqlite:///./machine_viz.db"
    
    # セキュリティ設定
    secret_key: str = "dev-secret-key"
    
    # ログ設定
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    
    # データソース設定
    use_dummy_data: bool = True  # Trueでダミーデータ、Falseでデータベースを使用
    
    @property
    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self.app_env == "production"
    



@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()


# モジュールレベルでアクセス可能な設定インスタンス
settings = get_settings()
