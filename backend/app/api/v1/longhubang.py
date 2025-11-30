"""
智瞰龙虎API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.dependencies import get_database
from app.services.longhubang_service import LonghubangService

router = APIRouter()


@router.post("/analyze")
async def analyze_longhubang(
    date: str = None,
    days: int = 1,
    model: str = "deepseek-chat",
    db: Session = Depends(get_database)
):
    """龙虎榜分析"""
    service = LonghubangService(db)
    try:
        result = await service.analyze_longhubang(date, days, model)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze")
async def batch_analyze(
    stock_codes: list,
    model: str = "deepseek-chat",
    db: Session = Depends(get_database)
):
    """批量分析"""
    service = LonghubangService(db)
    try:
        result = await service.batch_analyze(stock_codes, model)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scoring")
async def get_scoring(
    report_id: int,
    db: Session = Depends(get_database)
):
    """获取评分排名"""
    service = LonghubangService(db)
    try:
        result = await service.get_scoring(report_id)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_database)
):
    """历史报告"""
    service = LonghubangService(db)
    try:
        result = await service.get_history(page, page_size)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-pdf")
async def generate_pdf(
    report_id: int,
    db: Session = Depends(get_database)
):
    """生成PDF"""
    service = LonghubangService(db)
    try:
        result = await service.generate_pdf(report_id)
        return success_response(result, msg="PDF生成成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

