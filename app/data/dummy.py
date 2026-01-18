"""
ダミーデータモジュール

機種シリーズ、機種番号、機番、特性値データを生成する。
将来的にはデータベースからの取得に置き換える。
"""

import random
from datetime import datetime, timedelta
from typing import Any

# 機種シリーズ
SERIES_LIST = ["SERIES-1", "SERIES-2", "SERIES-3"]

# 利用可能な月リスト（24ヶ月分）
_AVAILABLE_MONTHS: list[str] = []

def _init_months() -> list[str]:
    """過去24ヶ月分の月リストを生成（初期化時に一度だけ実行）"""
    global _AVAILABLE_MONTHS
    if not _AVAILABLE_MONTHS:
        base_date = datetime(2026, 1, 1)
        for i in range(24):
            d = base_date - timedelta(days=i * 30)
            _AVAILABLE_MONTHS.append(d.strftime("%Y-%m"))
    return _AVAILABLE_MONTHS

_init_months()


def _generate_models_and_machines() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """
    機種番号と機番を動的に生成
    SERIES-1: 3機種, SERIES-2: 2機種, SERIES-3: 5機種
    機番は「機種番号-6桁数字」形式（例: A-1-000001）
    合計約100,000件
    """
    models_by_series: dict[str, list[str]] = {}
    machines_by_model: dict[str, list[str]] = {}
    
    # 各シリーズの設定
    series_config = {
        "SERIES-1": {"prefix": "A", "model_count": 3, "machines_per_model": 10000},
        "SERIES-2": {"prefix": "B", "model_count": 2, "machines_per_model": 10000},
        "SERIES-3": {"prefix": "C", "model_count": 5, "machines_per_model": 10000},
    }
    # 合計: 3*10000 + 2*10000 + 5*10000 = 100,000件
    
    for series in SERIES_LIST:
        config = series_config[series]
        prefix = config["prefix"]
        models = []
        
        for model_num in range(1, config["model_count"] + 1):
            model_id = f"{prefix}-{model_num}"
            models.append(model_id)
            
            # 機番を「機種番号-6桁数字」形式で生成（例: A-1-000001）
            machines = []
            for machine_num in range(1, config["machines_per_model"] + 1):
                machine_id = f"{model_id}-{machine_num:06d}"
                machines.append(machine_id)
            
            machines_by_model[model_id] = machines
        
        models_by_series[series] = models
    
    return models_by_series, machines_by_model


# 機種番号と機番を動的生成
MODELS_BY_SERIES, MACHINES_BY_MODEL = _generate_models_and_machines()

# データカテゴリー
DATA_CATEGORIES = ["生産時データ", "稼働時データ"]

# 特性値ID（カテゴリーごと）
CHARACTERISTIC_IDS: dict[str, list[str]] = {
    "生産時データ": ["特性値ID1", "特性値ID2", "特性値ID3"],
    "稼働時データ": ["特性値ID1", "特性値ID2", "特性値ID3"],
}

# 集計方法
AGGREGATION_METHODS = ["平均値", "最大値", "最小値", "合計値", "カウント"]


def get_available_months() -> list[str]:
    """過去24ヶ月分の月リストを取得"""
    return _AVAILABLE_MONTHS


# 機番の詳細情報（遅延生成でメモリ効率化）
_machine_details_cache: dict[str, dict[str, Any]] = {}

