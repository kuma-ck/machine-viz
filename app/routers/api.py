"""
APIエンドポイント
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.data import dummy

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


class HistogramRequest(BaseModel):
    model: str
    category: str
    characteristic_id: str
    aggregation: str
    target_month: str
    selected_machine_ids: list[str] | None = None


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
