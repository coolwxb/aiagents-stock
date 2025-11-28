"""
通用模式
"""
from pydantic import BaseModel
from typing import Optional, List, Any, Generic, TypeVar

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    timestamp: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int
    message: str
    error: Optional[str] = None
    timestamp: Optional[str] = None

