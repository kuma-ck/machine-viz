"""
アノテーションデータモジュール

イベント情報（ファームウェア更新、部品交換、メンテナンス、エラー発生など）を生成する。
将来的にはデータベースからの取得に置き換える。
"""

import random
from datetime import datetime, timedelta
from typing import Any


# アノテーションタイプ
ANNOTATION_TYPES = [
    {"id": "firmware", "label": "ファームウェア更新", "color": "#3b82f6"},
    {"id": "parts", "label": "部品交換", "color": "#f59e0b"},
    {"id": "maintenance", "label": "メンテナンス", "color": "#10b981"},
    {"id": "error", "label": "エラー発生", "color": "#ef4444"},
]


def get_annotation_types() -> list[dict[str, str]]:
    """アノテーションタイプ一覧を取得"""
    return ANNOTATION_TYPES


def generate_machine_annotations(
    machine_ids: list[str],
    months: int = 12,
) -> list[dict[str, Any]]:
    """
    機番ごとのアノテーションを生成
    
    Returns:
        [
            {
                "date": "2025-08-15",
                "type": "firmware",
                "label": "ファームウェア更新",
                "description": "v2.1.0 へ更新",
                "machine_ids": ["65010001", "65010002"]
            },
            ...
        ]
    """
    base_date = datetime(2026, 1, 1)
    annotations = []
    
    # 共通イベント（全機番に影響）
    common_events = [
        {
            "date": (base_date - timedelta(days=60)).strftime("%Y-%m-%d"),
            "type": "firmware",
            "label": "ファームウェア更新",
            "description": "v2.1.0 へ更新",
            "machine_ids": machine_ids,
        },
        {
            "date": (base_date - timedelta(days=150)).strftime("%Y-%m-%d"),
            "type": "firmware",
            "label": "ファームウェア更新",
            "description": "v2.0.0 へ更新",
            "machine_ids": machine_ids,
        },
    ]
    annotations.extend(common_events)
    
    # 機番個別のイベント
    for machine_id in machine_ids:
        seed = hash(machine_id)
        random.seed(seed)
        
        # ランダムにイベントを生成
        num_events = random.randint(1, 4)
        
        for _ in range(num_events):
            days_ago = random.randint(30, months * 30)
            event_date = base_date - timedelta(days=days_ago)
            event_type = random.choice(["parts", "maintenance", "error"])
            
            type_info = next(t for t in ANNOTATION_TYPES if t["id"] == event_type)
            
            descriptions = {
                "parts": ["センサー交換", "モーター交換", "フィルター交換", "バルブ交換"],
                "maintenance": ["定期点検", "校正作業", "清掃作業", "調整作業"],
                "error": ["通信エラー", "高温警告", "振動異常", "圧力異常"],
            }
            
            annotations.append({
                "date": event_date.strftime("%Y-%m-%d"),
                "type": event_type,
                "label": type_info["label"],
                "description": random.choice(descriptions[event_type]),
                "machine_ids": [machine_id],
            })
    
    random.seed()
    
    # 日付順にソート
    annotations.sort(key=lambda x: x["date"])
    
    return annotations


def get_annotations_for_timeseries(
    machine_ids: list[str],
    months: int = 12,
) -> list[dict[str, Any]]:
    """
    時系列グラフ用のアノテーションを取得
    Chart.js annotation plugin形式で返す
    
    Returns:
        [
            {
                "type": "line",
                "xMin": "2025-08",
                "xMax": "2025-08",
                "borderColor": "#3b82f6",
                "borderWidth": 2,
                "label": {
                    "display": true,
                    "content": "FW更新 v2.1.0",
                    "position": "start"
                }
            },
            ...
        ]
    """
    raw_annotations = generate_machine_annotations(machine_ids, months)
    
    chart_annotations = []
    for ann in raw_annotations:
        # 日付を月形式に変換（時系列チャートの形式に合わせる）
        date_obj = datetime.strptime(ann["date"], "%Y-%m-%d")
        month_label = date_obj.strftime("%Y-%m")
        
        type_info = next((t for t in ANNOTATION_TYPES if t["id"] == ann["type"]), None)
        color = type_info["color"] if type_info else "#888888"
        
        # 機番情報をラベルに追加
        machine_info = ""
        if len(ann["machine_ids"]) == 1:
            # 単一機番の場合は機番を表示（末尾6桁のみ）
            mid = ann["machine_ids"][0]
            # A-1-000001 → 000001 のように末尾のみ
            short_id = mid.split("-")[-1] if "-" in mid else mid[-6:]
            machine_info = f"[{short_id}] "
        elif len(ann["machine_ids"]) > 1 and len(ann["machine_ids"]) < len(machine_ids):
            # 複数機番だが全てではない場合
            machine_info = f"[{len(ann['machine_ids'])}台] "
        # 全機番に共通の場合は表示しない（例：FW更新など）
        
        chart_annotations.append({
            "type": "line",
            "xMin": month_label,
            "xMax": month_label,
            "borderColor": color,
            "borderWidth": 2,
            "borderDash": [5, 5] if ann["type"] == "error" else [],
            "label": {
                "display": True,
                "content": f"{machine_info}{ann['description']}",
                "position": "start",
                "backgroundColor": color,
                "font": {"size": 10},
            },
            "raw": ann,  # 元データも含める
        })
    
    return chart_annotations
