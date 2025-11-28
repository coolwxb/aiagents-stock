"""
监测请求/响应模式
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MonitorTaskCreate(BaseModel):
    """创建监测任务请求"""
    task_name: str
    stock_code: str
    stock_name: str
    check_interval: int = 300
    auto_trade: bool = False
    trading_hours_only: bool = False


class MonitorTaskResponse(BaseModel):
    """监测任务响应"""
    id: int
    task_name: str
    stock_code: str
    stock_name: str
    status: str
    check_interval: int
    auto_trade: bool
    trading_hours_only: bool
    created_at: datetime
    updated_at: Optional[datetime]

