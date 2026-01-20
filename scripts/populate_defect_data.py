"""
サンプル不具合データをデータベースに投入するスクリプト
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
from app.models import Machine, Defect


DEFECT_TYPES = ["異音", "動作不良", "停止", "エラー表示", "部品破損"]
SEVERITIES = ["高", "中", "低"]


async def populate_defect_data():
    """サンプル不具合データを投入"""
    
    async with async_session_maker() as session:
        # 機番を取得
        result = await session.execute(select(Machine.id, Machine.firmware_version).limit(100))
        machines = [(row[0], row[1]) for row in result.all()]
        print(f"Found {len(machines)} machines")
        
        if not machines:
            print("No machines found. Please run seed script first.")
            return
        
        # 既存データをクリア
        await session.execute(Defect.__table__.delete())
        await session.flush()
        
        # 不具合データを生成（過去12ヶ月）
        base_date = datetime(2026, 1, 1)
        defect_count = 0
        
        for machine_id, firmware_version in machines:
            # 機番ごとにランダムな不具合を生成
            seed = hash(machine_id)
            random.seed(seed)
            
            # 5%の確率で不具合を持つ
            if random.random() < 0.3:
                # 1〜5件の不具合を生成
                num_defects = random.randint(1, 5)
                
                for _ in range(num_defects):
                    # 過去12ヶ月のランダムな日付
                    days_ago = random.randint(0, 365)
                    occurred_at = (base_date - timedelta(days=days_ago)).date()
                    
                    defect = Defect(
                        machine_id=machine_id,
                        defect_type=random.choice(DEFECT_TYPES),
                        occurred_at=occurred_at,
                        severity=random.choice(SEVERITIES),
                        firmware_version=firmware_version,
                        description=f"不具合発生: {machine_id}",
                    )
                    session.add(defect)
                    defect_count += 1
        
        await session.commit()
        print(f"Inserted {defect_count} defect records")
        random.seed()


if __name__ == "__main__":
    asyncio.run(populate_defect_data())
