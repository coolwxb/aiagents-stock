"""
股票分析API
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.dependencies import get_database
from app.schemas.stock import StockAnalyzeRequest, StockAnalyzeResponse, BatchAnalyzeRequest
from app.services.stock_service import StockService

router = APIRouter()


@router.post("/analyze", response_model=StockAnalyzeResponse)
async def analyze_stock(
    request: StockAnalyzeRequest,
    db: Session = Depends(get_database)
):
    """单股分析"""
    service = StockService(db)
    try:
        result = await service.analyze_stock(request)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze")
async def batch_analyze(
    request: BatchAnalyzeRequest,
    db: Session = Depends(get_database)
):
    """批量分析"""
    service = StockService(db)
    try:
        result = await service.batch_analyze(request)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    stock_code: str = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_database)
):
    """查询历史记录"""
    service = StockService(db)
    try:
        result = await service.get_history(stock_code, page, page_size)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}")
async def get_stock_info(
    stock_code: str,
    db: Session = Depends(get_database)
):
    """获取股票信息"""
    service = StockService(db)
    try:
        result = await service.get_stock_info(stock_code)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-pdf")
async def generate_pdf(
    analysis_id: int,
    db: Session = Depends(get_database)
):
    """生成PDF报告"""
    service = StockService(db)
    try:
        result = await service.generate_pdf(analysis_id)
        return success_response(result, msg="PDF生成成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

