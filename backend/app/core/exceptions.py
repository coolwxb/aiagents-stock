"""
异常处理模块
"""
from fastapi import HTTPException, status


class StockAnalysisException(HTTPException):
    """股票分析异常"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class DataSourceException(HTTPException):
    """数据源异常"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class AIServiceException(HTTPException):
    """AI服务异常"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

