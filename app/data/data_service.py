"""
データサービス

開発環境ではダミーデータ、本番環境ではデータベースからデータを取得。
設定に応じて自動的に切り替える。
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data import dummy
from app.data import annotations as ann_module
from app.data import repository


async def get_series(db: AsyncSession | None = None) -> list[str]:
    """シリーズ一覧を取得"""
    if settings.use_dummy_data or db is None:
        return dummy.get_series_list()
    return await repository.get_series(db)


async def get_models(series: str, db: AsyncSession | None = None) -> list[str]:
    """機種番号一覧を取得"""
    if settings.use_dummy_data or db is None:
        return dummy.get_models_by_series(series)
    return await repository.get_models(db, series)


async def get_machines(model: str, db: AsyncSession | None = None) -> list[str]:
    """機番一覧を取得"""
    if settings.use_dummy_data or db is None:
        return dummy.get_machines_by_model(model)
    # TODO: リポジトリに追加
    return dummy.get_machines_by_model(model)


async def get_categories(db: AsyncSession | None = None) -> list[str]:
    """カテゴリー一覧を取得"""
    if settings.use_dummy_data or db is None:
        return dummy.get_data_categories()
    return await repository.get_categories(db)


async def get_characteristics(category: str, db: AsyncSession | None = None) -> list[str]:
    """特性値ID一覧を取得"""
    if settings.use_dummy_data or db is None:
        return dummy.get_characteristic_ids(category)
    return await repository.get_characteristics(db, category)


async def get_aggregations(db: AsyncSession | None = None) -> list[str]:
    """集計方法一覧を取得"""
    if settings.use_dummy_data or db is None:
        return dummy.get_aggregation_methods()
    return await repository.get_aggregations(db)


async def get_months(db: AsyncSession | None = None) -> list[str]:
    """月一覧を取得"""
    if settings.use_dummy_data or db is None:
        return dummy.get_available_months()
    return await repository.get_months(db)


def get_annotation_types() -> list[dict[str, str]]:
    """アノテーションタイプ一覧を取得"""
    return ann_module.get_annotation_types()


async def search_machines(
    series: str | None = None,
    models: list[str] | None = None,
    manufacture_month_from: str | None = None,
    manufacture_month_to: str | None = None,
    operation_start_month_from: str | None = None,
    operation_start_month_to: str | None = None,
    db: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """機番検索"""
    if settings.use_dummy_data or db is None:
        return dummy.search_machines(
            series=series,
            models=models,
            manufacture_month_from=manufacture_month_from,
            manufacture_month_to=manufacture_month_to,
            operation_start_month_from=operation_start_month_from,
            operation_start_month_to=operation_start_month_to,
        )
    return await repository.search_machines(
        db,
        series=series,
        models=models,
        manufacture_month_from=manufacture_month_from,
        manufacture_month_to=manufacture_month_to,
        operation_start_month_from=operation_start_month_from,
        operation_start_month_to=operation_start_month_to,
    )


def sample_machines(machine_ids: list[str], sample_size: int) -> list[str]:
    """ランダムサンプリング"""
    machines = [{"machine_id": mid} for mid in machine_ids]
    sampled = dummy.random_sample_machines(machines, sample_size)
    return [m["machine_id"] for m in sampled]


def get_timeseries(
    machine_ids: list[str],
    category: str,
    characteristic_id: str,
    aggregation: str,
) -> dict[str, Any]:
    """時系列データを取得"""
    # 現時点ではダミーデータのみ（本番DBへの時系列データ格納は別途実装）
    return dummy.generate_timeseries_data(
        machine_ids=machine_ids,
        category=category,
        characteristic_id=characteristic_id,
        aggregation=aggregation,
    )


def get_multi_timeseries(
    machine_ids: list[str],
    variables: list[dict[str, str]],
    aggregation: str,
    x_axis_type: str = "time",
) -> dict[str, Any]:
    """多変量時系列データを取得"""
    return dummy.generate_multi_timeseries_data(
        machine_ids=machine_ids,
        variables=variables,
        aggregation=aggregation,
        x_axis_type=x_axis_type,
    )


def get_annotations(machine_ids: list[str], months: int = 12) -> list[dict[str, Any]]:
    """アノテーションを取得"""
    return ann_module.get_annotations_for_timeseries(
        machine_ids=machine_ids,
        months=months,
    )


def get_histogram(
    model: str,
    category: str,
    characteristic_id: str,
    aggregation: str,
    target_month: str,
    selected_machine_ids: list[str] | None = None,
) -> dict[str, Any]:
    """ヒストグラムデータを取得"""
    return dummy.generate_histogram_data(
        model=model,
        category=category,
        characteristic_id=characteristic_id,
        aggregation=aggregation,
        target_month=target_month,
        selected_machine_ids=selected_machine_ids,
    )


def get_scatter(
    model: str,
    x_category: str,
    x_characteristic_id: str,
    y_category: str,
    y_characteristic_id: str,
    aggregation: str,
    target_month: str,
    selected_machine_ids: list[str] | None = None,
) -> dict[str, Any]:
    """散布図データを取得"""
    return dummy.generate_scatter_data(
        model=model,
        x_category=x_category,
        x_characteristic_id=x_characteristic_id,
        y_category=y_category,
        y_characteristic_id=y_characteristic_id,
        aggregation=aggregation,
        target_month=target_month,
        selected_machine_ids=selected_machine_ids,
    )


def get_boxplot(
    models: list[str],
    category: str,
    characteristic_id: str,
    aggregation: str,
    target_month: str,
) -> dict[str, Any]:
    """箱ひげ図データを取得"""
    return dummy.generate_boxplot_data(
        models=models,
        category=category,
        characteristic_id=characteristic_id,
        aggregation=aggregation,
        target_month=target_month,
    )
