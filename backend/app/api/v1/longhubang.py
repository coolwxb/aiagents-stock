"""
智瞰龙虎API
提供龙虎榜分析、历史报告、评分排名等接口
支持WebSocket实时进度推送
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.api.response import success_response
from app.api.websocket import longhubang_progress_manager

router = APIRouter()

# 线程池用于运行同步分析任务
_executor = ThreadPoolExecutor(max_workers=2)


# ============ 请求模型 ============

class AnalyzeRequest(BaseModel):
    """龙虎榜分析请求"""
    date: Optional[str] = None  # 指定日期，格式 YYYY-MM-DD
    days: int = 1  # 分析最近N天
    model: str = "deepseek-chat"  # AI模型


class BatchAnalyzeRequest(BaseModel):
    """批量分析请求"""
    stock_codes: List[str]
    model: str = "deepseek-chat"


class GeneratePDFRequest(BaseModel):
    """生成PDF请求"""
    report_id: int


# ============ 辅助函数 ============

def get_longhubang_service(model: str = "deepseek-chat"):
    """获取龙虎榜服务实例"""
    # 动态导入避免循环依赖
    import sys
    # 添加服务目录到路径
    service_path = os.path.join(os.path.dirname(__file__), '../../services/longhubang')
    if service_path not in sys.path:
        sys.path.insert(0, service_path)
    
    from app.services.longhubang.longhubang_service import LonghubangService
    return LonghubangService(model=model)


# ============ WebSocket 端点 ============

@router.websocket("/ws/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket端点：接收分析进度推送
    
    客户端连接后，会收到以下类型的消息：
    - progress: 进度更新 {type, task_id, progress, message, stage, timestamp}
    - log: 日志消息 {type, task_id, level, message, timestamp}
    - complete: 完成消息 {type, task_id, success, result/error, timestamp}
    """
    # 设置事件循环
    longhubang_progress_manager.set_loop(asyncio.get_event_loop())
    
    await longhubang_progress_manager.connect(task_id, websocket)
    
    try:
        while True:
            # 保持连接，等待客户端消息或断开
            data = await websocket.receive_text()
            # 可以处理客户端发来的消息（如取消请求）
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        longhubang_progress_manager.disconnect(task_id)
    except Exception as e:
        print(f"WebSocket错误: {e}")
        longhubang_progress_manager.disconnect(task_id)


# ============ API 接口 ============

@router.post("/analyze")
async def analyze_longhubang(request: AnalyzeRequest):
    """
    龙虎榜综合分析（同步版本，无进度推送）
    
    - 获取龙虎榜数据
    - 5位AI分析师多维度分析
    - 生成推荐股票和评分排名
    """
    try:
        service = get_longhubang_service(model=request.model)
        result = service.run_comprehensive_analysis(
            date=request.date,
            days=request.days
        )
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AnalyzeAsyncRequest(BaseModel):
    """异步分析请求"""
    date: Optional[str] = None
    days: int = 1
    model: str = "deepseek-chat"
    task_id: str  # 客户端生成的任务ID，用于WebSocket连接


@router.post("/analyze-async")
async def analyze_longhubang_async(request: AnalyzeAsyncRequest, background_tasks: BackgroundTasks):
    """
    龙虎榜综合分析（异步版本，支持WebSocket进度推送）
    
    使用步骤：
    1. 客户端生成唯一task_id
    2. 客户端连接WebSocket: ws://host/api/v1/longhubang/ws/{task_id}
    3. 客户端调用此接口，传入相同的task_id
    4. 服务端通过WebSocket推送进度
    5. 分析完成后，WebSocket收到complete消息
    """
    task_id = request.task_id
    
    # 检查WebSocket是否已连接
    if task_id not in longhubang_progress_manager.task_connections:
        raise HTTPException(
            status_code=400, 
            detail="请先连接WebSocket: ws://host/api/v1/longhubang/ws/{task_id}"
        )
    
    # 在后台线程中运行分析
    def run_analysis():
        try:
            # 导入带进度回调的服务
            from app.services.longhubang.longhubang_service import LonghubangService
            
            # 创建进度回调函数
            def progress_callback(progress: int, message: str, stage: str = ""):
                longhubang_progress_manager.sync_send_progress(
                    task_id, progress, message, stage
                )
            
            def log_callback(level: str, message: str):
                longhubang_progress_manager.sync_send_log(task_id, level, message)
            
            # 创建服务实例
            service = LonghubangService(model=request.model)
            
            # 运行分析（带进度回调）
            result = service.run_comprehensive_analysis_with_progress(
                date=request.date,
                days=request.days,
                progress_callback=progress_callback,
                log_callback=log_callback
            )
            
            # 发送完成消息
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                longhubang_progress_manager.send_complete(task_id, True, result)
            )
            loop.close()
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                longhubang_progress_manager.send_complete(task_id, False, error=error_msg)
            )
            loop.close()
    
    # 提交到线程池
    _executor.submit(run_analysis)
    
    return success_response({
        "task_id": task_id,
        "status": "started",
        "message": "分析任务已启动，请通过WebSocket接收进度"
    })


