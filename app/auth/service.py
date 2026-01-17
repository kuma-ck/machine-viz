"""
認証サービス

パスワードのハッシュ化、検証、セッション管理を行う。
"""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User


class AuthService:
    """認証サービス"""
    
    def __init__(self):
        self.serializer = URLSafeTimedSerializer(settings.secret_key)
        self.session_max_age = 60 * 60 * 24 * 7  # 7日間
    
    # パスワード関連
    @staticmethod
    def hash_password(password: str) -> str:
        """パスワードをハッシュ化"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """パスワードを検証"""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    
    # セッション関連
    def create_session_token(self, user_id: int) -> str:
        """セッショントークンを生成"""
        return self.serializer.dumps({"user_id": user_id})
    
    def verify_session_token(self, token: str) -> Optional[int]:
        """セッショントークンを検証してユーザーIDを返す"""
        try:
            data = self.serializer.loads(token, max_age=self.session_max_age)
            return data.get("user_id")
        except (BadSignature, SignatureExpired):
            return None
    
    # ユーザー操作
    async def authenticate(
        self, 
        session: AsyncSession, 
        username: str, 
        password: str
    ) -> Optional[User]:
        """ユーザー名とパスワードで認証"""
        result = await session.execute(
            select(User).where(User.username == username, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if user and self.verify_password(password, user.hashed_password):
            # 最終ログイン日時を更新
            user.last_login = datetime.utcnow()
            await session.commit()
            return user
        
        return None
    
    async def get_user_by_id(
        self, 
        session: AsyncSession, 
        user_id: int
    ) -> Optional[User]:
        """IDでユーザーを取得"""
        result = await session.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        session: AsyncSession,
        username: str,
        password: str,
        email: str | None = None,
        is_admin: bool = False,
    ) -> User:
        """新規ユーザーを作成"""
        user = User(
            username=username,
            email=email,
            hashed_password=self.hash_password(password),
            is_admin=is_admin,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


# シングルトンインスタンス
auth_service = AuthService()
