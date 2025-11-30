"""
实时监测API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.dependencies import get_database
from app.services.realtime_service import RealtimeService

router = APIRouter()


@router.get("/monitors")
async def get_monitors(db: Session = Depends(get_database)):
    """获取监测列表"""
    service = RealtimeService(db)
    try:
        result = await service.get_monitors()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitors")
async def create_monitor(
    monitor_data: dict,
    db: Session = Depends(get_database)
):
    """添加监测"""
    service = RealtimeService(db)
    try:
        result = await service.create_monitor(monitor_data)
        return success_response(result, msg="监测创建成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/monitors/{monitor_id}")
async def update_monitor(
    monitor_id: int,
    monitor_data: dict,
    db: Session = Depends(get_database)
):
    """更新监测"""
    service = RealtimeService(db)
    try:
        result = await service.update_monitor(monitor_id, monitor_data)
        return success_response(result, msg="监测更新成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/monitors/{monitor_id}")
async def delete_monitor(
    monitor_id: int,
    db: Session = Depends(get_database)
):
    """删除监测"""
    service = RealtimeService(db)
    try:
        result = await service.delete_monitor(monitor_id)
        return success_response(result, msg="监测删除成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_service(db: Session = Depends(get_database)):
    """启动监测服务"""
    service = RealtimeService(db)
    try:
        result = await service.start_service()
        return success_response(result, msg="监测服务已启动")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_service(db: Session = Depends(get_database)):
    """停止监测服务"""
    service = RealtimeService(db)
    try:
        result = await service.stop_service()
        return success_response(result, msg="监测服务已停止")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications")
async def get_notifications(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_database)
):
    """通知历史"""
    service = RealtimeService(db)
    try:
        result = await service.get_notifications(page, page_size)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

