"""
GS策略API
提供股票池管理、监控任务管理、持仓查询和交易历史统计接口
"""
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from app.api.response import success_response, error_response
from app.dependencies import get_database
from app.services.gs_strategy_service import GSStrategyService

router = APIRouter()


# ==================== 请求模型 ====================

class StockPoolCreate(BaseModel):
    """添加股票到股票池的请求模型"""
    stock_code: str
    
    @validator('stock_code')
    def validate_stock_code(cls, v):
        """验证股票代码格式（A股：6位数字，以0/3/6开头）"""
        if not v:
            raise ValueError('股票代码不能为空')
        # 去除可能的后缀（如.SH, .SZ）
        code = v.split('.')[0]
        if not re.match(r'^[036]\d{5}$', code):
            raise ValueError('股票代码格式无效，应为6位数字且以0/3/6开头')
        return v


class MonitorCreate(BaseModel):
    """创建监控任务的请求模型"""
    stock_id: int
    interval: int = 300  # 默认5分钟
    
    @validator('interval')
    def validate_interval(cls, v):
        """验证监测间隔（最小30秒，最大3600秒）"""
        if v < 30:
            raise ValueError('监测间隔不能小于30秒')
        if v > 3600:
            raise ValueError('监测间隔不能大于3600秒')
        return v


class MonitorUpdate(BaseModel):
    """更新监控任务的请求模型"""
    interval: Optional[int] = None
    
    @validator('interval')
    def validate_interval(cls, v):
        """验证监测间隔"""
        if v is not None:
            if v < 30:
                raise ValueError('监测间隔不能小于30秒')
            if v > 3600:
                raise ValueError('监测间隔不能大于3600秒')
        return v


# ==================== 股票池管理接口 ====================

@router.get("/stock-pool")
async def get_stock_pool(db: Session = Depends(get_database)):
    """
    获取股票池列表
    
    Returns:
        股票池中所有股票的列表
    """
    service = GSStrategyService(db)
    try:
        result = service.get_stock_pool()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock-pool")
async def add_to_stock_pool(
    data: StockPoolCreate,
    db: Session = Depends(get_database)
):
    """
    添加股票到股票池（自动获取股票名称）
    
    Args:
        data: 包含stock_code的请求体
        
    Returns:
        添加的股票信息
    """
    service = GSStrategyService(db)
    try:
        result = service.add_to_stock_pool(data.stock_code)
        return success_response(result, msg="股票添加成功")
    except ValueError as e:
        return error_response(msg=str(e), code=409)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stock-pool/{stock_id}")
async def remove_from_stock_pool(
    stock_id: int,
    db: Session = Depends(get_database)
):
    """
    从股票池中删除股票
    
    Args:
        stock_id: 股票池记录ID
        
    Returns:
        删除结果
    """
    service = GSStrategyService(db)
    try:
        result = service.remove_from_stock_pool(stock_id)
        return success_response(result, msg="股票删除成功")
    except ValueError as e:
        return error_response(msg=str(e), code=404)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock-pool/search")
async def search_stock_pool(
    keyword: str = Query(..., description="搜索关键词（股票代码或名称）"),
    db: Session = Depends(get_database)
):
    """
    搜索股票池
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        匹配的股票列表
    """
    service = GSStrategyService(db)
    try:
        result = service.search_stock_pool(keyword)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock-info/{stock_code}")
async def get_stock_info(
    stock_code: str,
    db: Session = Depends(get_database)
):
    """
    获取股票信息（通过QMT接口）
    
    Args:
        stock_code: 股票代码（6位数字）
        
    Returns:
        股票信息，包含股票名称
    """
    service = GSStrategyService(db)
    try:
        result = service.get_stock_info(stock_code)
        return success_response(result)
    except ValueError as e:
        return error_response(msg=str(e), code=500)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 监控任务管理接口 ====================

@router.get("/monitors")
async def get_monitors(db: Session = Depends(get_database)):
    """
    获取监控任务列表
    
    Returns:
        所有监控任务的列表，包含运行时长计算
    """
    service = GSStrategyService(db)
    try:
        result = service.get_monitors()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitors")
async def create_monitor(
    data: MonitorCreate,
    db: Session = Depends(get_database)
):
    """
    创建监控任务
    
    Args:
        data: 包含stock_id和interval的请求体
        
    Returns:
        创建的监控任务信息
    """
    service = GSStrategyService(db)
    try:
        result = service.create_monitor(data.stock_id, data.interval)
        return success_response(result, msg="监控任务创建成功")
    except ValueError as e:
        error_msg = str(e)
        if "未找到" in error_msg:
            return error_response(msg=error_msg, code=404)
        elif "已在监控" in error_msg:
            return error_response(msg=error_msg, code=409)
        return error_response(msg=error_msg, code=400)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/monitors/{monitor_id}")
async def update_monitor(
    monitor_id: int,
    data: MonitorUpdate,
    db: Session = Depends(get_database)
):
    """
    更新监控任务配置
    
    Args:
        monitor_id: 监控任务ID
        data: 更新的数据
        
    Returns:
        更新后的监控任务信息
    """
    service = GSStrategyService(db)
    try:
        update_data = {}
        if data.interval is not None:
            update_data['interval'] = data.interval
        
        result = service.update_monitor(monitor_id, update_data)
        return success_response(result, msg="监控任务更新成功")
    except ValueError as e:
        return error_response(msg=str(e), code=404)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/monitors/{monitor_id}")
async def delete_monitor(
    monitor_id: int,
    db: Session = Depends(get_database)
):
    """
    删除监控任务
    
    Args:
        monitor_id: 监控任务ID
        
    Returns:
        删除结果
    """
    service = GSStrategyService(db)
    try:
        result = service.delete_monitor(monitor_id)
        return success_response(result, msg="监控任务删除成功")
    except ValueError as e:
        return error_response(msg=str(e), code=404)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitors/{monitor_id}/start")
async def start_monitor(
    monitor_id: int,
    db: Session = Depends(get_database)
):
    """
    启动监控任务
    
    Args:
        monitor_id: 监控任务ID
        
    Returns:
        启动后的监控任务信息
    """
    service = GSStrategyService(db)
    try:
        result = service.start_monitor(monitor_id)
        return success_response(result, msg="监控任务已启动")
    except ValueError as e:
        return error_response(msg=str(e), code=404)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitors/{monitor_id}/stop")
async def stop_monitor(
    monitor_id: int,
    db: Session = Depends(get_database)
):
    """
    停止监控任务
    
    Args:
        monitor_id: 监控任务ID
        
    Returns:
        停止后的监控任务信息
    """
    service = GSStrategyService(db)
    try:
        result = service.stop_monitor(monitor_id)
        return success_response(result, msg="监控任务已停止")
    except ValueError as e:
        return error_response(msg=str(e), code=404)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 持仓和历史统计接口 ====================

@router.get("/positions")
async def get_positions(db: Session = Depends(get_database)):
    """
    获取QMT持仓信息
    
    Returns:
        账户信息和持仓列表
    """
    service = GSStrategyService(db)
    try:
        result = service.get_positions()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_trade_history(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    db: Session = Depends(get_database)
):
    """
    获取交易历史记录
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        交易历史列表
    """
    service = GSStrategyService(db)
    try:
        result = service.get_trade_history(start_date, end_date)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_database)):
    """
    获取交易统计数据
    
    Returns:
        统计数据，包含总交易数、胜率、总盈亏等
    """
    service = GSStrategyService(db)
    try:
        result = service.get_statistics()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
