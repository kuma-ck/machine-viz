"""
Alembic マイグレーション環境設定

アプリケーションのモデルとデータベース設定を使用してマイグレーションを実行。
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# アプリケーションの設定とモデルをインポート
from app.config import settings
from app.database import Base, get_database_url
from app.models import *  # noqa: F401, F403 - モデルをインポートしてBaseに登録

# Alembic Config object
config = context.config

# ログ設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# モデルのメタデータを設定
target_metadata = Base.metadata


def get_url() -> str:
    """データベースURLを取得（同期版）"""
    url = settings.database_url
    # SQLite用の変換（同期版）
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://")
    return url


def run_migrations_offline() -> None:
    """オフラインモードでマイグレーションを実行"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """マイグレーションを実行"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """非同期マイグレーションを実行"""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """オンラインモードでマイグレーションを実行"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
