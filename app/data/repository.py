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
            "firmware_version": m.firmware_version or "-",
            "options": m.options or "標準",
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


async def get_timeseries_data(
    session: AsyncSession,
    machine_ids: list[str],
    category: str,
    characteristic_id: str,
    aggregation: str,
    months: int = 12,
) -> dict[str, Any]:
    """
    時系列データを取得
    
    Returns:
        {
            "labels": ["2025-02", "2025-03", ...],
            "datasets": [
                {"machine_id": "A-1-000001", "data": [10.5, 12.3, ...]},
                ...
            ]
        }
    """
    from datetime import datetime, timedelta
    
    # 対象月のリストを生成
    base_date = datetime(2026, 1, 1)
    labels = []
    for i in range(months - 1, -1, -1):
        d = base_date - timedelta(days=i * 30)
        labels.append(d.strftime("%Y-%m"))
    
    # 特性値IDを取得
    char_result = await session.execute(
        select(Characteristic.id)
        .where(Characteristic.category_id == category)
        .where(Characteristic.name == characteristic_id)
    )
    char_id = char_result.scalar()
    
    if not char_id:
        # 特性値が見つからない場合は空のデータを返す
        return {
            "labels": labels,
            "datasets": [{"machine_id": mid, "data": [None] * months} for mid in machine_ids]
        }
    
    # 機番ごとにデータを取得
    datasets = []
    for machine_id in machine_ids:
        result = await session.execute(
            select(MachineData.month, MachineData.value)
            .where(MachineData.machine_id == machine_id)
            .where(MachineData.characteristic_id == char_id)
            .where(MachineData.aggregation == aggregation)
            .where(MachineData.month.in_(labels))
            .order_by(MachineData.month)
        )
        rows = result.all()
        
        # 月ごとのデータをマッピング
        month_data = {row.month: row.value for row in rows}
        data = [round(month_data.get(label, 0), 2) if month_data.get(label) is not None else None for label in labels]
        
        datasets.append({
            "machine_id": machine_id,
            "data": data,
        })
    
    return {
        "labels": labels,
        "datasets": datasets,
    }


