"""
APIエンドポイント
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.data import dummy
from app.data import annotations

router = APIRouter(tags=["api"])


# リクエストモデル
class SearchRequest(BaseModel):
    series: str | None = None
    models: list[str] | None = None  # 複数選択対応
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
    variables: list[dict[str, str]]  # [{"category": "...", "characteristic_id": "...", "axis": "left|right"}]
    aggregation: str
    x_axis_type: str = "time"  # "time" or "usage"


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
    models: list[str]  # 複数機種をグループ比較
    category: str
    characteristic_id: str
    aggregation: str
    target_month: str


class AnnotationsRequest(BaseModel):
    """アノテーションリクエスト"""
    machine_ids: list[str]
    months: int = 12


# マスターデータ取得
@router.get("/series")
def get_series() -> list[str]:
    """機種シリーズ一覧"""
    return dummy.get_series_list()


@router.get("/models/{series}")
def get_models(series: str) -> list[str]:
    """機種番号一覧"""
    return dummy.get_models_by_series(series)


@router.get("/machines/{model}")
def get_machines(model: str) -> list[str]:
    """機番一覧"""
    return dummy.get_machines_by_model(model)


@router.get("/categories")
def get_categories() -> list[str]:
    """データカテゴリー一覧"""
    return dummy.get_data_categories()


@router.get("/characteristics/{category}")
def get_characteristics(category: str) -> list[str]:
    """特性値ID一覧"""
    return dummy.get_characteristic_ids(category)


@router.get("/aggregations")
def get_aggregations() -> list[str]:
    """集計方法一覧"""
    return dummy.get_aggregation_methods()


@router.get("/months")
def get_months() -> list[str]:
    """選択可能月一覧"""
    return dummy.get_available_months()


@router.get("/annotation-types")
def get_annotation_types() -> list[dict[str, str]]:
    """アノテーションタイプ一覧"""
    return annotations.get_annotation_types()


# 機番検索
@router.post("/search")
def search_machines(req: SearchRequest) -> list[dict[str, Any]]:
    """条件に合致する機番を検索"""
    return dummy.search_machines(
        series=req.series,
        models=req.models,
        manufacture_month_from=req.manufacture_month_from,
        manufacture_month_to=req.manufacture_month_to,
        operation_start_month_from=req.operation_start_month_from,
        operation_start_month_to=req.operation_start_month_to,
    )


@router.post("/sample")
def sample_machines(req: SampleRequest) -> list[str]:
    """機番リストからランダムサンプリング"""
    machines = [{"machine_id": mid} for mid in req.machine_ids]
    sampled = dummy.random_sample_machines(machines, req.sample_size)
    return [m["machine_id"] for m in sampled]


# 時系列データ
@router.post("/timeseries")
def get_timeseries(req: TimeseriesRequest) -> dict[str, Any]:
    """時系列データを取得"""
    return dummy.generate_timeseries_data(
        machine_ids=req.machine_ids,
        category=req.category,
        characteristic_id=req.characteristic_id,
        aggregation=req.aggregation,
    )


@router.post("/timeseries/multi")
def get_multi_timeseries(req: MultiTimeseriesRequest) -> dict[str, Any]:
    """多変量時系列データを取得"""
    return dummy.generate_multi_timeseries_data(
        machine_ids=req.machine_ids,
        variables=req.variables,
        aggregation=req.aggregation,
        x_axis_type=req.x_axis_type,
    )


@router.post("/annotations")
def get_annotations(req: AnnotationsRequest) -> list[dict[str, Any]]:
    """アノテーション（イベント情報）を取得"""
    return annotations.get_annotations_for_timeseries(
        machine_ids=req.machine_ids,
        months=req.months,
    )


# 断面データ
@router.post("/histogram")
def get_histogram(req: HistogramRequest) -> dict[str, Any]:
    """断面データを取得"""
    return dummy.generate_histogram_data(
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
    return dummy.generate_scatter_data(
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
    return dummy.generate_boxplot_data(
        models=req.models,
        category=req.category,
        characteristic_id=req.characteristic_id,
        aggregation=req.aggregation,
        target_month=req.target_month,
    )
