"""
监测相关模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
from app.database import Base


class MonitorTask(Base):
    """监测任务模型"""
    __tablename__ = "monitor_tasks"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    task_name = Column(String(100), comment="任务名称")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    stock_name = Column(String(100), comment="股票名称")
    status = Column(String(20), comment="任务状态: running-运行中, stopped-已停止")
    check_interval = Column(Integer, comment="检查间隔(秒)")
    auto_trade = Column(Boolean, default=False, comment="是否自动交易")
    trading_hours_only = Column(Boolean, default=False, comment="是否仅交易时段监控")
    
    # 进场区间
    entry_min = Column(Float, nullable=True, comment="进场最低价(元)")
    entry_max = Column(Float, nullable=True, comment="进场最高价(元)")
    
    # 止盈止损
    take_profit = Column(Float, nullable=True, comment="止盈价位(元)")
    stop_loss = Column(Float, nullable=True, comment="止损价位(元)")
    
    # 通知设置
    notification_enabled = Column(Boolean, default=False, comment="是否启用通知")
    
    # 量化配置（JSON格式存储）
    quant_config = Column(Text, nullable=True, comment="量化策略配置(JSON字符串)")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, onupdate=func.now(), comment="更新时间")

