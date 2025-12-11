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
    """
    主力选股分析
    
    从问财获取主力资金净流入TOP100股票，经过筛选后由AI分析师团队进行整体分析，
    最终精选出指定数量的优质标的。
    """
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
    """
    批量深度分析
    
    对指定的股票列表进行完整的多智能体分析，获取投资评级和关键价位。
    支持顺序分析和并行分析两种模式。
    """
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
    """
    获取批量分析历史记录
    
    返回分页的历史记录列表，包含统计信息。
    """
    service = MainforceService(db)
    try:
        result = await service.get_history(page, page_size)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{record_id}")
async def get_history_detail(
    record_id: int,
    db: Session = Depends(get_database)
):
    """
    获取历史记录详情
    
    返回指定ID的批量分析记录详情，包含所有分析结果。
    """
    service = MainforceService(db)
    try:
        result = await service.get_history_detail(record_id)
        if result is None:
            raise HTTPException(status_code=404, detail="记录不存在")
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{record_id}")
async def delete_history(
    record_id: int,
    db: Session = Depends(get_database)
):
    """
    删除历史记录
    
    删除指定ID的批量分析记录。
    """
    service = MainforceService(db)
    try:
        success = await service.delete_history(record_id)
        if not success:
            raise HTTPException(status_code=404, detail="记录不存在或删除失败")
        return success_response({"message": "删除成功"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    db: Session = Depends(get_database)
):
    """
    获取统计信息
    
    返回批量分析的整体统计数据。
    """
    service = MainforceService(db)
    try:
        stats = service.batch_db.get_statistics()
        return success_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