def _get_machine_detail(machine_id: str, model: str, series: str) -> dict[str, Any]:
    """
    機番の詳細情報を取得（キャッシュ付き）
    製造月・稼働開始月は24ヶ月に均等分布するよう割り当て
    """
    if machine_id in _machine_details_cache:
        return _machine_details_cache[machine_id]
    
    months = _AVAILABLE_MONTHS
    
    # 機番IDから決定論的にインデックスを計算（均等分布）
    # 新フォーマット（A-1-000001）から末尾の数字部分を抽出
    parts = machine_id.split("-")
    if len(parts) >= 3:
        machine_num = int(parts[-1])
    else:
        # 旧フォーマット対応（8桁数字）
        machine_num = int(machine_id) % 10000
    
    # 製造月: 機番を18で割った余りでインデックス決定（6〜23の範囲で均等分布）
    mfg_idx = 6 + (machine_num % 18)
    
    # 稼働開始月: 製造月より後（0〜mfg_idx-1の範囲で均等分布）
    op_idx = machine_num % mfg_idx if mfg_idx > 0 else 0
    
    detail = {
        "machine_id": machine_id,
        "model": model,
        "series": series,
        "manufacture_month": months[mfg_idx],
        "operation_start_month": months[op_idx],
    }
    _machine_details_cache[machine_id] = detail
    return detail


def get_series_list() -> list[str]:
    """機種シリーズ一覧を取得"""
    return SERIES_LIST


def get_models_by_series(series: str) -> list[str]:
    """シリーズに紐づく機種番号一覧を取得"""
    return MODELS_BY_SERIES.get(series, [])


def get_machines_by_model(model: str) -> list[str]:
    """機種番号に紐づく機番一覧を取得"""
    return MACHINES_BY_MODEL.get(model, [])


def get_all_machines_by_series(series: str) -> list[str]:
    """シリーズに紐づく全機番を取得"""
    machines = []
    for model in MODELS_BY_SERIES.get(series, []):
        machines.extend(MACHINES_BY_MODEL.get(model, []))
    return machines


def get_data_categories() -> list[str]:
    """データカテゴリー一覧を取得"""
    return DATA_CATEGORIES


def get_characteristic_ids(category: str) -> list[str]:
    """カテゴリーに紐づく特性値ID一覧を取得"""
    return CHARACTERISTIC_IDS.get(category, [])


def get_aggregation_methods() -> list[str]:
    """集計方法一覧を取得"""
    return AGGREGATION_METHODS


def search_machines(
    series: str | None = None,
    models: list[str] | None = None,
    manufacture_month_from: str | None = None,
    manufacture_month_to: str | None = None,
    operation_start_month_from: str | None = None,
    operation_start_month_to: str | None = None,
) -> list[dict[str, Any]]:
    """条件に合致する機番を検索（月は範囲指定対応、機種番号は複数選択対応）"""
    results = []
    
    # 検索対象のモデルを絞り込み
    target_series = [series] if series else SERIES_LIST
    
    for s in target_series:
        # 機種番号フィルター（複数選択対応）
        if models and len(models) > 0:
            target_models = [m for m in models if m in MODELS_BY_SERIES.get(s, [])]
        else:
            target_models = MODELS_BY_SERIES.get(s, [])
        
        for m in target_models:
            if m not in MODELS_BY_SERIES.get(s, []):
                continue
                
            machines = MACHINES_BY_MODEL.get(m, [])
            
            for machine_id in machines:
                details = _get_machine_detail(machine_id, m, s)
                
                # 製造月の範囲フィルター
                mfg_month = details["manufacture_month"]
                if manufacture_month_from and mfg_month < manufacture_month_from:
                    continue
                if manufacture_month_to and mfg_month > manufacture_month_to:
                    continue
                
                # 稼働開始月の範囲フィルター
                op_month = details["operation_start_month"]
                if operation_start_month_from and op_month < operation_start_month_from:
                    continue
                if operation_start_month_to and op_month > operation_start_month_to:
                    continue
                
                results.append(details)
    
    return results


def random_sample_machines(
    machines: list[dict[str, Any]], sample_size: int
) -> list[dict[str, Any]]:
    """機番リストからランダムサンプリング"""
    if sample_size >= len(machines):
        return machines
    return random.sample(machines, sample_size)


