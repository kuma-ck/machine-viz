"""
データベース接続モジュール

SQLAlchemy 2.0 を使用して非同期データベース接続を管理。
開発環境ではSQLite、本番環境ではPostgreSQL/SQL Serverに対応。
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy ベースモデル"""
    pass


def get_database_url() -> str:
    """
    環境に応じたデータベースURLを取得
    
    SQLite: sqlite+aiosqlite:///./machine_viz.db
    PostgreSQL: postgresql+asyncpg://user:pass@host:port/db
    SQL Server: mssql+aioodbc://user:pass@host:port/db?driver=ODBC+Driver+18+for+SQL+Server
    """
    url = settings.database_url
    
    # 同期URLを非同期URLに変換
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://")
    elif url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    elif url.startswith("mssql://"):
        return url.replace("mssql://", "mssql+aioodbc://")
    
    return url


# 非同期エンジンの作成
engine = create_async_engine(
    get_database_url(),
    echo=settings.app_debug,  # デバッグ時はSQLをログ出力
    pool_pre_ping=True,  # 接続の有効性確認
)

# 非同期セッションファクトリー
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依存性注入用のデータベースセッション取得
    
    Usage:
        @router.get("/")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """データベースの初期化（テーブル作成）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """データベース接続のクローズ"""
    await engine.dispose()
