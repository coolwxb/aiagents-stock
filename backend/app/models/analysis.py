"""
分析结果模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class AnalysisHistory(Base):
    """分析历史记录模型"""
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String(50))  # stock/sector/longhubang等
    analysis_id = Column(Integer, index=True)
    content = Column(Text)  # JSON格式的分析内容
    created_at = Column(DateTime, server_default=func.now())

