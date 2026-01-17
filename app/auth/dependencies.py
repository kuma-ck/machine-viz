"""
認証依存性

FastAPIのDependsで使用する認証関連の依存性関数。
"""

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.auth.service import auth_service


async def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    現在のログインユーザーを取得
    未ログインの場合はNoneを返す
    """
    if not session_token:
        return None
    
    user_id = auth_service.verify_session_token(session_token)
    if not user_id:
        return None
    
    user = await auth_service.get_user_by_id(db, user_id)
    return user


async def require_auth(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    認証が必要なエンドポイント用
    未ログインの場合は401エラー
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ログインが必要です",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(require_auth),
) -> User:
    """
    管理者権限が必要なエンドポイント用
    管理者でない場合は403エラー
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です",
        )
    return current_user
