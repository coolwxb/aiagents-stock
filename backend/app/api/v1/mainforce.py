"""
主力选股API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_database
from app.services.mainforce_service import MainforceService

router = APIRouter()


@router.post("/analyze")
async def analyze_mainforce(
    start_date: str,
    max_market_cap: float = 5000,
    min_market_cap: float = 50,
    max_change_pct: float = 50,
    model: str = "deepseek-chat",
    db: Session = Depends(get_database)
):
    """主力选股分析"""
    service = MainforceService(db)
    try:
        result = await service.analyze_mainforce(
            start_date, max_market_cap, min_market_cap, max_change_pct, model
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze")
async def batch_analyze(
    count: int = 10,
    model: str = "deepseek-chat",
    db: Session = Depends(get_database)
):
    """批量分析"""
    service = MainforceService(db)
    try:
        result = await service.batch_analyze(count, model)
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
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

