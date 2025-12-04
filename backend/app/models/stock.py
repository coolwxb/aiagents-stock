"""
股票相关模型
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class StockAnalysis(Base):
    """股票分析记录模型"""
    __tablename__ = "stock_analysis"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    stock_name = Column(String(100), comment="股票名称")
    analysis_type = Column(String(50), comment="分析类型: single-单股分析, batch-批量分析")
    analysis_result = Column(Text, comment="分析结果(JSON格式)")
    rating = Column(String(20), comment="评级: 买入/持有/卖出")
    confidence_level = Column(Float, comment="置信度(0-1)")
    entry_range = Column(String(50), comment="建议进场区间")
    take_profit = Column(Float, comment="止盈价位(元)")
    stop_loss = Column(Float, comment="止损价位(元)")
    target_price = Column(Float, comment="目标价(元)")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

