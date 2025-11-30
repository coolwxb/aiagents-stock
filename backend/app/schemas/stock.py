"""
股票请求/响应模式
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


from pydantic import Field, field_validator


class StockAnalyzeRequest(BaseModel):
    """股票分析请求"""
    stock_code: str = Field(..., description="股票代码")
    period: str = "1y"
    model: str = "deepseek-chat"
    analysts: Optional[Dict[str, bool]] = None  # 分析师配置
    agents: Optional[List[str]] = None  # 旧版兼容
    
    @field_validator('stock_code', mode='before')
    @classmethod
    def convert_symbol_to_stock_code(cls, v, info):
        """兼容前端的symbol参数，自动转换为stock_code"""
        # 如果传入的是dict且包含symbol，使用symbol的值
        if isinstance(info.data, dict) and 'symbol' in info.data and not v:
            return info.data.get('symbol')
        return v


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


class MainforceAnalyzeRequest(BaseModel):
    """主力选股分析请求"""
    start_date: Optional[str] = None
    days_ago: Optional[int] = 90
    final_n: int = 5
    max_range_change: float = 30.0
    min_market_cap: float = 50.0
    max_market_cap: float = 5000.0
    model: str = "deepseek-chat"


class MainforceAnalyzeResponse(BaseModel):
    """主力选股分析响应"""
    success: bool
    total_stocks: int
    filtered_stocks: int
    final_recommendations: List[Dict[str, Any]]
    params: Dict[str, Any]
    error: Optional[str] = None


class MainforceBatchAnalyzeRequest(BaseModel):
    """主力选股批量分析请求"""
    stock_codes: List[str]
    analysis_mode: str = "sequential"  # sequential/parallel
    max_workers: int = 3
    model: str = "deepseek-chat"


class MainforceBatchAnalyzeResponse(BaseModel):
    """主力选股批量分析响应"""
    total: int
    success: int
    failed: int
    elapsed_time: float
    analysis_mode: str
    results: List[Dict[str, Any]]

