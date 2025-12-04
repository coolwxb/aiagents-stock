"""
持仓相关模型
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class PortfolioStock(Base):
    """持仓股票模型"""
    __tablename__ = "portfolio_stocks"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    stock_name = Column(String(100), comment="股票名称")
    cost_price = Column(Float, comment="成本价(元)")
    quantity = Column(Integer, comment="持有数量(股)")
    notes = Column(Text, comment="备注信息")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, onupdate=func.now(), comment="更新时间")

