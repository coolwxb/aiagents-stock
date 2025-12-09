"""
API路由汇总
"""
from fastapi import APIRouter
from app.api.v1 import (
    stock,
    sector,
    longhubang,
    mainforce,
    monitor,
    realtime,
    portfolio,
    trading,
    notification,
    config,
    user,
    data_management,
    gs_strategy,
    qmt
)

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(stock.router, prefix="/stock", tags=["股票分析"])
api_router.include_router(sector.router, prefix="/sector", tags=["智策板块"])
api_router.include_router(longhubang.router, prefix="/longhubang", tags=["智瞰龙虎"])
api_router.include_router(mainforce.router, prefix="/mainforce", tags=["主力选股"])
api_router.include_router(monitor.router, prefix="/monitor", tags=["智能盯盘"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["实时监测"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["持仓分析"])
api_router.include_router(trading.router, prefix="/trading", tags=["量化交易"])
api_router.include_router(notification.router, prefix="/notification", tags=["通知服务"])
api_router.include_router(config.router, prefix="/config", tags=["配置管理"])
api_router.include_router(user.router, prefix="/user", tags=["用户管理"])
api_router.include_router(data_management.router, prefix="/data", tags=["数据管理"])
api_router.include_router(gs_strategy.router, prefix="/gs-strategy", tags=["GS策略"])
api_router.include_router(qmt.router, prefix="/qmt", tags=["QMT交易"])

