"""
SQLAlchemy モデル定義

全テーブルのモデルを定義。
"""

from datetime import date
from typing import Optional

from sqlalchemy import ForeignKey, String, Float, Date, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Series(Base):
    """機種シリーズ"""
    __tablename__ = "series"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    
    # リレーション
    models: Mapped[list["Model"]] = relationship(back_populates="series", cascade="all, delete-orphan")


class Model(Base):
    """機種番号"""
    __tablename__ = "models"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    series_id: Mapped[str] = mapped_column(ForeignKey("series.id"))
    name: Mapped[str] = mapped_column(String(100))
    
    # リレーション
    series: Mapped["Series"] = relationship(back_populates="models")
    machines: Mapped[list["Machine"]] = relationship(back_populates="model", cascade="all, delete-orphan")


class Machine(Base):
    """機番"""
    __tablename__ = "machines"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"))
    manufacture_month: Mapped[str] = mapped_column(String(7))  # YYYY-MM
    operation_start_month: Mapped[str] = mapped_column(String(7))  # YYYY-MM
    firmware_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # v1.2.3 形式
    options: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # カンマ区切り: OP-A, OP-B
    
    # リレーション
    model: Mapped["Model"] = relationship(back_populates="machines")
    data: Mapped[list["MachineData"]] = relationship(back_populates="machine", cascade="all, delete-orphan")
    annotations: Mapped[list["Annotation"]] = relationship(back_populates="machine", cascade="all, delete-orphan")


class Category(Base):
    """データカテゴリー"""
    __tablename__ = "categories"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    
    # リレーション
    characteristics: Mapped[list["Characteristic"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class Characteristic(Base):
    """特性値ID"""
    __tablename__ = "characteristics"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(100))
    
    # リレーション
    category: Mapped["Category"] = relationship(back_populates="characteristics")
    data: Mapped[list["MachineData"]] = relationship(back_populates="characteristic")


class Aggregation(Base):
    """集計方法"""
    __tablename__ = "aggregations"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class MachineData(Base):
    """機番データ（時系列データ）"""
    __tablename__ = "machine_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.id"), index=True)
    characteristic_id: Mapped[str] = mapped_column(ForeignKey("characteristics.id"), index=True)
    month: Mapped[str] = mapped_column(String(7), index=True)  # YYYY-MM
    value: Mapped[float] = mapped_column(Float)
    aggregation: Mapped[str] = mapped_column(String(50))
    
    # リレーション
    machine: Mapped["Machine"] = relationship(back_populates="data")
    characteristic: Mapped["Characteristic"] = relationship(back_populates="data")


class Annotation(Base):
    """アノテーション（イベント情報）"""
    __tablename__ = "annotations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.id"), index=True)
    event_date: Mapped[date] = mapped_column(Date, index=True)
    event_type: Mapped[str] = mapped_column(String(50))  # firmware, parts, maintenance, error
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # リレーション
    machine: Mapped["Machine"] = relationship(back_populates="annotations")
