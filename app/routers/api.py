"""
APIエンドポイント

データサービス層を使用してデータを取得。
開発環境ではダミーデータ、本番環境ではデータベースから取得。
"""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.data import data_service

router = APIRouter(tags=["api"])


# 依存性注入：本番環境のみDBセッションを提供
async def get_optional_db() -> AsyncSession | None:
    """設定に応じてDBセッションを提供（開発環境ではNone）"""
    if settings.use_dummy_data:
        return None
    async for db in get_db():
        return db
    return None


# リクエストモデル
class SearchRequest(BaseModel):
    series: str | None = None
    models: list[str] | None = None
    manufacture_month_from: str | None = None
    manufacture_month_to: str | None = None
    operation_start_month_from: str | None = None
    operation_start_month_to: str | None = None


class SampleRequest(BaseModel):
    machine_ids: list[str]
    sample_size: int


class TimeseriesRequest(BaseModel):
    machine_ids: list[str]
    category: str
    characteristic_id: str
    aggregation: str


class MultiTimeseriesRequest(BaseModel):
    """多変量時系列リクエスト"""
    machine_ids: list[str]
    variables: list[dict[str, str]]
    aggregation: str
    x_axis_type: str = "time_month"  # "time_month" | "time_day" | "usage"
    date_from: str | None = None  # 日単位表示時の開始日
    date_to: str | None = None    # 日単位表示時の終了日


class HistogramRequest(BaseModel):
    model: str
    category: str
    characteristic_id: str
    aggregation: str
    target_date_from: str
    target_date_to: str
    selected_machine_ids: list[str] | None = None


class ScatterRequest(BaseModel):
    """散布図リクエスト"""
    model: str
    x_category: str
    x_characteristic_id: str
    y_category: str
    y_characteristic_id: str
    aggregation: str
    target_month: str
    selected_machine_ids: list[str] | None = None


class BoxplotRequest(BaseModel):
    """箱ひげ図リクエスト"""
    models: list[str]
    category: str
    characteristic_id: str
    aggregation: str
    target_month: str


class DistributionBoxplotRequest(BaseModel):
    """分布傾向箱ひげ図リクエスト"""
    model: str
    x_axis_type: str  # "usage" | "mfg_month"
    bin_width: int = 50000  # ビン幅（使用回数の場合）
    category: str
    characteristic_id: str
    aggregation: str
    selected_machine_ids: list[str] | None = None
    chart_type: str = "boxplot"  # "boxplot" | "line"


class AnnotationsRequest(BaseModel):
    """アノテーションリクエスト"""
    machine_ids: list[str]
    months: int = 12
    date_from: str | None = None
    date_to: str | None = None


# マスターデータ取得
@router.get("/series")
async def get_series(db: AsyncSession | None = Depends(get_optional_db)) -> list[str]:
    """機種シリーズ一覧"""
    return await data_service.get_series(db)


@router.get("/models/{series}")
async def get_models(series: str, db: AsyncSession | None = Depends(get_optional_db)) -> list[str]:
    """機種番号一覧"""
    return await data_service.get_models(series, db)


@router.get("/machines/{model}")
async def get_machines(model: str, db: AsyncSession | None = Depends(get_optional_db)) -> list[str]:
    """機番一覧"""
    return await data_service.get_machines(model, db)


@router.get("/categories")
async def get_categories(db: AsyncSession | None = Depends(get_optional_db)) -> list[str]:
    """データカテゴリー一覧"""
    return await data_service.get_categories(db)


@router.get("/characteristics/{category}")
async def get_characteristics(category: str, db: AsyncSession | None = Depends(get_optional_db)) -> list[str]:
    """特性値ID一覧"""
    return await data_service.get_characteristics(category, db)


@router.get("/aggregations")
async def get_aggregations(db: AsyncSession | None = Depends(get_optional_db)) -> list[str]:
    """集計方法一覧"""
    return await data_service.get_aggregations(db)


@router.get("/months")
async def get_months(db: AsyncSession | None = Depends(get_optional_db)) -> list[str]:
    """選択可能月一覧"""
    return await data_service.get_months(db)


@router.get("/annotation-types")
def get_annotation_types() -> list[dict[str, str]]:
    """アノテーションタイプ一覧"""
    return data_service.get_annotation_types()


# 機番検索
@router.post("/search")
async def search_machines(req: SearchRequest, db: AsyncSession | None = Depends(get_optional_db)) -> list[dict[str, Any]]:
    """条件に合致する機番を検索"""
    return await data_service.search_machines(
        series=req.series,
        models=req.models,
        manufacture_month_from=req.manufacture_month_from,
        manufacture_month_to=req.manufacture_month_to,
        operation_start_month_from=req.operation_start_month_from,
        operation_start_month_to=req.operation_start_month_to,
        db=db,
    )


