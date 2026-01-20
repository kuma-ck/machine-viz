"""
既存の機番データにファームウェアバージョンとオプション構成を設定するスクリプト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update

from app.database import async_session_maker
from app.models import Machine


async def populate_firmware_and_options():
    """既存の機番にファームウェアバージョンとオプション構成を設定"""
    available_options = ["OP-A", "OP-B", "OP-C", "OP-D", "OP-E", "OP-F"]
    
    async with async_session_maker() as session:
        # 全機番を取得
        result = await session.execute(select(Machine))
        machines = result.scalars().all()
        
        print(f"Updating {len(machines)} machines...")
        
        for machine in machines:
            # 機番IDから決定論的に値を生成
            parts = machine.id.split("-")
            if len(parts) >= 3:
                machine_num = int(parts[-1])
            else:
                machine_num = hash(machine.id) % 10000
            
            # ファームウェアバージョン
            fw_major = 1 + (machine_num % 3)  # 1-3
            fw_minor = (machine_num // 3) % 10  # 0-9
            fw_patch = (machine_num // 30) % 20  # 0-19
            machine.firmware_version = f"v{fw_major}.{fw_minor}.{fw_patch}"
            
            # オプション構成
            option_mask = machine_num % 64  # 6ビットのマスク
            options = [opt for i, opt in enumerate(available_options) if option_mask & (1 << i)]
            machine.options = ", ".join(options) if options else "標準"
        
        await session.commit()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(populate_firmware_and_options())
