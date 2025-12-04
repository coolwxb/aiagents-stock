"""
分析结果模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class AnalysisHistory(Base):
    """分析历史记录模型"""
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    analysis_type = Column(String(50), comment="分析类型: stock-股票分析, sector-板块分析, longhubang-龙虎榜分析")
    analysis_id = Column(Integer, index=True, comment="关联分析记录ID")
    content = Column(Text, comment="分析内容(JSON格式)")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

