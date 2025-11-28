"""
股票相关模型
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class StockAnalysis(Base):
    """股票分析记录模型"""
    __tablename__ = "stock_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100))
    analysis_type = Column(String(50))  # single/batch
    analysis_result = Column(Text)  # JSON格式
    rating = Column(String(20))  # 买入/持有/卖出
    confidence_level = Column(Float)
    entry_range = Column(String(50))
    take_profit = Column(Float)
    stop_loss = Column(Float)
    target_price = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

