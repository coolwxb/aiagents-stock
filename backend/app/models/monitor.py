"""
监测相关模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
from app.database import Base


class MonitorTask(Base):
    """监测任务模型"""
    __tablename__ = "monitor_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(100))
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100))
    status = Column(String(20))  # running/stopped
    check_interval = Column(Integer)  # 秒
    auto_trade = Column(Boolean, default=False)
    trading_hours_only = Column(Boolean, default=False)
    
    # 进场区间
    entry_min = Column(Float, nullable=True)
    entry_max = Column(Float, nullable=True)
    
    # 止盈止损
    take_profit = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    
    # 通知设置
    notification_enabled = Column(Boolean, default=False)
    
    # 量化配置（JSON格式存储）
    quant_config = Column(Text, nullable=True)  # 存储JSON字符串
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

