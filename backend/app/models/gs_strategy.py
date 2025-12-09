"""
GS策略相关模型
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class GSStockPool(Base):
    """GS策略股票池模型"""
    __tablename__ = "gs_stock_pool"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    stock_code = Column(String(20), nullable=False, unique=True, index=True, comment="股票代码")
    stock_name = Column(String(100), comment="股票名称")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, onupdate=func.now(), comment="更新时间")
    
    # 关联监控任务
    monitor_tasks = relationship("GSMonitorTask", back_populates="stock_pool", cascade="all, delete-orphan")


class GSMonitorTask(Base):
    """GS策略监控任务模型"""
    __tablename__ = "gs_monitor_tasks"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    stock_pool_id = Column(Integer, ForeignKey('gs_stock_pool.id'), comment="股票池ID")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    stock_name = Column(String(100), comment="股票名称")
    interval = Column(Integer, default=300, comment="监测间隔(秒)")
    status = Column(String(20), default='stopped', index=True, comment="状态: running/stopped")
    started_at = Column(DateTime, comment="监控启动时间")
    execution_count = Column(Integer, default=0, comment="策略执行次数")
    last_signal = Column(String(20), comment="最后信号: buy/sell/hold")
    last_signal_time = Column(DateTime, comment="最后信号时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, onupdate=func.now(), comment="更新时间")
    
    # 关联股票池
    stock_pool = relationship("GSStockPool", back_populates="monitor_tasks")
    # 关联交易历史
    trade_history = relationship("GSTradeHistory", back_populates="monitor_task", cascade="all, delete-orphan")
    
    # 复合索引
    __table_args__ = (
        Index('ix_gs_monitor_tasks_stock_status', 'stock_code', 'status'),
    )


class GSTradeHistory(Base):
    """GS策略交易历史模型"""
    __tablename__ = "gs_trade_history"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    monitor_id = Column(Integer, ForeignKey('gs_monitor_tasks.id'), comment="监控任务ID")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    stock_name = Column(String(100), comment="股票名称")
    
    # 买入信息
    buy_price = Column(Float, comment="买入价格")
    buy_quantity = Column(Integer, comment="买入数量")
    buy_time = Column(DateTime, comment="买入时间")
    buy_order_id = Column(String(50), comment="买入订单ID")
    
    # 卖出信息
    sell_price = Column(Float, comment="卖出价格")
    sell_quantity = Column(Integer, comment="卖出数量")
    sell_time = Column(DateTime, comment="卖出时间")
    sell_order_id = Column(String(50), comment="卖出订单ID")
    
    # 盈亏信息
    profit_loss = Column(Float, comment="盈亏金额")
    profit_loss_pct = Column(Float, comment="盈亏百分比")
    
    # 状态
    status = Column(String(20), comment="状态: open(持仓中)/closed(已平仓)")
    trade_details = Column(Text, comment="交易详情(JSON格式)")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, onupdate=func.now(), comment="更新时间")
    
    # 关联监控任务
    monitor_task = relationship("GSMonitorTask", back_populates="trade_history")
