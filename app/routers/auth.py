"""
認証APIルーター

ログイン、ログアウト、認証状態確認のエンドポイント。
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.auth.service import auth_service
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """ログインリクエスト"""
    username: str
    password: str


class UserResponse(BaseModel):
    """ユーザーレスポンス"""
    id: int
    username: str
    is_admin: bool


@router.post("/login")
async def login(
    req: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """ログイン"""
    user = await auth_service.authenticate(db, req.username, req.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
        )
    
    # セッショントークンを生成してCookieに設定
    token = auth_service.create_session_token(user.id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=settings.is_production,  # 本番環境ではSecure属性を有効化
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7日間
    )
    
    return {
        "message": "ログインしました",
        "user": UserResponse(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
        ),
    }


@router.post("/logout")
async def logout(response: Response):
    """ログアウト"""
    response.delete_cookie(key="session_token")
    return {"message": "ログアウトしました"}


@router.get("/me")
async def get_me(
    current_user: User | None = Depends(get_current_user),
):
    """現在のログインユーザーを取得"""
    if not current_user:
        return {"user": None}
    
    return {
        "user": UserResponse(
            id=current_user.id,
            username=current_user.username,
            is_admin=current_user.is_admin,
        ),
    }
