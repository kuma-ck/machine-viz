"""
データリポジトリ

データベースからデータを取得する関数群。
dummy.py と同じインターフェースを提供し、切り替え可能にする。
"""

from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Series,
    Model,
    Machine,
    Category,
    Characteristic,
    Aggregation,
    MachineData,
    Annotation,
)


async def get_series(session: AsyncSession) -> list[str]:
    """シリーズ一覧を取得"""
    result = await session.execute(select(Series.id).order_by(Series.id))
    return list(result.scalars().all())


async def get_models(session: AsyncSession, series: str) -> list[str]:
    """指定シリーズの機種番号一覧を取得"""
    result = await session.execute(
        select(Model.id).where(Model.series_id == series).order_by(Model.id)
    )
    return list(result.scalars().all())


async def get_categories(session: AsyncSession) -> list[str]:
    """カテゴリー一覧を取得"""
    result = await session.execute(select(Category.id).order_by(Category.id))
    return list(result.scalars().all())


async def get_characteristics(session: AsyncSession, category: str) -> list[str]:
    """指定カテゴリーの特性値ID一覧を取得"""
    result = await session.execute(
        select(Characteristic.name)
        .where(Characteristic.category_id == category)
        .order_by(Characteristic.name)
    )
    return list(result.scalars().all())


async def get_aggregations(session: AsyncSession) -> list[str]:
    """集計方法一覧を取得"""
    result = await session.execute(select(Aggregation.id).order_by(Aggregation.id))
    return list(result.scalars().all())


async def get_months(session: AsyncSession) -> list[str]:
    """利用可能な月一覧を取得"""
    result = await session.execute(
        select(Machine.manufacture_month)
        .distinct()
        .order_by(Machine.manufacture_month.desc())
    )
    return list(result.scalars().all())


async def search_machines(
    session: AsyncSession,
    series: str | None = None,
    models: list[str] | None = None,
    manufacture_month_from: str | None = None,
    manufacture_month_to: str | None = None,
    operation_start_month_from: str | None = None,
    operation_start_month_to: str | None = None,
) -> list[dict[str, Any]]:
    """条件に合致する機番を検索"""
    query = select(Machine).options(selectinload(Machine.model))
    
    # フィルター条件を追加
    if models and len(models) > 0:
        query = query.where(Machine.model_id.in_(models))
    elif series:
        # シリーズから機種を取得してフィルター
        model_ids = await get_models(session, series)
        query = query.where(Machine.model_id.in_(model_ids))
    
    if manufacture_month_from:
        query = query.where(Machine.manufacture_month >= manufacture_month_from)
    if manufacture_month_to:
        query = query.where(Machine.manufacture_month <= manufacture_month_to)
    if operation_start_month_from:
        query = query.where(Machine.operation_start_month >= operation_start_month_from)
    if operation_start_month_to:
        query = query.where(Machine.operation_start_month <= operation_start_month_to)
    
    result = await session.execute(query.order_by(Machine.id))
    machines = result.scalars().all()
    
    return [
        {
            "machine_id": m.id,
            "model": m.model_id,
            "series": m.model.series_id,
            "manufacture_month": m.manufacture_month,
            "operation_start_month": m.operation_start_month,
        }
        for m in machines
    ]


async def get_machine_count(
    session: AsyncSession,
    model: str,
) -> int:
    """指定機種の機番数を取得"""
    result = await session.execute(
        select(func.count(Machine.id)).where(Machine.model_id == model)
    )
    return result.scalar() or 0
