"""
智能盯盘API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.dependencies import get_database
from app.services.monitor_service import MonitorService

router = APIRouter()


@router.get("/tasks")
async def get_tasks(db: Session = Depends(get_database)):
    """获取监控任务列表"""
    service = MonitorService(db)
    try:
        result = await service.get_tasks()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks")
async def create_task(
    task_data: dict,
    db: Session = Depends(get_database)
):
    """创建监控任务"""
    service = MonitorService(db)
    try:
        result = await service.create_task(task_data)
        return success_response(result, msg="任务创建成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: int,
    task_data: dict,
    db: Session = Depends(get_database)
):
    """更新任务"""
    service = MonitorService(db)
    try:
        result = await service.update_task(task_id, task_data)
        return success_response(result, msg="任务更新成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_database)
):
    """删除任务"""
    service = MonitorService(db)
    try:
        result = await service.delete_task(task_id)
        return success_response(result, msg="任务删除成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: int,
    db: Session = Depends(get_database)
):
    """启动任务"""
    service = MonitorService(db)
    try:
        result = await service.start_task(task_id)
        return success_response(result, msg="任务已启动")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/stop")
async def stop_task(
    task_id: int,
    db: Session = Depends(get_database)
):
    """停止任务"""
    service = MonitorService(db)
    try:
        result = await service.stop_task(task_id)
        return success_response(result, msg="任务已停止")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: int,
    db: Session = Depends(get_database)
):
    """获取任务状态"""
    service = MonitorService(db)
    try:
        result = await service.get_task_status(task_id)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions(db: Session = Depends(get_database)):
    """获取持仓"""
    service = MonitorService(db)
    try:
        result = await service.get_positions()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_database)
):
    """决策历史"""
    service = MonitorService(db)
    try:
        result = await service.get_history(page, page_size)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote/{stock_code}")
async def get_stock_quote(
    stock_code: str,
    db: Session = Depends(get_database)
):
    """获取股票实时行情"""
    service = MonitorService(db)
    try:
        result = await service.get_stock_quote(stock_code)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