def generate_timeseries_data(
    machine_ids: list[str],
    category: str,
    characteristic_id: str,
    aggregation: str,
    months: int = 12,
) -> dict[str, Any]:
    """
    時系列データを生成
    集計方法によって結果が異なるように、月ごとに複数の生データを生成して集計
    
    Returns:
        {
            "labels": ["2025-02", "2025-03", ...],
            "datasets": [
                {"machine_id": "65010001", "data": [10.5, 12.3, ...]},
                ...
            ]
        }
    """
    base_date = datetime(2026, 1, 1)
    labels = []
    for i in range(months - 1, -1, -1):
        d = base_date - timedelta(days=i * 30)
        labels.append(d.strftime("%Y-%m"))
    
    datasets = []
    for machine_id in machine_ids:
        # シード値を設定して再現性を確保
        seed = hash(f"{machine_id}_{category}_{characteristic_id}")
        random.seed(seed)
        
        base_value = random.uniform(50, 150)
        data = []
        
        for month_idx in range(months):
            # 月ごとに5〜15個の生データを生成（日次データをシミュレート）
            raw_count = random.randint(5, 15)
            raw_values = []
            
            for _ in range(raw_count):
                # トレンドとノイズを加える
                value = base_value + random.uniform(-30, 30)
                raw_values.append(value)
            
            # 集計方法に応じて結果を計算
            if aggregation == "平均値":
                result = sum(raw_values) / len(raw_values)
            elif aggregation == "最大値":
                result = max(raw_values)
            elif aggregation == "最小値":
                result = min(raw_values)
            elif aggregation == "合計値":
                result = sum(raw_values)
            elif aggregation == "カウント":
                result = len(raw_values)
            else:
                result = sum(raw_values) / len(raw_values)
            
            # ベース値を少し変動させる（トレンド）
            base_value += random.uniform(-5, 5)
            
            data.append(round(result, 2))
        
        datasets.append({"machine_id": machine_id, "data": data})
    
    random.seed()  # シードをリセット
    return {"labels": labels, "datasets": datasets}


