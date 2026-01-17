"""
管理者ユーザー作成スクリプト

初期管理者ユーザーを作成する。
"""

import asyncio
import sys

from app.database import async_session_maker, init_db
from app.auth.service import auth_service


async def create_admin_user(username: str, password: str):
    """管理者ユーザーを作成"""
    await init_db()
    
    async with async_session_maker() as session:
        try:
            user = await auth_service.create_user(
                session=session,
                username=username,
                password=password,
                is_admin=True,
            )
            print(f"管理者ユーザーを作成しました: {user.username}")
        except Exception as e:
            print(f"エラー: {e}")
            print("既に同じユーザー名が存在する可能性があります")


def main():
    if len(sys.argv) < 3:
        print("使い方: python scripts/create_admin.py <username> <password>")
        print("例: python scripts/create_admin.py admin password123")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    asyncio.run(create_admin_user(username, password))


if __name__ == "__main__":
    main()
