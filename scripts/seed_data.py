"""
初期データ投入スクリプト

マスターデータ（シリーズ、機種、カテゴリー、特性値、集計方法）をデータベースに投入。
"""

import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker, init_db
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


async def seed_master_data(session: AsyncSession) -> None:
    """マスターデータを投入"""
    
    # シリーズ
    series_data = [
        Series(id="SERIES-1", name="SERIES-1"),
        Series(id="SERIES-2", name="SERIES-2"),
        Series(id="SERIES-3", name="SERIES-3"),
    ]
    session.add_all(series_data)
    
    # 機種番号
    models_data = [
        # SERIES-1: A-1, A-2, A-3
        Model(id="A-1", series_id="SERIES-1", name="A-1"),
        Model(id="A-2", series_id="SERIES-1", name="A-2"),
        Model(id="A-3", series_id="SERIES-1", name="A-3"),
        # SERIES-2: B-1, B-2
        Model(id="B-1", series_id="SERIES-2", name="B-1"),
        Model(id="B-2", series_id="SERIES-2", name="B-2"),
        # SERIES-3: C-1 ~ C-5
        Model(id="C-1", series_id="SERIES-3", name="C-1"),
        Model(id="C-2", series_id="SERIES-3", name="C-2"),
        Model(id="C-3", series_id="SERIES-3", name="C-3"),
        Model(id="C-4", series_id="SERIES-3", name="C-4"),
        Model(id="C-5", series_id="SERIES-3", name="C-5"),
    ]
    session.add_all(models_data)
    
    # カテゴリーと特性値
    categories_data = [
        Category(id="生産時データ", name="生産時データ"),
        Category(id="稼働時データ", name="稼働時データ"),
    ]
    session.add_all(categories_data)
    
    characteristics_data = [
        Characteristic(id="生産時データ_特性値ID1", category_id="生産時データ", name="特性値ID1"),
        Characteristic(id="生産時データ_特性値ID2", category_id="生産時データ", name="特性値ID2"),
        Characteristic(id="生産時データ_特性値ID3", category_id="生産時データ", name="特性値ID3"),
        Characteristic(id="稼働時データ_特性値ID1", category_id="稼働時データ", name="特性値ID1"),
        Characteristic(id="稼働時データ_特性値ID2", category_id="稼働時データ", name="特性値ID2"),
        Characteristic(id="稼働時データ_特性値ID3", category_id="稼働時データ", name="特性値ID3"),
    ]
    session.add_all(characteristics_data)
    
    # 集計方法
    aggregations_data = [
        Aggregation(id="平均値", name="平均値"),
        Aggregation(id="最大値", name="最大値"),
        Aggregation(id="最小値", name="最小値"),
        Aggregation(id="合計値", name="合計値"),
        Aggregation(id="カウント", name="カウント"),
    ]
    session.add_all(aggregations_data)
    
    await session.commit()
    print("マスターデータを投入しました")


async def seed_machines(session: AsyncSession, machines_per_model: int = 100) -> None:
    """機番データを投入（サンプル数を指定可能）"""
    
    base_date = datetime(2026, 1, 1)
    months = []
    for i in range(24):
        d = base_date - timedelta(days=i * 30)
        months.append(d.strftime("%Y-%m"))
    
    models_config = {
        "A-1": 1, "A-2": 2, "A-3": 3,
        "B-1": 1, "B-2": 2,
        "C-1": 1, "C-2": 2, "C-3": 3, "C-4": 4, "C-5": 5,
    }
    
    machines = []
    for model_id, model_num in models_config.items():
        for i in range(1, machines_per_model + 1):
            machine_id = f"{model_id}-{i:06d}"
            
            # 製造月と稼働開始月を決定
            random.seed(hash(machine_id))
            machine_num = i % 10000
            mfg_idx = 6 + (machine_num % 18)
            op_idx = machine_num % mfg_idx if mfg_idx > 0 else 0
            
            machines.append(Machine(
                id=machine_id,
                model_id=model_id,
                manufacture_month=months[mfg_idx],
                operation_start_month=months[op_idx],
            ))
    
    session.add_all(machines)
    await session.commit()
    print(f"{len(machines)}件の機番データを投入しました")


async def main():
    """メイン処理"""
    print("データベースを初期化中...")
    await init_db()
    
    async with async_session_maker() as session:
        print("マスターデータを投入中...")
        await seed_master_data(session)
        
        print("機番データを投入中...")
        await seed_machines(session, machines_per_model=100)  # サンプルとして100件/機種
    
    print("初期データ投入が完了しました")


if __name__ == "__main__":
    asyncio.run(main())
