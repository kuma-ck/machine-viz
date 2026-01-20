"""
サンプル時系列データをデータベースに投入するスクリプト
"""

import asyncio
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_maker
from app.models import Machine, Category, Characteristic, MachineData, Aggregation


async def populate_timeseries_data():
    """サンプル時系列データを投入"""
    
    async with async_session_maker() as session:
        # 機番を取得
        result = await session.execute(select(Machine.id).limit(100))
        machine_ids = [row[0] for row in result.all()]
        print(f"Found {len(machine_ids)} machines")
        
        # カテゴリと特性値を取得
        cat_result = await session.execute(select(Category))
        categories = cat_result.scalars().all()
        
        if not categories:
            print("No categories found. Creating sample categories...")
            # サンプルカテゴリを作成
            sample_categories = ["カテゴリー1", "カテゴリー2", "カテゴリー3"]
            for cat_id in sample_categories:
                category = Category(id=cat_id, name=cat_id)
                session.add(category)
            await session.flush()
            
            # 特性値を作成
            for cat_id in sample_categories:
                for i in range(1, 4):
                    char = Characteristic(
                        id=f"{cat_id}-char-{i}",
                        category_id=cat_id,
                        name=f"特性{i}"
                    )
                    session.add(char)
            await session.flush()
            
            # 集計方法を作成
            agg_result = await session.execute(select(Aggregation))
            if not agg_result.scalars().all():
                for agg in ["平均値", "最大値", "最小値", "合計値", "カウント"]:
                    session.add(Aggregation(id=agg, name=agg))
                await session.flush()
        
        # 特性値IDを取得
        char_result = await session.execute(select(Characteristic))
        characteristics = char_result.scalars().all()
        print(f"Found {len(characteristics)} characteristics")
        
        if not characteristics:
            print("No characteristics found. Please run seed script first.")
            return
        
        # 月ラベルを生成（過去12ヶ月）
        base_date = datetime(2026, 1, 1)
        months = []
        for i in range(11, -1, -1):
            d = base_date - timedelta(days=i * 30)
            months.append(d.strftime("%Y-%m"))
        
        # 既存データをクリア
        await session.execute(MachineData.__table__.delete())
        await session.flush()
        
        # 時系列データを生成
        aggregations = ["平均値", "最大値", "最小値"]
        data_count = 0
        
        for machine_id in machine_ids[:20]:  # 最初の20台のみ
            for char in characteristics[:3]:  # 最初の3つの特性値
                for agg in aggregations:
                    seed = hash(f"{machine_id}_{char.id}_{agg}")
                    random.seed(seed)
                    base_value = random.uniform(50, 150)
                    
                    for month in months:
                        value = base_value + random.uniform(-30, 30)
                        
                        machine_data = MachineData(
                            machine_id=machine_id,
                            characteristic_id=char.id,
                            month=month,
                            value=round(value, 2),
                            aggregation=agg,
                        )
                        session.add(machine_data)
                        data_count += 1
        
        await session.commit()
        print(f"Inserted {data_count} timeseries data records")
        random.seed()


if __name__ == "__main__":
    asyncio.run(populate_timeseries_data())
