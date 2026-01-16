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
    機番は8桁（例: 65010001）
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
            
            # 8桁の機番を生成（例: 65010001 〜 65019999）
            machines = []
            # プレフィックス部分: A=65, B=66, C=67
            prefix_num = 65 + (ord(prefix) - ord("A"))
            base_num = prefix_num * 1000000 + model_num * 10000
            
            for machine_num in range(1, config["machines_per_model"] + 1):
                machine_id = str(base_num + machine_num).zfill(8)
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