def generate_histogram_data(
    model: str,
    category: str,
    characteristic_id: str,
    aggregation: str,
    target_month: str,
    selected_machine_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    断面データ（ヒストグラム用）を生成
    集計方法によって結果が異なるように、機番ごとに複数の生データを生成して集計
    
    Returns:
        {
            "bins": [0, 20, 40, 60, 80, 100, 120],
            "selected_group": {"label": "選択機番", "counts": [1, 2, 3, ...]},
            "other_group": {"label": "その他", "counts": [2, 1, 4, ...]},
        }
    """
    machines = MACHINES_BY_MODEL.get(model, [])
    
    # 各機番の値を生成
    all_values = []
    selected_values = []
    other_values = []
    
    for machine_id in machines:
        seed = hash(f"{machine_id}_{category}_{characteristic_id}_{target_month}")
        random.seed(seed)
        
        # 機番ごとに3〜10個の生データを生成（センサー読み取り値をシミュレート）
        raw_count = random.randint(3, 10)
        base_value = random.uniform(40, 100)
        raw_values = []
        
        for _ in range(raw_count):
            # ノイズを加える（±25の範囲）
            value = base_value + random.uniform(-25, 25)
            raw_values.append(value)
        
        # 集計方法に応じて結果を計算
        if aggregation == "平均値":
            result = sum(raw_values) / len(raw_values)
        elif aggregation == "最大値":
            result = max(raw_values)
        elif aggregation == "最小値":
            result = min(raw_values)
        elif aggregation == "合計値":
            result = sum(raw_values)
        elif aggregation == "カウント":
            result = len(raw_values)
        else:
            result = sum(raw_values) / len(raw_values)
        
        all_values.append({"machine_id": machine_id, "value": round(result, 2)})
        
        if selected_machine_ids and machine_id in selected_machine_ids:
            selected_values.append(result)
        else:
            other_values.append(result)
    
    random.seed()
    
    # ビン設定（集計方法によって範囲を調整）
    if aggregation == "合計値":
        bins = [0, 100, 200, 300, 400, 500, 600, 700, 800]
    elif aggregation == "カウント":
        bins = [0, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    else:
        bins = [0, 20, 40, 60, 80, 100, 120, 140]
    
    def count_in_bins(values: list[float]) -> list[int]:
        counts = [0] * (len(bins) - 1)
        for v in values:
            for i in range(len(bins) - 1):
                if bins[i] <= v < bins[i + 1]:
                    counts[i] += 1
                    break
            # 最後のビンより大きい場合は最後のビンに入れる
            if v >= bins[-1]:
                counts[-1] += 1
        return counts
    
    result_data: dict[str, Any] = {
        "bins": bins,
        "raw_data": all_values,
    }
    
    if selected_machine_ids:
        result_data["selected_group"] = {
            "label": "選択機番",
            "counts": count_in_bins(selected_values),
        }
        result_data["other_group"] = {
            "label": "その他",
            "counts": count_in_bins(other_values),
        }
    else:
        result_data["all_group"] = {
            "label": "全機番",
            "counts": count_in_bins([v["value"] for v in all_values]),
        }
    
    return result_data


def generate_multi_timeseries_data(
    machine_ids: list[str],
    variables: list[dict[str, str]],
    aggregation: str,
    x_axis_type: str = "time",
    months: int = 12,
) -> dict[str, Any]:
    """
    多変量時系列データを生成（マルチY軸対応）
    
    Args:
        machine_ids: 機番リスト
        variables: [{"category": "...", "characteristic_id": "...", "axis": "left|right"}]
        aggregation: 集計方法
        x_axis_type: "time" (月次) or "usage" (使用回数)
        months: 月数
    
    Returns:
        {
            "labels": ["2025-02", "2025-03", ...] or ["100", "200", ...],
            "datasets": [...],
            "scales": {...},
            "x_axis_type": "time" or "usage"
        }
    """
    base_date = datetime(2026, 1, 1)
    
    # X軸ラベルを生成
    if x_axis_type == "usage":
        # 使用回数ベース（0〜1000回を12分割）
        labels = [str(i * 100) for i in range(months)]
    else:
        # 時間ベース（月次）
        labels = []
        for i in range(months - 1, -1, -1):
            d = base_date - timedelta(days=i * 30)
            labels.append(d.strftime("%Y-%m"))
    
    datasets = []
    left_values: list[float] = []
    right_values: list[float] = []
    
    for machine_id in machine_ids:
        for var in variables:
            category = var.get("category", "")
            char_id = var.get("characteristic_id", "")
            axis = var.get("axis", "left")
            
            # シード値を設定して再現性を確保
            seed = hash(f"{machine_id}_{category}_{char_id}_{x_axis_type}")
            random.seed(seed)
            
            # 特性値ごとに異なる基準値を設定
            char_base = {"特性値ID1": 100, "特性値ID2": 300, "特性値ID3": 50}
            base_value = char_base.get(char_id, random.uniform(50, 150))
            
            data = []
            for idx in range(months):
                raw_count = random.randint(5, 15)
                raw_values = [base_value + random.uniform(-30, 30) for _ in range(raw_count)]
                
                if aggregation == "平均値":
                    result = sum(raw_values) / len(raw_values)
                elif aggregation == "最大値":
                    result = max(raw_values)
                elif aggregation == "最小値":
                    result = min(raw_values)
                elif aggregation == "合計値":
                    result = sum(raw_values)
                elif aggregation == "カウント":
                    result = len(raw_values)
                else:
                    result = sum(raw_values) / len(raw_values)
                
                # 使用回数モードでは劣化傾向を表現
                if x_axis_type == "usage":
                    degradation = idx * random.uniform(0.5, 2.0)
                    base_value += degradation
                else:
                    base_value += random.uniform(-5, 5)
                    
                data.append(round(result, 2))
            
            datasets.append({
                "machine_id": machine_id,
                "variable": {"category": category, "characteristic_id": char_id},
                "axis": axis,
                "data": data,
            })
            
            # スケール計算用
            if axis == "left":
                left_values.extend(data)
            else:
                right_values.extend(data)
    
    random.seed()
    
    # スケール情報
    scales = {}
    if left_values:
        scales["left"] = {
            "min": 0,
            "max": max(left_values) * 1.2,
            "label": variables[0].get("characteristic_id", ""),
        }
    if right_values:
        right_vars = [v for v in variables if v.get("axis") == "right"]
        scales["right"] = {
            "min": 0,
            "max": max(right_values) * 1.2,
            "label": right_vars[0].get("characteristic_id", "") if right_vars else "",
        }
    
    return {
        "labels": labels,
        "datasets": datasets, 
        "scales": scales,
        "x_axis_type": x_axis_type,
    }


def generate_scatter_data(
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
    散布図データを生成
    
    Returns:
        {
            "data": [
                {"machine_id": "65010001", "x": 50.5, "y": 120.3, "selected": true},
                ...
            ],
            "x_label": "特性値ID1",
            "y_label": "特性値ID2",
            "correlation": 0.75
        }
    """
    machines = MACHINES_BY_MODEL.get(model, [])
    data = []
    
    x_values = []
    y_values = []
    
    for machine_id in machines:
        # X軸の値
        seed_x = hash(f"{machine_id}_{x_category}_{x_characteristic_id}_{target_month}")
        random.seed(seed_x)
        raw_count = random.randint(3, 10)
        base_x = random.uniform(40, 100)
        raw_x = [base_x + random.uniform(-25, 25) for _ in range(raw_count)]
        
        if aggregation == "平均値":
            x_val = sum(raw_x) / len(raw_x)
        elif aggregation == "最大値":
            x_val = max(raw_x)
        elif aggregation == "最小値":
            x_val = min(raw_x)
        elif aggregation == "合計値":
            x_val = sum(raw_x)
        elif aggregation == "カウント":
            x_val = len(raw_x)
        else:
            x_val = sum(raw_x) / len(raw_x)
        
        # Y軸の値（X軸と相関を持たせる）
        seed_y = hash(f"{machine_id}_{y_category}_{y_characteristic_id}_{target_month}")
        random.seed(seed_y)
        base_y = x_val * 1.5 + random.uniform(-20, 20)  # 相関を持たせる
        raw_y = [base_y + random.uniform(-15, 15) for _ in range(raw_count)]
        
        if aggregation == "平均値":
            y_val = sum(raw_y) / len(raw_y)
        elif aggregation == "最大値":
            y_val = max(raw_y)
        elif aggregation == "最小値":
            y_val = min(raw_y)
        elif aggregation == "合計値":
            y_val = sum(raw_y)
        elif aggregation == "カウント":
            y_val = len(raw_y)
        else:
            y_val = sum(raw_y) / len(raw_y)
        
        is_selected = selected_machine_ids and machine_id in selected_machine_ids
        
        data.append({
            "machine_id": machine_id,
            "x": round(x_val, 2),
            "y": round(y_val, 2),
            "selected": is_selected,
        })
        
        x_values.append(x_val)
        y_values.append(y_val)
    
    random.seed()
    
    # 相関係数を計算
    n = len(x_values)
    if n > 1:
        mean_x = sum(x_values) / n
        mean_y = sum(y_values) / n
        cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values)) / n
        std_x = (sum((x - mean_x) ** 2 for x in x_values) / n) ** 0.5
        std_y = (sum((y - mean_y) ** 2 for y in y_values) / n) ** 0.5
        correlation = cov / (std_x * std_y) if std_x > 0 and std_y > 0 else 0
    else:
        correlation = 0
    
    return {
        "data": data,
        "x_label": x_characteristic_id,
        "y_label": y_characteristic_id,
        "correlation": round(correlation, 3),
    }


