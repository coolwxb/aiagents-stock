"""
量化交易API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.dependencies import get_database
from app.services.trading_service import TradingService

router = APIRouter()


@router.get("/status")
async def get_trading_status(db: Session = Depends(get_database)):
    """获取交易状态"""
    service = TradingService(db)
    try:
        result = await service.get_status()
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order")
async def place_order(
    order_data: dict,
    db: Session = Depends(get_database)
):
    """下单"""
    service = TradingService(db)
    try:
        result = await service.place_order(order_data)
        return success_response(result, msg="下单成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_database)
):
    """获取订单列表"""
    service = TradingService(db)
    try:
        result = await service.get_orders(page, page_size)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

