"""
主力选股API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.dependencies import get_database
from app.services.mainforce_service import MainforceService
from app.schemas.stock import (
    MainforceAnalyzeRequest,
    MainforceAnalyzeResponse,
    MainforceBatchAnalyzeRequest,
    MainforceBatchAnalyzeResponse
)

router = APIRouter()


@router.post("/analyze", response_model=MainforceAnalyzeResponse)
async def analyze_mainforce(
    request: MainforceAnalyzeRequest,
    db: Session = Depends(get_database)
):
    """主力选股分析"""
    service = MainforceService(db)
    try:
        result = await service.analyze_mainforce(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze", response_model=MainforceBatchAnalyzeResponse)
async def batch_analyze(
    request: MainforceBatchAnalyzeRequest,
    db: Session = Depends(get_database)
):
    """批量分析"""
    service = MainforceService(db)
    try:
        result = await service.batch_analyze(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_database)
):
    """历史记录"""
    service = MainforceService(db)
    try:
        result = await service.get_history(page, page_size)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

