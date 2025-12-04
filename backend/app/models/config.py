"""
配置存储模型
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from app.database import Base


class AppConfig(Base):
    """键值型配置表"""

    __tablename__ = "app_config"

    key = Column(String(128), primary_key=True, index=True, comment="配置键")
    value = Column(Text, nullable=False, default="", comment="配置值")
    description = Column(Text, nullable=True, comment="配置说明")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