def generate_boxplot_data(
    models: list[str],
    category: str,
    characteristic_id: str,
    aggregation: str,
    target_month: str,
) -> dict[str, Any]:
    """
    箱ひげ図データを生成
    
    Returns:
        {
            "labels": ["A-1", "A-2", "A-3"],
            "datasets": [
                {
                    "label": "分布",
                    "data": [
                        {"min": 20, "q1": 40, "median": 60, "q3": 80, "max": 100, "outliers": [5, 110]},
                        ...
                    ]
                }
            ]
        }
    """
    labels = []
    boxplot_data = []
    
    for model in models:
        machines = MACHINES_BY_MODEL.get(model, [])
        values = []
        
        for machine_id in machines:
            seed = hash(f"{machine_id}_{category}_{characteristic_id}_{target_month}")
            random.seed(seed)
            
            raw_count = random.randint(3, 10)
            base_value = random.uniform(40, 100)
            raw_values = [base_value + random.uniform(-25, 25) for _ in range(raw_count)]
            
            if aggregation == "平均値":
                result = sum(raw_values) / len(raw_values)
            elif aggregation == "最大値":
                result = max(raw_values)
            elif aggregation == "最小値":
                result = min(raw_values)
            elif aggregation == "合計値":
                result = sum(raw_values)
            elif aggregation == "カウント":
                result = len(raw_values)
            else:
                result = sum(raw_values) / len(raw_values)
            
            values.append(result)
        
        if not values:
            continue
        
        # 統計値を計算
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        
        q1 = sorted_values[q1_idx]
        median = sorted_values[n // 2]
        q3 = sorted_values[q3_idx]
        iqr = q3 - q1
        
        # 外れ値判定
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        
        outliers = [v for v in sorted_values if v < lower_fence or v > upper_fence]
        non_outliers = [v for v in sorted_values if lower_fence <= v <= upper_fence]
        
        labels.append(model)
        boxplot_data.append({
            "min": round(min(non_outliers) if non_outliers else sorted_values[0], 2),
            "q1": round(q1, 2),
            "median": round(median, 2),
            "q3": round(q3, 2),
            "max": round(max(non_outliers) if non_outliers else sorted_values[-1], 2),
            "outliers": [round(v, 2) for v in outliers],
        })
    
    random.seed()
    
    return {
        "labels": labels,
        "datasets": [
            {
                "label": f"{category} - {characteristic_id}",
                "data": boxplot_data,
            }
        ],
    }


def generate_distribution_boxplot_data(
    model: str,
    x_axis_type: str,
    bin_method: str,
    bin_count: int,
    category: str,
    characteristic_id: str,
    aggregation: str,
    selected_machine_ids: list[str] | None = None,
    chart_type: str = "boxplot",
) -> dict[str, Any]:
    """
    分布傾向データを生成（2群比較・箱ひげ図/折れ線グラフ対応）
    
    Args:
        model: 機種番号
        x_axis_type: "usage" | "mfg_month"
        bin_method: "equal_width" | "quantile"
        bin_count: ビン数
        category: データカテゴリー
        characteristic_id: 特性値ID
        aggregation: 集計方法
        selected_machine_ids: 選択機番リスト（2群比較用）
        chart_type: "boxplot" | "line"
    
    Returns:
        箱ひげ図または折れ線グラフ用のデータ
    """
    machines = MACHINES_BY_MODEL.get(model, [])
    if not machines:
        return {"labels": [], "datasets": [], "x_axis_label": ""}
    
    # 選択機番セット
    selected_set = set(selected_machine_ids) if selected_machine_ids else set()
    
    # 各機番のX軸値とY軸値を収集
    data_points: list[dict[str, Any]] = []
    
    for machine_id in machines:
        # X軸の値を取得
        if x_axis_type == "usage":
            seed = hash(f"{machine_id}_usage")
            random.seed(seed)
            x_value = random.randint(0, 1000)
        else:  # mfg_month
            parts = machine_id.split("-")
            if len(parts) >= 3:
                machine_num = int(parts[-1])
            else:
                machine_num = int(machine_id) % 10000
            mfg_idx = 6 + (machine_num % 18)
            x_value = mfg_idx
        
        # Y軸の値（特徴量）を取得
        seed = hash(f"{machine_id}_{category}_{characteristic_id}")
        random.seed(seed)
        raw_count = random.randint(3, 10)
        base_value = random.uniform(40, 100)
        raw_values = [base_value + random.uniform(-25, 25) for _ in range(raw_count)]
        
        if aggregation == "平均値":
            y_value = sum(raw_values) / len(raw_values)
        elif aggregation == "最大値":
            y_value = max(raw_values)
        elif aggregation == "最小値":
            y_value = min(raw_values)
        elif aggregation == "合計値":
            y_value = sum(raw_values)
        elif aggregation == "カウント":
            y_value = len(raw_values)
        else:
            y_value = sum(raw_values) / len(raw_values)
        
        is_selected = machine_id in selected_set
        data_points.append({"x": x_value, "y": y_value, "machine_id": machine_id, "selected": is_selected})
    
    random.seed()
    
    # X軸の値でビン分割
    x_values = [d["x"] for d in data_points]
    
    if x_axis_type == "mfg_month":
        # 降順ソート（インデックス大=古い月が先）→ 左が古く右が新しい順
        unique_months = sorted(set(x_values), reverse=True)
        labels = [_AVAILABLE_MONTHS[m] if m < len(_AVAILABLE_MONTHS) else f"Month-{m}" for m in unique_months]
        bin_keys = unique_months
        
        # 各月のデータをグループ化
        if selected_set:
            binned_selected: dict[int, list[float]] = {m: [] for m in unique_months}
            binned_other: dict[int, list[float]] = {m: [] for m in unique_months}
            for d in data_points:
                if d["selected"]:
                    binned_selected[d["x"]].append(d["y"])
                else:
                    binned_other[d["x"]].append(d["y"])
        else:
            binned_all: dict[int, list[float]] = {m: [] for m in unique_months}
            for d in data_points:
                binned_all[d["x"]].append(d["y"])
    else:
        # 使用回数の場合はビン分割
        min_x, max_x = min(x_values), max(x_values)
        
        if bin_method == "quantile":
            sorted_x = sorted(x_values)
            n = len(sorted_x)
            bin_edges = []
            for i in range(bin_count + 1):
                idx = int(i * n / bin_count)
                if idx >= n:
                    idx = n - 1
                bin_edges.append(sorted_x[idx])
            bin_edges = sorted(set(bin_edges))
            if len(bin_edges) < 2:
                bin_edges = [min_x, max_x]
        else:
            step = (max_x - min_x) / bin_count if max_x > min_x else 1
            bin_edges = [min_x + i * step for i in range(bin_count + 1)]
        
        labels = [f"{int(bin_edges[i])}-{int(bin_edges[i+1])}" for i in range(len(bin_edges) - 1)]
        bin_keys = list(range(len(bin_edges) - 1))
        
        # 各ビンのデータをグループ化
        if selected_set:
            binned_selected = {i: [] for i in bin_keys}
            binned_other = {i: [] for i in bin_keys}
            for d in data_points:
                for i in range(len(bin_edges) - 1):
                    if bin_edges[i] <= d["x"] < bin_edges[i + 1]:
                        if d["selected"]:
                            binned_selected[i].append(d["y"])
                        else:
                            binned_other[i].append(d["y"])
                        break
                else:
                    if len(bin_edges) > 1:
                        if d["selected"]:
                            binned_selected[len(bin_edges) - 2].append(d["y"])
                        else:
                            binned_other[len(bin_edges) - 2].append(d["y"])
        else:
            binned_all = {i: [] for i in bin_keys}
            for d in data_points:
                for i in range(len(bin_edges) - 1):
                    if bin_edges[i] <= d["x"] < bin_edges[i + 1]:
                        binned_all[i].append(d["y"])
                        break
                else:
                    if len(bin_edges) > 1:
                        binned_all[len(bin_edges) - 2].append(d["y"])
    
    x_axis_label = "使用回数" if x_axis_type == "usage" else "製造月"
    
    def calc_stats(values: list[float]) -> dict[str, Any]:
        """統計量を計算"""
        if not values:
            return {"mean": 0, "std": 0, "min": 0, "q1": 0, "median": 0, "q3": 0, "max": 0, "count": 0, "p2_5": 0, "p97_5": 0}
        n = len(values)
        sorted_v = sorted(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n if n > 1 else 0
        std = variance ** 0.5
        q1_idx, q3_idx = n // 4, (3 * n) // 4
        q1, median, q3 = sorted_v[q1_idx], sorted_v[n // 2], sorted_v[q3_idx]
        
        # 2.5%と97.5%パーセンタイル
        p2_5_idx = max(0, int(n * 0.025))
        p97_5_idx = min(n - 1, int(n * 0.975))
        p2_5 = sorted_v[p2_5_idx]
        p97_5 = sorted_v[p97_5_idx]
        
        iqr = q3 - q1
        lower_fence, upper_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = [v for v in sorted_v if v < lower_fence or v > upper_fence]
        non_outliers = [v for v in sorted_v if lower_fence <= v <= upper_fence]
        return {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": round(min(non_outliers) if non_outliers else sorted_v[0], 2),
            "q1": round(q1, 2),
            "median": round(median, 2),
            "q3": round(q3, 2),
            "max": round(max(non_outliers) if non_outliers else sorted_v[-1], 2),
            "outliers": [round(v, 2) for v in outliers],
            "count": n,
            "p2_5": round(p2_5, 2),
            "p97_5": round(p97_5, 2),
        }
    
    if chart_type == "line":
        # 折れ線グラフ用データ（平均＋標準偏差）
        if selected_set:
            selected_data = []
            other_data = []
            for i, key in enumerate(bin_keys):
                selected_data.append(calc_stats(binned_selected[key]))
                other_data.append(calc_stats(binned_other[key]))
            return {
                "labels": labels,
                "datasets": [
                    {"label": "選択機番群", "data": selected_data, "group": "selected"},
                    {"label": "その他", "data": other_data, "group": "other"},
                ],
                "x_axis_label": x_axis_label,
                "chart_type": "line",
            }
        else:
            all_data = [calc_stats(binned_all[key]) for key in bin_keys]
            return {
                "labels": labels,
                "datasets": [{"label": "全機番", "data": all_data, "group": "all"}],
                "x_axis_label": x_axis_label,
                "chart_type": "line",
            }
    else:
        # 箱ひげ図用データ
        if selected_set:
            selected_boxplot = []
            other_boxplot = []
            final_labels = []
            for i, key in enumerate(bin_keys):
                s_stats = calc_stats(binned_selected[key])
                o_stats = calc_stats(binned_other[key])
                if s_stats["count"] > 0 or o_stats["count"] > 0:
                    selected_boxplot.append(s_stats)
                    other_boxplot.append(o_stats)
                    final_labels.append(labels[i])
            return {
                "labels": final_labels,
                "datasets": [
                    {"label": "選択機番群", "data": selected_boxplot, "group": "selected"},
                    {"label": "その他", "data": other_boxplot, "group": "other"},
                ],
                "x_axis_label": x_axis_label,
                "chart_type": "boxplot",
            }
        else:
            boxplot_data = []
            final_labels = []
            for i, key in enumerate(bin_keys):
                stats = calc_stats(binned_all[key])
                if stats["count"] > 0:
                    boxplot_data.append(stats)
                    final_labels.append(labels[i])
            return {
                "labels": final_labels,
                "datasets": [{"label": f"{category} - {characteristic_id}", "data": boxplot_data, "group": "all"}],
                "x_axis_label": x_axis_label,
                "chart_type": "boxplot",
            }
