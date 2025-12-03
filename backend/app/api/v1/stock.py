"""
股票分析API
"""
from typing import List
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.dependencies import get_database
from app.schemas.stock import StockAnalyzeRequest, StockAnalyzeResponse, BatchAnalyzeRequest
from app.services.stock_service import StockService
from app.core.progress_tracker import get_progress_tracker
from app.core.websocket_manager import get_ws_manager

router = APIRouter()


@router.post("/analyze")
async def analyze_stock(
    request: StockAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """单股分析 - 异步任务，立即返回task_id"""
    service = StockService(db)
    tracker = get_progress_tracker()
    
    # 创建任务
    task_id = tracker.create_task(
        task_type="stock_analysis",
        params={
            "stock_code": request.stock_code,
            "period": request.period,
            "model": request.model
        }
    )
    
    # 在后台执行分析任务
    background_tasks.add_task(
        service.analyze_stock_with_progress,
        task_id=task_id,
        request=request
    )
    
    return success_response({
        "task_id": task_id,
        "message": "分析任务已启动，请通过task_id查询进度"
    })


@router.get("/analyze-progress/{task_id}")
async def get_analyze_progress(task_id: str):
    """查询分析进度"""
    tracker = get_progress_tracker()
    task_info = tracker.get_task(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return success_response(task_info)


@router.get("/active-tasks")
async def get_active_tasks():
    """获取所有进行中的任务"""
    tracker = get_progress_tracker()
    active_tasks = tracker.get_active_tasks()
    return success_response({
        "tasks": active_tasks,
        "count": len(active_tasks)
    })


@router.websocket("/ws/analyze/{task_id}")
async def websocket_analyze_progress(websocket: WebSocket, task_id: str):
    """
WebSocket连接端点 - 实时推送分析进度
    
    客户端可以连接到此端点来接收实时进度更新
    地址: ws://host:port/api/v1/stock/ws/analyze/{task_id}
    """
    ws_manager = get_ws_manager()
    tracker = get_progress_tracker()
    
    try:
        # 建立连接
        await ws_manager.connect(websocket, task_id)
        
        # 立即发送当前任务状态
        task_info = tracker.get_task(task_id)
        if task_info:
            await websocket.send_text(json.dumps(task_info, ensure_ascii=False))
        else:
            await websocket.send_text(json.dumps({
                "error": "任务不存在",
                "task_id": task_id
            }))
        
        # 保持连接，监听客户端消息
        while True:
            try:
                # 接收客户端消息（用于保持连接）
                data = await websocket.receive_text()
                
                # 处理客户端请求（可选）
                try:
                    message = json.loads(data)
                    if message.get("action") == "ping":
                        await websocket.send_text(json.dumps({"action": "pong"}))
                    elif message.get("action") == "get_status":
                        task_info = tracker.get_task(task_id)
                        if task_info:
                            await websocket.send_text(json.dumps(task_info, ensure_ascii=False))
                except json.JSONDecodeError:
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket错误: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket连接错误: {e}")
    finally:
        # 断开连接
        ws_manager.disconnect(websocket)


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

