"""
分析请求/响应模式
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AnalysisRequest(BaseModel):
    """分析请求基类"""
    model: str = "deepseek-chat"


class AnalysisResponse(BaseModel):
    """分析响应基类"""
    id: int
    analysis_type: str
    content: Dict[str, Any]
    created_at: datetime

