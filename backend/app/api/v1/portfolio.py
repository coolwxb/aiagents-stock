"""
持仓分析API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.dependencies import get_database
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/stocks")
async def get_stocks(db: Session = Depends(get_database)):
    """获取持仓列表"""
    service = PortfolioService(db)
    try:
        result = await service.get_stocks()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stocks")
async def create_stock(
    stock_data: dict,
    db: Session = Depends(get_database)
):
    """添加持仓"""
    service = PortfolioService(db)
    try:
        result = await service.create_stock(stock_data)
        return success_response(result, msg="持仓创建成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/stocks/{stock_id}")
async def update_stock(
    stock_id: int,
    stock_data: dict,
    db: Session = Depends(get_database)
):
    """更新持仓"""
    service = PortfolioService(db)
    try:
        result = await service.update_stock(stock_id, stock_data)
        return success_response(result, msg="持仓更新成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stocks/{stock_id}")
async def delete_stock(
    stock_id: int,
    db: Session = Depends(get_database)
):
    """删除持仓"""
    service = PortfolioService(db)
    try:
        result = await service.delete_stock(stock_id)
        return success_response(result, msg="持仓删除成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze")
async def batch_analyze(
    mode: str = "sequential",
    max_workers: int = 3,
    db: Session = Depends(get_database)
):
    """批量分析"""
    service = PortfolioService(db)
    try:
        result = await service.batch_analyze(mode, max_workers)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule")
async def get_schedule(db: Session = Depends(get_database)):
    """获取定时配置"""
    service = PortfolioService(db)
    try:
        result = await service.get_schedule()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def set_schedule(
    schedule_times: list,
    db: Session = Depends(get_database)
):
    """设置定时配置"""
    service = PortfolioService(db)
    try:
        result = await service.set_schedule(schedule_times)
        return success_response(result, msg="定时配置已更新")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    stock_code: str = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_database)
):
    """分析历史"""
    service = PortfolioService(db)
    try:
        result = await service.get_history(stock_code, page, page_size)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

