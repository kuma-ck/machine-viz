"""
不具合情報モデル

市場での不具合発生情報を格納するテーブル。
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Defect(Base):
    """不具合情報"""
    __tablename__ = "defects"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(String(50), index=True)  # 機番
    defect_type: Mapped[str] = mapped_column(String(100), index=True)  # 不具合種別
    occurred_at: Mapped[date] = mapped_column(Date, index=True)  # 発生日
    severity: Mapped[str] = mapped_column(String(20))  # 重大度（高/中/低）
    firmware_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 発生時点のFWバージョン
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 詳細
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