@router.post("/sample")
def sample_machines(req: SampleRequest) -> list[str]:
    """機番リストからランダムサンプリング"""
    return data_service.sample_machines(req.machine_ids, req.sample_size)


# 時系列データ
@router.post("/timeseries")
async def get_timeseries(req: TimeseriesRequest, db: AsyncSession | None = Depends(get_optional_db)) -> dict[str, Any]:
    """時系列データを取得"""
    if settings.use_dummy_data or db is None:
        return data_service.get_timeseries(
            machine_ids=req.machine_ids,
            category=req.category,
            characteristic_id=req.characteristic_id,
            aggregation=req.aggregation,
        )
    from app.data import repository
    return await repository.get_timeseries_data(
        session=db,
        machine_ids=req.machine_ids,
        category=req.category,
        characteristic_id=req.characteristic_id,
        aggregation=req.aggregation,
    )


@router.post("/timeseries/multi")
async def get_multi_timeseries(req: MultiTimeseriesRequest, db: AsyncSession | None = Depends(get_optional_db)) -> dict[str, Any]:
    """多変量時系列データを取得"""
    if settings.use_dummy_data or db is None:
        return data_service.get_multi_timeseries(
            machine_ids=req.machine_ids,
            variables=req.variables,
            aggregation=req.aggregation,
            x_axis_type=req.x_axis_type,
            date_from=req.date_from,
            date_to=req.date_to,
        )
    from app.data import repository
    return await repository.get_multi_timeseries_data(
        session=db,
        machine_ids=req.machine_ids,
        variables=req.variables,
        aggregation=req.aggregation,
        x_axis_type=req.x_axis_type,
        date_from=req.date_from,
        date_to=req.date_to,
    )


@router.post("/annotations")
async def get_annotations(req: AnnotationsRequest, db: AsyncSession | None = Depends(get_optional_db)) -> list[dict[str, Any]]:
    """アノテーション（イベント情報）を取得"""
    if settings.use_dummy_data or db is None:
        return data_service.get_annotations(
            machine_ids=req.machine_ids,
            months=req.months,
            date_from=req.date_from,
            date_to=req.date_to,
        )
    from app.data import repository
    return await repository.get_annotations_data(
        session=db,
        machine_ids=req.machine_ids,
        months=req.months,
        date_from=req.date_from,
        date_to=req.date_to,
    )


# 断面データ
@router.post("/histogram")
async def get_histogram(req: HistogramRequest, db: AsyncSession | None = Depends(get_optional_db)) -> dict[str, Any]:
    """断面データを取得"""
    if settings.use_dummy_data or db is None:
        return data_service.get_histogram(
            model=req.model,
            category=req.category,
            characteristic_id=req.characteristic_id,
            aggregation=req.aggregation,
            target_date_from=req.target_date_from,
            target_date_to=req.target_date_to,
            selected_machine_ids=req.selected_machine_ids,
        )
    from app.data import repository
    return await repository.get_histogram_data(
        session=db,
        model=req.model,
        category=req.category,
        characteristic_id=req.characteristic_id,
        aggregation=req.aggregation,
        target_date_from=req.target_date_from,
        target_date_to=req.target_date_to,
        selected_machine_ids=req.selected_machine_ids,
    )


@router.post("/scatter")
async def get_scatter(req: ScatterRequest, db: AsyncSession | None = Depends(get_optional_db)) -> dict[str, Any]:
    """散布図データを取得"""
    if settings.use_dummy_data or db is None:
        return data_service.get_scatter(
            model=req.model,
            x_category=req.x_category,
            x_characteristic_id=req.x_characteristic_id,
            y_category=req.y_category,
            y_characteristic_id=req.y_characteristic_id,
            aggregation=req.aggregation,
            target_month=req.target_month,
            selected_machine_ids=req.selected_machine_ids,
        )
    from app.data import repository
    return await repository.get_scatter_data(
        session=db,
        model=req.model,
        x_category=req.x_category,
        x_characteristic_id=req.x_characteristic_id,
        y_category=req.y_category,
        y_characteristic_id=req.y_characteristic_id,
        aggregation=req.aggregation,
        target_month=req.target_month,
        selected_machine_ids=req.selected_machine_ids,
    )