async def get_multi_timeseries_data(
    session: AsyncSession,
    machine_ids: list[str],
    variables: list[dict[str, str]],
    aggregation: str,
    x_axis_type: str = "time_month",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """
    多変量時系列データを取得
    
    Args:
        machine_ids: 機番リスト
        variables: [{"category": "...", "characteristic_id": "...", "axis": "left|right"}, ...]
        aggregation: 集計方法
        x_axis_type: X軸タイプ ("time_month", "time_day", "usage")
    
    Returns:
        {
            "labels": ["2025-02", ...],
            "datasets": [
                {"label": "特性値1", "data": [...], "axis": "left", "machine_count": 3},
                ...
            ],
            "scales": {...}
        }
    """
    from datetime import datetime, timedelta
    
    # X軸ラベルを生成
    if x_axis_type == "time_day" and date_from and date_to:
        start = datetime.strptime(date_from, "%Y-%m-%d")
        end = datetime.strptime(date_to, "%Y-%m-%d")
        labels = []
        current = start
        while current <= end:
            labels.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
    else:
        # 月次（デフォルト12ヶ月）
        base_date = datetime(2026, 1, 1)
        labels = []
        for i in range(11, -1, -1):
            d = base_date - timedelta(days=i * 30)
            labels.append(d.strftime("%Y-%m"))
    
    datasets = []
    left_values = []
    right_values = []
    
    for var in variables:
        category = var.get("category", "")
        char_name = var.get("characteristic_id", "")
        axis = var.get("axis", "left")
        
        # 特性値IDを取得
        char_result = await session.execute(
            select(Characteristic.id)
            .where(Characteristic.category_id == category)
            .where(Characteristic.name == char_name)
        )
        char_id = char_result.scalar()
        
        if not char_id:
            datasets.append({
                "label": char_name,
                "data": [None] * len(labels),
                "axis": axis,
                "machine_count": len(machine_ids),
            })
            continue
        
        # 全機番のデータを取得して平均を計算
        all_data = []
        for label in labels:
            result = await session.execute(
                select(func.avg(MachineData.value))
                .where(MachineData.machine_id.in_(machine_ids))
                .where(MachineData.characteristic_id == char_id)
                .where(MachineData.aggregation == aggregation)
                .where(MachineData.month == label if x_axis_type == "time_month" else True)
            )
            avg_value = result.scalar()
            all_data.append(round(avg_value, 2) if avg_value is not None else None)
        
        datasets.append({
            "label": char_name,
            "data": all_data,
            "axis": axis,
            "machine_count": len(machine_ids),
        })
        
        # スケール計算用にデータを収集
        valid_data = [v for v in all_data if v is not None]
        if axis == "left":
            left_values.extend(valid_data)
        else:
            right_values.extend(valid_data)
    
    # スケール情報
    scales = {}
    if left_values:
        scales["left"] = {
            "min": 0,
            "max": max(left_values) * 1.2 if left_values else 100,
            "label": variables[0].get("characteristic_id", "") if variables else "",
        }
    if right_values:
        right_vars = [v for v in variables if v.get("axis") == "right"]
        scales["right"] = {
            "min": 0,
            "max": max(right_values) * 1.2 if right_values else 100,
            "label": right_vars[0].get("characteristic_id", "") if right_vars else "",
        }
    
    return {
        "labels": labels,
        "datasets": datasets,
        "scales": scales,
        "x_axis_type": x_axis_type,
    }


async def get_histogram_data(
    session: AsyncSession,
    model: str,
    category: str,
    characteristic_id: str,
    aggregation: str,
    target_date_from: str,
    target_date_to: str,
    selected_machine_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    ヒストグラムデータを取得
    
    Returns:
        {
            "labels": ["0-10", "10-20", ...],
            "datasets": [
                {"label": "母集団", "data": [10, 20, ...]},
                {"label": "選択機番", "data": [2, 5, ...]}
            ],
            "stats": {"mean": ..., "std": ..., "n": ...}
        }
    """
    import numpy as np
    
    # 特性値IDを取得
    char_result = await session.execute(
        select(Characteristic.id)
        .where(Characteristic.category_id == category)
        .where(Characteristic.name == characteristic_id)
    )
    char_id = char_result.scalar()
    
    if not char_id:
        return {"labels": [], "datasets": [], "stats": {}}
    
    # 対象機種の機番を取得
    machine_result = await session.execute(
        select(Machine.id).where(Machine.model_id == model)
    )
    all_machine_ids = [row[0] for row in machine_result.all()]
    
    # データを取得
    result = await session.execute(
        select(MachineData.machine_id, MachineData.value)
        .where(MachineData.machine_id.in_(all_machine_ids))
        .where(MachineData.characteristic_id == char_id)
        .where(MachineData.aggregation == aggregation)
        .where(MachineData.month >= target_date_from[:7])
        .where(MachineData.month <= target_date_to[:7])
    )
    rows = result.all()
    
    if not rows:
        return {"labels": [], "datasets": [], "stats": {}}
    
    # 機番ごとの平均値を計算
    machine_values = {}
    for machine_id, value in rows:
        if machine_id not in machine_values:
            machine_values[machine_id] = []
        machine_values[machine_id].append(value)
    
    all_values = [np.mean(vals) for vals in machine_values.values()]
    
    # ヒストグラムを計算
    if not all_values:
        return {"labels": [], "datasets": [], "stats": {}}
    
    hist, bin_edges = np.histogram(all_values, bins=10)
    labels = [f"{bin_edges[i]:.0f}-{bin_edges[i+1]:.0f}" for i in range(len(hist))]
    
    datasets = [{
        "label": "母集団",
        "data": hist.tolist(),
    }]
    
    # 選択機番がある場合
    if selected_machine_ids:
        selected_values = [np.mean(machine_values[mid]) for mid in selected_machine_ids if mid in machine_values]
        if selected_values:
            selected_hist, _ = np.histogram(selected_values, bins=bin_edges)
            datasets.append({
                "label": "選択機番",
                "data": selected_hist.tolist(),
            })
    
    return {
        "labels": labels,
        "datasets": datasets,
        "stats": {
            "mean": round(np.mean(all_values), 2),
            "std": round(np.std(all_values), 2),
            "n": len(all_values),
        },
    }


async def get_scatter_data(
    session: AsyncSession,
    model: str,
    x_category: str,
    x_characteristic_id: str,
    y_category: str,
    y_characteristic_id: str,
    aggregation: str,
    target_month: str,
    selected_machine_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    散布図データを取得
    
    Returns:
        {
            "datasets": [
                {"label": "母集団", "data": [{"x": 10, "y": 20, "machine_id": "..."}, ...]},
                {"label": "選択機番", "data": [...]}
            ],
            "x_label": "...",
            "y_label": "..."
        }
    """
    # 特性値IDを取得
    x_char_result = await session.execute(
        select(Characteristic.id)
        .where(Characteristic.category_id == x_category)
        .where(Characteristic.name == x_characteristic_id)
    )
    x_char_id = x_char_result.scalar()
    
    y_char_result = await session.execute(
        select(Characteristic.id)
        .where(Characteristic.category_id == y_category)
        .where(Characteristic.name == y_characteristic_id)
    )
    y_char_id = y_char_result.scalar()
    
    if not x_char_id or not y_char_id:
        return {"datasets": [], "x_label": x_characteristic_id, "y_label": y_characteristic_id}
    
    # 対象機種の機番を取得
    machine_result = await session.execute(
        select(Machine.id).where(Machine.model_id == model)
    )
    all_machine_ids = [row[0] for row in machine_result.all()]
    
    # X軸データを取得
    x_result = await session.execute(
        select(MachineData.machine_id, MachineData.value)
        .where(MachineData.machine_id.in_(all_machine_ids))
        .where(MachineData.characteristic_id == x_char_id)
        .where(MachineData.aggregation == aggregation)
        .where(MachineData.month == target_month[:7])
    )
    x_data = {row.machine_id: row.value for row in x_result.all()}
    
    # Y軸データを取得
    y_result = await session.execute(
        select(MachineData.machine_id, MachineData.value)
        .where(MachineData.machine_id.in_(all_machine_ids))
        .where(MachineData.characteristic_id == y_char_id)
        .where(MachineData.aggregation == aggregation)
        .where(MachineData.month == target_month[:7])
    )
    y_data = {row.machine_id: row.value for row in y_result.all()}
    
    # 両方のデータがある機番のみ
    common_ids = set(x_data.keys()) & set(y_data.keys())
    
    all_points = [
        {"x": round(x_data[mid], 2), "y": round(y_data[mid], 2), "machine_id": mid}
        for mid in common_ids
    ]
    
    datasets = [{"label": "母集団", "data": all_points}]
    
    if selected_machine_ids:
        selected_points = [p for p in all_points if p["machine_id"] in selected_machine_ids]
        datasets.append({"label": "選択機番", "data": selected_points})
    
    return {
        "datasets": datasets,
        "x_label": x_characteristic_id,
        "y_label": y_characteristic_id,
    }


async def get_boxplot_data(
    session: AsyncSession,
    models: list[str],
    category: str,
    characteristic_id: str,
    aggregation: str,
    target_month: str,
) -> dict[str, Any]:
    """
    箱ひげ図データを取得
    
    Returns:
        {
            "labels": ["A-1", "A-2", ...],
            "datasets": [{
                "label": "特性値名",
                "data": [[min, q1, median, q3, max], ...]
            }]
        }
    """
    import numpy as np
    
    # 特性値IDを取得
    char_result = await session.execute(
        select(Characteristic.id)
        .where(Characteristic.category_id == category)
        .where(Characteristic.name == characteristic_id)
    )
    char_id = char_result.scalar()
    
    if not char_id:
        return {"labels": models, "datasets": []}
    
    boxplot_data = []
    
    for model in models:
        # 対象機種の機番を取得
        machine_result = await session.execute(
            select(Machine.id).where(Machine.model_id == model)
        )
        machine_ids = [row[0] for row in machine_result.all()]
        
        # データを取得
        result = await session.execute(
            select(MachineData.value)
            .where(MachineData.machine_id.in_(machine_ids))
            .where(MachineData.characteristic_id == char_id)
            .where(MachineData.aggregation == aggregation)
            .where(MachineData.month == target_month[:7])
        )
        values = [row[0] for row in result.all()]
        
        if values:
            q1, median, q3 = np.percentile(values, [25, 50, 75])
            boxplot_data.append([
                round(min(values), 2),
                round(q1, 2),
                round(median, 2),
                round(q3, 2),
                round(max(values), 2),
            ])
        else:
            boxplot_data.append([0, 0, 0, 0, 0])
    
    return {
        "labels": models,
        "datasets": [{
            "label": characteristic_id,
            "data": boxplot_data,
        }],
    }


async def get_annotations_data(
    session: AsyncSession,
    machine_ids: list[str],
    months: int = 12,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """
    アノテーションデータを取得
    
    Returns:
        [
            {"machine_id": "...", "date": "...", "type": "...", "description": "..."},
            ...
        ]
    """
    from datetime import datetime, timedelta
    
    if date_from and date_to:
        start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
    else:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=months * 30)
    
    result = await session.execute(
        select(Annotation)
        .where(Annotation.machine_id.in_(machine_ids))
        .where(Annotation.event_date >= start_date)
        .where(Annotation.event_date <= end_date)
        .order_by(Annotation.event_date)
    )
    annotations = result.scalars().all()
    
    return [
        {
            "machine_id": a.machine_id,
            "date": a.event_date.isoformat(),
            "type": a.event_type,
            "description": a.description,
        }
        for a in annotations
    ]


async def get_defect_types(session: AsyncSession) -> list[str]:
    """不具合種別マスタを取得"""
    from app.models import Defect
    
    result = await session.execute(
        select(Defect.defect_type).distinct().order_by(Defect.defect_type)
    )
    return [row[0] for row in result.all()]


async def get_defects_timeseries(
    session: AsyncSession,
    series: str | None = None,
    models: list[str] | None = None,
    date_from: str = None,
    date_to: str = None,
    defect_types: list[str] | None = None,
    group_by: str = "month",
) -> dict[str, Any]:
    """
    不具合発生件数の時系列データを取得
    
    Returns:
        {
            "labels": ["2025-01", "2025-02", ...],
            "datasets": [
                {"label": "異音", "data": [10, 20, ...]},
                ...
            ]
        }
    """
    from datetime import datetime
    from collections import defaultdict
    from app.models import Defect
    
    # 対象機番を取得
    machine_query = select(Machine.id)
    if models and len(models) > 0:
        machine_query = machine_query.where(Machine.model_id.in_(models))
    elif series:
        model_ids = await get_models(session, series)
        machine_query = machine_query.where(Machine.model_id.in_(model_ids))
    
    machine_result = await session.execute(machine_query)
    target_machine_ids = [row[0] for row in machine_result.all()]
    
    if not target_machine_ids:
        return {"labels": [], "datasets": []}
    
    # 不具合データを取得
    start_date = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
    end_date = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None
    
    query = select(Defect).where(Defect.machine_id.in_(target_machine_ids))
    if start_date:
        query = query.where(Defect.occurred_at >= start_date)
    if end_date:
        query = query.where(Defect.occurred_at <= end_date)
    if defect_types:
        query = query.where(Defect.defect_type.in_(defect_types))
    
    result = await session.execute(query)
    defects = result.scalars().all()
    
    # 期間ごと・種別ごとに集計
    data_by_type = defaultdict(lambda: defaultdict(int))
    all_periods = set()
    all_types = set()
    
    for defect in defects:
        if group_by == "day":
            period = defect.occurred_at.strftime("%Y-%m-%d")
        else:
            period = defect.occurred_at.strftime("%Y-%m")
        data_by_type[defect.defect_type][period] += 1
        all_periods.add(period)
        all_types.add(defect.defect_type)
    
    labels = sorted(all_periods)
    datasets = []
    
    for dtype in sorted(all_types):
        datasets.append({
            "label": dtype,
            "data": [data_by_type[dtype].get(period, 0) for period in labels],
        })
    
    return {
        "labels": labels,
        "datasets": datasets,
    }


async def get_defects_summary(
    session: AsyncSession,
    series: str | None = None,
    models: list[str] | None = None,
    date_from: str = None,
    date_to: str = None,
    defect_types: list[str] | None = None,
) -> dict[str, Any]:
    """
    不具合発生件数の集計テーブルデータを取得
    
    Returns:
        {
            "columns": ["異音", "動作不良", ...],
            "rows": [
                {"model": "A-1", "異音": 10, "動作不良": 5, ...},
                ...
            ]
        }
    """
    from datetime import datetime
    from collections import defaultdict
    from app.models import Defect
    
    # 対象機番を取得
    machine_query = select(Machine.id, Machine.model_id)
    if models and len(models) > 0:
        machine_query = machine_query.where(Machine.model_id.in_(models))
    elif series:
        model_ids = await get_models(session, series)
        machine_query = machine_query.where(Machine.model_id.in_(model_ids))
    
    machine_result = await session.execute(machine_query)
    machine_model_map = {row[0]: row[1] for row in machine_result.all()}
    
    if not machine_model_map:
        return {"columns": [], "rows": []}
    
    # 不具合データを取得
    start_date = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
    end_date = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None
    
    query = select(Defect).where(Defect.machine_id.in_(machine_model_map.keys()))
    if start_date:
        query = query.where(Defect.occurred_at >= start_date)
    if end_date:
        query = query.where(Defect.occurred_at <= end_date)
    if defect_types:
        query = query.where(Defect.defect_type.in_(defect_types))
    
    result = await session.execute(query)
    defects = result.scalars().all()
    
    # 機種ごと・種別ごとに集計
    model_type_counts = defaultdict(lambda: defaultdict(int))
    all_types = set()
    
    for defect in defects:
        model = machine_model_map.get(defect.machine_id, "不明")
        model_type_counts[model][defect.defect_type] += 1
        all_types.add(defect.defect_type)
    
    columns = sorted(all_types)
    rows = []
    
    for model in sorted(model_type_counts.keys()):
        row = {"model": model}
        for dtype in columns:
            row[dtype] = model_type_counts[model].get(dtype, 0)
        row["total"] = sum(model_type_counts[model].values())
        rows.append(row)
    
    return {
        "columns": columns,
        "rows": rows,
    }


async def get_defect_machines(
    session: AsyncSession,
    series: str | None = None,
    models: list[str] | None = None,
    date_from: str = None,
    date_to: str = None,
    defect_types: list[str] | None = None,
    target_period: str | None = None,
    target_defect_type: str | None = None,
) -> dict[str, Any]:
    """
    不具合発生機番リストを取得
    
    Returns:
        {
            "machines": [
                {"machine_id": "...", "model": "...", "defect_type": "...", "count": 1, "firmware_version": "..."},
                ...
            ],
            "total_count": 100,
            "filter_info": {...} or None
        }
    """
    from datetime import datetime
    from collections import defaultdict
    from app.models import Defect
    
    # 対象機番を取得
    machine_query = select(Machine.id, Machine.model_id, Machine.firmware_version)
    if models and len(models) > 0:
        machine_query = machine_query.where(Machine.model_id.in_(models))
    elif series:
        model_ids = await get_models(session, series)
        machine_query = machine_query.where(Machine.model_id.in_(model_ids))
    
    machine_result = await session.execute(machine_query)
    machine_info = {row[0]: {"model": row[1], "firmware_version": row[2]} for row in machine_result.all()}
    
    if not machine_info:
        return {"machines": [], "total_count": 0, "filter_info": None}
    
    # 不具合データを取得
    start_date = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
    end_date = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None
    
    query = select(Defect).where(Defect.machine_id.in_(machine_info.keys()))
    if start_date:
        query = query.where(Defect.occurred_at >= start_date)
    if end_date:
        query = query.where(Defect.occurred_at <= end_date)
    
    # グラフクリック時のフィルター
    if target_period and target_defect_type:
        if len(target_period) == 7:  # YYYY-MM
            query = query.where(func.strftime("%Y-%m", Defect.occurred_at) == target_period)
        else:  # YYYY-MM-DD
            query = query.where(Defect.occurred_at == datetime.strptime(target_period, "%Y-%m-%d").date())
        query = query.where(Defect.defect_type == target_defect_type)
    elif defect_types:
        query = query.where(Defect.defect_type.in_(defect_types))
    
    result = await session.execute(query)
    defects = result.scalars().all()
    
    # 機番×種別ごとに集計
    machine_defects = defaultdict(lambda: defaultdict(int))
    machine_fw = {}
    
    for defect in defects:
        key = (defect.machine_id, defect.defect_type)
        machine_defects[defect.machine_id][defect.defect_type] += 1
        # 不具合レコードにFWバージョンがあればそれを使用
        if defect.firmware_version:
            machine_fw[defect.machine_id] = defect.firmware_version
        elif defect.machine_id in machine_info:
            machine_fw[defect.machine_id] = machine_info[defect.machine_id].get("firmware_version")
    
    machines = []
    for machine_id, type_counts in machine_defects.items():
        info = machine_info.get(machine_id, {})
        for defect_type, count in type_counts.items():
            machines.append({
                "machine_id": machine_id,
                "model": info.get("model", "不明"),
                "defect_type": defect_type,
                "count": count,
                "firmware_version": machine_fw.get(machine_id, "-"),
                "period": target_period,
            })
    
    # 件数でソート
    machines.sort(key=lambda x: x["count"], reverse=True)
    
    filter_info = None
    if target_period and target_defect_type:
        filter_info = {
            "period": target_period,
            "defect_type": target_defect_type,
        }
    
    return {
        "machines": machines,
        "total_count": len(machines),
        "filter_info": filter_info,
    }



