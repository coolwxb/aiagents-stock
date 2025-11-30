"""
智策板块API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.dependencies import get_database
from app.services.sector_service import SectorService

router = APIRouter()


@router.post("/analyze")
async def analyze_sector(
    model: str = "deepseek-chat",
    db: Session = Depends(get_database)
):
    """板块分析"""
    service = SectorService(db)
    try:
        result = await service.analyze_sector(model)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule")
async def get_schedule(db: Session = Depends(get_database)):
    """获取定时任务"""
    service = SectorService(db)
    try:
        result = await service.get_schedule()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def set_schedule(
    schedule_time: str,
    enabled: bool = True,
    db: Session = Depends(get_database)
):
    """设置定时任务"""
    service = SectorService(db)
    try:
        result = await service.set_schedule(schedule_time, enabled)
        return success_response(result, msg="定时任务已更新")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedule/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_database)
):
    """删除定时任务"""
    service = SectorService(db)
    try:
        result = await service.delete_schedule(schedule_id)
        return success_response(result, msg="定时任务已删除")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger")
async def trigger_analysis(db: Session = Depends(get_database)):
    """手动触发分析"""
    service = SectorService(db)
    try:
        result = await service.trigger_analysis()
        return success_response(result, msg="分析任务已触发")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_database)
):
    """历史报告"""
    service = SectorService(db)
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
    service = SectorService(db)
    try:
        result = await service.generate_pdf(report_id)
        return success_response(result, msg="PDF生成成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