@router.post("/batch-analyze")
async def batch_analyze(request: BatchAnalyzeRequest):
    """
    批量分析龙虎榜TOP股票
    
    对指定的股票列表进行深度分析
    """
    try:
        # 批量分析需要调用主力选股的分析函数
        # 这里暂时返回提示信息，实际实现需要集成主力选股模块
        return success_response({
            "message": "批量分析功能开发中",
            "stock_codes": request.stock_codes,
            "model": request.model
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scoring")
async def get_scoring(
    report_id: Optional[int] = Query(None, description="报告ID，不传则获取最新"),
    limit: int = Query(20, description="返回数量")
):
    """
    获取AI智能评分排名
    
    返回股票的综合评分排名数据
    """
    try:
        service = get_longhubang_service()
        
        if report_id:
            # 获取指定报告的评分数据
            report = service.get_report_detail(report_id)
            if not report:
                raise HTTPException(status_code=404, detail="报告不存在")
            
            # 从报告中提取评分数据
            analysis_content = report.get('analysis_content_parsed', {})
            scoring_ranking = analysis_content.get('scoring_ranking', [])
            
            return success_response({
                "items": scoring_ranking[:limit],
                "total": len(scoring_ranking),
                "report_id": report_id
            })
        else:
            # 获取最新报告的评分数据
            reports_df = service.get_historical_reports(limit=1)
            if reports_df.empty:
                return success_response({
                    "items": [],
                    "total": 0,
                    "message": "暂无评分数据"
                })
            
            latest_report_id = int(reports_df.iloc[0]['id'])
            report = service.get_report_detail(latest_report_id)
            
            if report:
                analysis_content = report.get('analysis_content_parsed', {})
                scoring_ranking = analysis_content.get('scoring_ranking', [])
                
                return success_response({
                    "items": scoring_ranking[:limit],
                    "total": len(scoring_ranking),
                    "report_id": latest_report_id
                })
            
            return success_response({
                "items": [],
                "total": 0,
                "message": "暂无评分数据"
            })
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取历史分析报告列表
    """
    try:
        service = get_longhubang_service()
        
        # 获取历史报告
        limit = page_size * page
        reports_df = service.get_historical_reports(limit=limit)
        
        if reports_df.empty:
            return success_response({
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size
            })
        
        # 分页处理
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_df = reports_df.iloc[start_idx:end_idx]
        
        # 转换为列表
        items = []
        for _, row in page_df.iterrows():
            item = {
                "id": int(row['id']),
                "analysis_date": row['analysis_date'],
                "data_date_range": row['data_date_range'],
                "summary": row['summary'],
                "created_at": row['created_at']
            }
            
            # 尝试解析analysis_content获取更多信息
            try:
                import json
                if row.get('analysis_content'):
                    content = json.loads(row['analysis_content'])
                    item['confidence_score'] = content.get('confidence_score', 0.75)
                    item['market_outlook'] = content.get('market_outlook', '中性')
                    item['analysis_content'] = content
            except:
                item['confidence_score'] = 0.75
                item['market_outlook'] = '中性'
            
            items.append(item)
        
        return success_response({
            "items": items,
            "total": len(reports_df),
            "page": page,
            "page_size": page_size
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{report_id}")
async def get_history_detail(report_id: int):
    """
    获取单个历史报告详情
    """
    try:
        service = get_longhubang_service()
        report = service.get_report_detail(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        return success_response(report)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{report_id}")
async def delete_history(report_id: int):
    """
    删除历史报告
    """
    try:
        service = get_longhubang_service()
        success = service.database.delete_analysis_report(report_id)
        
        if success:
            return success_response({"message": f"报告 #{report_id} 已删除"})
        else:
            raise HTTPException(status_code=404, detail="报告不存在或删除失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics():
    """
    获取龙虎榜数据统计信息
    """
    try:
        service = get_longhubang_service()
        stats = service.get_statistics()
        
        return success_response(stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-youzi")
async def get_top_youzi(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    获取活跃游资排名
    """
    try:
        service = get_longhubang_service()
        df = service.get_top_youzi(start_date, end_date, limit)
        
        if df.empty:
            return success_response({"items": [], "total": 0})
        
        items = df.to_dict('records')
        return success_response({
            "items": items,
            "total": len(items)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-stocks")
async def get_top_stocks(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    获取热门股票排名
    """
    try:
        service = get_longhubang_service()
        df = service.get_top_stocks(start_date, end_date, limit)
        
        if df.empty:
            return success_response({"items": [], "total": 0})
        
        items = df.to_dict('records')
        return success_response({
            "items": items,
            "total": len(items)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-pdf")
async def generate_pdf(request: GeneratePDFRequest):
    """
    生成PDF报告
    """
    try:
        service = get_longhubang_service()
        report = service.get_report_detail(request.report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        # 动态导入PDF生成器
        from app.services.longhubang.longhubang_pdf import LonghubangPDFGenerator
        
        # 构建完整的result数据
        analysis_content = report.get('analysis_content_parsed', {})
        result_data = {
            "success": True,
            "timestamp": report.get('analysis_date', ''),
            "data_info": analysis_content.get('data_info', {}),
            "agents_analysis": analysis_content.get('agents_analysis', {}),
            "scoring_ranking": analysis_content.get('scoring_ranking', []),
            "final_report": analysis_content.get('final_report', {}),
            "recommended_stocks": report.get('recommended_stocks', [])
        }
        
        # 生成PDF
        generator = LonghubangPDFGenerator()
        pdf_path = generator.generate_pdf(result_data)
        
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(
                path=pdf_path,
                filename=f"longhubang_report_{request.report_id}.pdf",
                media_type="application/pdf"
            )
        else:
            raise HTTPException(status_code=500, detail="PDF生成失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
