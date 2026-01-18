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
    x_axis_type: str = "time"


class HistogramRequest(BaseModel):
    model: str
    category: str
    characteristic_id: str
    aggregation: str
    target_month: str
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
def get_timeseries(req: TimeseriesRequest) -> dict[str, Any]:
    """時系列データを取得"""
    return data_service.get_timeseries(
        machine_ids=req.machine_ids,
        category=req.category,
        characteristic_id=req.characteristic_id,
        aggregation=req.aggregation,
    )


@router.post("/timeseries/multi")
def get_multi_timeseries(req: MultiTimeseriesRequest) -> dict[str, Any]:
    """多変量時系列データを取得"""
    return data_service.get_multi_timeseries(
        machine_ids=req.machine_ids,
        variables=req.variables,
        aggregation=req.aggregation,
        x_axis_type=req.x_axis_type,
    )


@router.post("/annotations")
def get_annotations(req: AnnotationsRequest) -> list[dict[str, Any]]:
    """アノテーション（イベント情報）を取得"""
    return data_service.get_annotations(
        machine_ids=req.machine_ids,
        months=req.months,
    )


# 断面データ
@router.post("/histogram")
def get_histogram(req: HistogramRequest) -> dict[str, Any]:
    """断面データを取得"""
    return data_service.get_histogram(
        model=req.model,
        category=req.category,
        characteristic_id=req.characteristic_id,
        aggregation=req.aggregation,
        target_month=req.target_month,
        selected_machine_ids=req.selected_machine_ids,
    )


@router.post("/scatter")
def get_scatter(req: ScatterRequest) -> dict[str, Any]:
    """散布図データを取得"""
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


@router.post("/boxplot")
def get_boxplot(req: BoxplotRequest) -> dict[str, Any]:
    """箱ひげ図データを取得"""
    return data_service.get_boxplot(
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
