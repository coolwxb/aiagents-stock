"""
股票请求/响应模式
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class StockAnalyzeRequest(BaseModel):
    """股票分析请求"""
    stock_code: str
    period: str = "1y"
    agents: Optional[List[str]] = None


class StockAnalyzeResponse(BaseModel):
    """股票分析响应"""
    stock_code: str
    stock_name: str
    rating: str
    confidence_level: float
    entry_range: str
    take_profit: float
    stop_loss: float
    target_price: float
    analysis_result: Dict[str, Any]
    created_at: datetime


class BatchAnalyzeRequest(BaseModel):
    """批量分析请求"""
    stock_codes: List[str]
    period: str = "1y"
    mode: str = "sequential"  # sequential/parallel
    max_workers: int = 3
    agents: Optional[List[str]] = None


class BatchAnalyzeResponse(BaseModel):
    """批量分析响应"""
    total: int
    success: int
    failed: int
    results: List[StockAnalyzeResponse]
    failed_stocks: List[Dict[str, Any]]

