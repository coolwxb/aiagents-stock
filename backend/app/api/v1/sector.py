"""
智策板块API
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import io

from app.api.response import success_response
from app.dependencies import get_database
from app.services.sector_service import SectorService

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """分析请求模型"""
    model: str = "deepseek-chat"


class ScheduleRequest(BaseModel):
    """定时任务请求模型"""
    enabled: bool = True
    time: str = "09:00"
    notifyEmail: bool = True


class PDFRequest(BaseModel):
    """PDF生成请求模型"""
    report_id: int


@router.post("/analyze")
async def analyze_sector(
    request: AnalyzeRequest = Body(default=AnalyzeRequest()),
    db: Session = Depends(get_database)
):
    """
    板块分析
    
    执行智策多智能体板块分析，返回完整的分析结果
    """
    service = SectorService(db)
    try:
        result = await service.analyze_sector(request.model)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule")
async def get_schedule(db: Session = Depends(get_database)):
    """
    获取定时任务状态
    """
    service = SectorService(db)
    try:
        result = await service.get_schedule()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def set_schedule(
    request: ScheduleRequest = Body(...),
    db: Session = Depends(get_database)
):
    """
    设置定时任务
    """
    service = SectorService(db)
    try:
        result = await service.set_schedule(request.time, request.enabled)
        return success_response(result, msg="定时任务已更新")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedule/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_database)
):
    """
    删除定时任务
    """
    service = SectorService(db)
    try:
        result = await service.delete_schedule(schedule_id)
        return success_response(result, msg="定时任务已删除")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger")
async def trigger_analysis(db: Session = Depends(get_database)):
    """
    手动触发分析
    """
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
    """
    获取历史报告列表
    """
    service = SectorService(db)
    try:
        result = await service.get_history(page, page_size)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{report_id}")
async def get_report_detail(
    report_id: int,
    db: Session = Depends(get_database)
):
    """
    获取报告详情
    """
    service = SectorService(db)
    try:
        result = await service.get_report_detail(report_id)
        if result is None:
            raise HTTPException(status_code=404, detail="报告不存在")
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_database)
):
    """
    删除报告
    """
    service = SectorService(db)
    try:
        success = await service.delete_report(report_id)
        if success:
            return success_response({"deleted": True}, msg="报告已删除")
        else:
            raise HTTPException(status_code=404, detail="报告不存在或删除失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-pdf")
async def generate_pdf(
    request: PDFRequest = Body(...),
    db: Session = Depends(get_database)
):
    """
    生成PDF报告
    """
    service = SectorService(db)
    try:
        result = await service.generate_pdf(request.report_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "PDF生成失败"))
        
        # 如果有PDF文件路径，返回文件流
        if result.get("pdf_path"):
            try:
                with open(result["pdf_path"], "rb") as f:
                    pdf_content = f.read()
                return StreamingResponse(
                    io.BytesIO(pdf_content),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename=sector-report-{request.report_id}.pdf"
                    }
                )
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="PDF文件未找到")
        
        # 否则返回Markdown内容
        return success_response(result, msg="PDF生成成功")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