@router.post("/boxplot")
async def get_boxplot(req: BoxplotRequest, db: AsyncSession | None = Depends(get_optional_db)) -> dict[str, Any]:
    """箱ひげ図データを取得"""
    if settings.use_dummy_data or db is None:
        return data_service.get_boxplot(
            models=req.models,
            category=req.category,
            characteristic_id=req.characteristic_id,
            aggregation=req.aggregation,
            target_month=req.target_month,
        )
    from app.data import repository
    return await repository.get_boxplot_data(
        session=db,
        models=req.models,
        category=req.category,
        characteristic_id=req.characteristic_id,
        aggregation=req.aggregation,
        target_month=req.target_month,
    )



@router.post("/distribution-boxplot")
def get_distribution_boxplot(req: DistributionBoxplotRequest) -> dict[str, Any]:
    """分布傾向箱ひげ図データを取得"""
    return data_service.get_distribution_boxplot(
        model=req.model,
        x_axis_type=req.x_axis_type,
        bin_width=req.bin_width,
        category=req.category,
        characteristic_id=req.characteristic_id,
        aggregation=req.aggregation,
        selected_machine_ids=req.selected_machine_ids,
        chart_type=req.chart_type,
    )


# ========================================
# 不具合分析API
# ========================================
class DefectTimeseriesRequest(BaseModel):
    series: str | None = None
    models: list[str] | None = None  # 複数選択対応
    date_from: str
    date_to: str
    defect_types: list[str] | None = None  # 複数選択対応
    group_by: str = "month"  # 'month' | 'day'


class DefectSummaryRequest(BaseModel):
    series: str | None = None
    models: list[str] | None = None  # 複数選択対応
    date_from: str
    date_to: str
    defect_types: list[str] | None = None  # 複数選択対応


@router.get("/defect-types")
async def get_defect_types(db: AsyncSession | None = Depends(get_optional_db)) -> list[str]:
    """不具合種別マスタを取得"""
    if settings.use_dummy_data or db is None:
        from app.data.dummy import get_defect_types
        return get_defect_types()
    from app.data import repository
    return await repository.get_defect_types(db)


@router.post("/defects/timeseries")
async def get_defects_timeseries(req: DefectTimeseriesRequest, db: AsyncSession | None = Depends(get_optional_db)) -> dict[str, Any]:
    """不具合発生件数の時系列データを取得"""
    if settings.use_dummy_data or db is None:
        from app.data.dummy import generate_defect_timeseries
        return generate_defect_timeseries(
            series=req.series,
            models=req.models,
            date_from=req.date_from,
            date_to=req.date_to,
            defect_types=req.defect_types,
            group_by=req.group_by,
        )
    from app.data import repository
    return await repository.get_defects_timeseries(
        session=db,
        series=req.series,
        models=req.models,
        date_from=req.date_from,
        date_to=req.date_to,
        defect_types=req.defect_types,
        group_by=req.group_by,
    )


@router.post("/defects/summary")
async def get_defects_summary(req: DefectSummaryRequest, db: AsyncSession | None = Depends(get_optional_db)) -> dict[str, Any]:
    """不具合発生件数の集計テーブルデータを取得"""
    if settings.use_dummy_data or db is None:
        from app.data.dummy import generate_defect_summary
        return generate_defect_summary(
            series=req.series,
            models=req.models,
            date_from=req.date_from,
            date_to=req.date_to,
            defect_types=req.defect_types,
        )
    from app.data import repository
    return await repository.get_defects_summary(
        session=db,
        series=req.series,
        models=req.models,
        date_from=req.date_from,
        date_to=req.date_to,
        defect_types=req.defect_types,
    )


class DefectMachinesRequest(BaseModel):
    series: str | None = None
    models: list[str] | None = None  # 複数選択対応
    date_from: str
    date_to: str
    defect_types: list[str] | None = None  # 複数選択対応
    target_period: str | None = None  # グラフクリック時：特定期間（"2025-01" or "2025-01-15"）
    target_defect_type: str | None = None  # グラフクリック時：特定不具合種別


@router.post("/defects/machines")
async def get_defect_machines(req: DefectMachinesRequest, db: AsyncSession | None = Depends(get_optional_db)) -> dict[str, Any]:
    """不具合発生機番リストを取得"""
    if settings.use_dummy_data or db is None:
        from app.data.dummy import generate_defect_machines
        return generate_defect_machines(
            series=req.series,
            models=req.models,
            date_from=req.date_from,
            date_to=req.date_to,
            defect_types=req.defect_types,
            target_period=req.target_period,
            target_defect_type=req.target_defect_type,
        )
    from app.data import repository
    return await repository.get_defect_machines(
        session=db,
        series=req.series,
        models=req.models,
        date_from=req.date_from,
        date_to=req.date_to,
        defect_types=req.defect_types,
        target_period=req.target_period,
        target_defect_type=req.target_defect_type,
    )

