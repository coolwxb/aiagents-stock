"""
QMT交易服务API
提供QMT连接、账户、持仓、交易、行情等接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.response import success_response, error_response
from app.dependencies import get_database
from app.services.qmt_service import qmt_service

router = APIRouter()


# ==================== 请求模型 ====================

class TradeRequest(BaseModel):
    """交易请求"""
    stock_code: str = Field(..., description="股票代码，如：600519")
    quantity: int = Field(..., description="数量（买入必须是100的整数倍）")
    price: float = Field(default=0, description="价格（限价单时使用）")
    order_type: str = Field(default="market", description="订单类型：market市价/limit限价")


class StockCodesRequest(BaseModel):
    """股票代码列表请求"""
    stock_codes: List[str] = Field(..., description="股票代码列表")


# ==================== 连接管理 ====================

@router.get("/status")
async def get_status(db: Session = Depends(get_database)):
    """
    获取QMT连接状态
    
    返回QMT模块加载状态、连接状态、配置信息等
    """
    try:
        # 加载配置
        qmt_service.load_config(db)
        
        return success_response({
            "enabled": qmt_service.enabled,
            "connected": qmt_service.is_connected(),
            "account_id": qmt_service.account_id,
            "account_type": qmt_service.account_type,
            "userdata_path": qmt_service.userdata_path,
            "module_loaded": qmt_service.xtdata_module is not None,
            "whole_quote_stats": qmt_service.get_whole_quote_stats()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect")
async def connect(db: Session = Depends(get_database)):
    """
    连接到MiniQMT
    
    按照官方文档标准流程建立连接
    """
    try:
        # 先加载配置
        qmt_service.load_config(db)
        
        success, message = qmt_service.connect()
        
        if success:
            return success_response({"connected": True}, msg=message)
        else:
            return error_response(msg=message, code=400, data={"connected": False})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect():
    """
    断开QMT连接
    """
    try:
        qmt_service.disconnect()
        return success_response({"connected": False}, msg="已断开连接")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 账户信息 ====================

@router.get("/account")
async def get_account_info():
    """
    获取账户信息
    
    返回可用资金、总资产、持仓市值、冻结资金等
    """
    try:
        account_info = qmt_service.get_account_info()
        return success_response(account_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 持仓管理 ====================

@router.get("/positions")
async def get_all_positions():
    """
    获取所有持仓
    
    返回持仓列表，包含股票代码、名称、数量、成本价、当前价、盈亏等
    """
    try:
        positions = qmt_service.get_all_positions()
        return success_response(positions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions/{stock_code}")
async def get_position(stock_code: str):
    """
    获取指定股票的持仓信息
    
    Args:
        stock_code: 股票代码（如：600519）
    """
    try:
        position = qmt_service.get_position(stock_code)
        if position:
            return success_response(position)
        else:
            return success_response(None, msg=f"未持有股票 {stock_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 交易接口 ====================

@router.post("/buy")
async def buy_stock(request: TradeRequest):
    """
    买入股票
    
    Args:
        stock_code: 股票代码
        quantity: 数量（必须是100的整数倍）
        price: 价格（限价单时使用）
        order_type: 订单类型（market/limit）
    """
    try:
        result = qmt_service.buy_stock(
            stock_code=request.stock_code,
            quantity=request.quantity,
            price=request.price,
            order_type=request.order_type
        )
        
        if result.get("success"):
            return success_response(result, msg="买入订单已提交")
        else:
            return error_response(msg=result.get("error", "买入失败"), code=400, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sell")
async def sell_stock(request: TradeRequest):
    """
    卖出股票
    
    Args:
        stock_code: 股票代码
        quantity: 数量
        price: 价格（限价单时使用）
        order_type: 订单类型（market/limit）
    """
    try:
        result = qmt_service.sell_stock(
            stock_code=request.stock_code,
            quantity=request.quantity,
            price=request.price,
            order_type=request.order_type
        )
        
        if result.get("success"):
            return success_response(result, msg="卖出订单已提交")
        else:
            return error_response(msg=result.get("error", "卖出失败"), code=400, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 实时行情（全推数据） ====================

@router.get("/quote/stats")
async def get_whole_quote_stats():
    """
    获取全推数据统计信息
    
    返回订阅状态、股票数量、最新更新时间等
    """
    try:
        stats = qmt_service.get_whole_quote_stats()
        return success_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote/{stock_code}")
async def get_stock_quote(stock_code: str):
    """
    获取指定股票的实时行情
    
    Args:
        stock_code: 股票代码（如：600519 或 600519.SH）
    """
    try:
        quote = qmt_service.get_stock_quote(stock_code)
        if quote:
            return success_response(quote)
        else:
            return success_response(None, msg=f"未找到股票 {stock_code} 的行情数据")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quote/batch")
async def get_stocks_quote(request: StockCodesRequest):
    """
    批量获取多个股票的实时行情
    
    Args:
        stock_codes: 股票代码列表
    """
    try:
        quotes = qmt_service.get_stocks_quote(request.stock_codes)
        return success_response(quotes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote")
async def get_all_quotes(
    limit: int = Query(default=100, description="返回数量限制，0表示全部")
):
    """
    获取所有全推行情数据
    
    Args:
        limit: 返回数量限制，默认100，0表示返回全部
    """
    try:
        all_data = qmt_service.get_whole_quote_data()
        
        if limit > 0:
            # 限制返回数量
            limited_data = dict(list(all_data.items())[:limit])
            return success_response({
                "total": len(all_data),
                "returned": len(limited_data),
                "data": limited_data
            })
        else:
            return success_response({
                "total": len(all_data),
                "returned": len(all_data),
                "data": all_data
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 股票基础信息 ====================

@router.get("/info/{stock_code}")
async def get_stock_info(stock_code: str):
    """
    获取股票基础信息（完整版）
    
    返回合约代码、名称、交易所、IPO日期、涨跌停价、股本等完整信息
    
    Args:
        stock_code: 股票代码（如：600519 或 600519.SH）
    """
    try:
        info = qmt_service.get_stock_info(stock_code)
        if info:
            return success_response(info)
        else:
            return success_response(None, msg=f"未找到股票 {stock_code} 的基础信息")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info/{stock_code}/basic")
async def get_stock_basic_info(stock_code: str):
    """
    获取股票基础信息（简化版）
    
    返回常用字段：代码、名称、交易所、涨跌停价、股本等
    
    Args:
        stock_code: 股票代码（如：600519 或 600519.SH）
    """
    try:
        info = qmt_service.get_stock_basic_info(stock_code)
        if info:
            return success_response(info)
        else:
            return success_response(None, msg=f"未找到股票 {stock_code} 的基础信息")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/info/batch")
async def get_stocks_info(request: StockCodesRequest):
    """
    批量获取多个股票的基础信息
    
    Args:
        stock_codes: 股票代码列表
    """
    try:
        infos = qmt_service.get_stocks_info(request.stock_codes)
        return success_response(infos)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 财务数据 ====================

@router.get("/financial/{stock_code}")
async def get_financial_data(
    stock_code: str,
    report_type: str = Query(
        default="Income",
        description="报表类型：Balance资产负债表/Income利润表/CashFlow现金流量表/PershareIndex主要指标/Capital股本表/Top10holder十大股东/Top10flowholder十大流通股东/Holdernum股东数"
    ),
    start_date: str = Query(default="", description="开始日期，格式：20240101"),
    end_date: str = Query(default="", description="结束日期，格式：20241231")
):
    """
    获取财务数据
    
    Args:
        stock_code: 股票代码
        report_type: 报表类型
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        data = qmt_service.get_financial_data(
            stock_code=stock_code,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date
        )
        if data:
            return success_response(data)
        else:
            return success_response(None, msg=f"未找到股票 {stock_code} 的财务数据")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/financial/{stock_code}/download")
async def download_financial_data(
    stock_code: str,
    report_type: str = Query(
        default="Income",
        description="报表类型：Balance/Income/CashFlow/PershareIndex/Capital/Top10holder/Top10flowholder/Holdernum"
    ),
    start_date: str = Query(default="", description="开始日期，格式：20240101"),
    end_date: str = Query(default="", description="结束日期，格式：20241231")
):
    """
    下载财务数据到本地
    
    下载后的数据会保存到本地，后续调用get_financial_data时会优先从本地读取
    
    Args:
        stock_code: 股票代码
        report_type: 报表类型
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        success = qmt_service.download_financial_data(
            stock_code=stock_code,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date
        )
        if success:
            return success_response({"downloaded": True}, msg="财务数据下载成功")
        else:
            return error_response(msg="财务数据下载失败", code=400)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financial/fields/{report_type}")
async def get_financial_fields_info(report_type: str):
    """
    获取财务数据字段说明
    
    Args:
        report_type: 报表类型：Balance/Income/CashFlow/PershareIndex/Capital/Top10holder/Top10flowholder/Holdernum
    """
    try:
        from app.services.qmt_service import QMTService
        fields_info = QMTService.get_financial_fields_info(report_type)
        return success_response(fields_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 历史K线数据 ====================

@router.get("/kline/{stock_code}")
async def get_stock_kline(
    stock_code: str,
    period: str = Query(default="1d", description="K线周期：1m/5m/15m/30m/60m/1d/1w/1M"),
    start_date: str = Query(default="", description="开始日期，格式：20240101"),
    end_date: str = Query(default="", description="结束日期，格式：20241231"),
    count: int = Query(default=200, description="获取数量")
):
    """
    获取股票历史K线数据
    
    Args:
        stock_code: 股票代码（如：600519 或 600519.SH）
        period: K线周期
        start_date: 开始日期
        end_date: 结束日期
        count: 获取数量
    
    Returns:
        K线数据DataFrame转换的字典
    """
    try:
        from app.data.data_source import data_source_manager
        
        df = data_source_manager.get_stock_hist_data(
            symbol=stock_code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            count=count
        )
        
        if df is None or df.empty:
            return success_response(None, msg=f"未找到股票 {stock_code} 的K线数据")
        
        # 将DataFrame转换为可序列化的格式
        result = {
            "date": df["date"].astype(str).tolist() if "date" in df.columns else [],
            "open": df["open"].tolist() if "open" in df.columns else [],
            "high": df["high"].tolist() if "high" in df.columns else [],
            "low": df["low"].tolist() if "low" in df.columns else [],
            "close": df["close"].tolist() if "close" in df.columns else [],
            "volume": df["volume"].tolist() if "volume" in df.columns else [],
            "amount": df["amount"].tolist() if "amount" in df.columns else [],
            "count": len(df)
        }
        
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 委托查询 ====================

@router.get("/orders")
async def get_orders(
    cancelable_only: bool = Query(default=False, description="是否只返回可撤单的委托")
):
    """
    查询当日所有委托
    
    Args:
        cancelable_only: 是否只返回可撤单的委托
    
    Returns:
        委托列表，包含订单编号、股票代码、委托类型、数量、价格、状态等
    """
    try:
        orders = qmt_service.get_orders(cancelable_only=cancelable_only)
        return success_response(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/summary")
async def get_orders_summary():
    """
    获取委托汇总信息
    
    Returns:
        委托汇总，包含各状态数量、买卖统计、成交金额等
    """
    try:
        summary = qmt_service.get_orders_summary()
        return success_response(summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/pending")
async def get_pending_orders():
    """
    查询未完成的委托（非最终状态）
    
    Returns:
        未完成的委托列表
    """
    try:
        orders = qmt_service.get_pending_orders()
        return success_response(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/completed")
async def get_completed_orders():
    """
    查询已完成的委托（最终状态）
    
    Returns:
        已完成的委托列表
    """
    try:
        orders = qmt_service.get_completed_orders()
        return success_response(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/successful")
async def get_successful_orders():
    """
    查询成交成功的委托
    
    Returns:
        成交成功的委托列表
    """
    try:
        orders = qmt_service.get_successful_orders()
        return success_response(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/canceled")
async def get_canceled_orders():
    """
    查询已撤销的委托
    
    Returns:
        已撤销的委托列表
    """
    try:
        orders = qmt_service.get_canceled_orders()
        return success_response(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/failed")
async def get_failed_orders():
    """
    查询废单
    
    Returns:
        废单列表
    """
    try:
        orders = qmt_service.get_failed_orders()
        return success_response(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/cancelable")
async def get_cancelable_orders():
    """
    查询可撤单的委托
    
    Returns:
        可撤单的委托列表
    """
    try:
        orders = qmt_service.get_cancelable_orders()
        return success_response(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/by-id/{order_id}")
async def get_order_by_id(order_id: int):
    """
    根据订单编号查询委托
    
    Args:
        order_id: 订单编号（策略端生成）
    
    Returns:
        委托信息
    """
    try:
        order = qmt_service.get_order_by_id(order_id)
        if order:
            return success_response(order)
        else:
            return success_response(None, msg=f"未找到订单 {order_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/by-sysid/{order_sysid}")
async def get_order_by_sysid(order_sysid: str):
    """
    根据柜台合同编号查询委托
    
    Args:
        order_sysid: 柜台合同编号
    
    Returns:
        委托信息
    """
    try:
        order = qmt_service.get_order_by_sysid(order_sysid)
        if order:
            return success_response(order)
        else:
            return success_response(None, msg=f"未找到柜台合同编号为 {order_sysid} 的订单")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/by-stock/{stock_code}")
async def get_orders_by_stock(stock_code: str):
    """
    查询指定股票的所有委托
    
    Args:
        stock_code: 股票代码（如：600519 或 600519.SH）
    
    Returns:
        该股票的委托列表
    """
    try:
        orders = qmt_service.get_orders_by_stock(stock_code)
        return success_response(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/by-status/{status}")
async def get_orders_by_status(status: int):
    """
    查询指定状态的委托
    
    Args:
        status: 委托状态码
            - 48: 未报
            - 49: 待报
            - 50: 已报
            - 51: 已报待撤
            - 52: 部成待撤
            - 53: 部撤
            - 54: 已撤
            - 55: 部成
            - 56: 已成
            - 57: 废单
    
    Returns:
        指定状态的委托列表
    """
    try:
        orders = qmt_service.get_orders_by_status(status)
        return success_response(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 撤单接口 ====================

@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: int):
    """
    撤销委托
    
    Args:
        order_id: 订单编号（策略端生成）
    
    Returns:
        撤单结果
    """
    try:
        result = qmt_service.cancel_order(order_id)
        if result.get("success"):
            return success_response(result, msg="撤单请求已提交")
        else:
            return error_response(msg=result.get("error", "撤单失败"), code=400, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/cancel-by-sysid/{order_sysid}")
async def cancel_order_by_sysid(order_sysid: str):
    """
    根据柜台合同编号撤销委托
    
    Args:
        order_sysid: 柜台合同编号
    
    Returns:
        撤单结果
    """
    try:
        result = qmt_service.cancel_order_by_sysid(order_sysid)
        if result.get("success"):
            return success_response(result, msg="撤单请求已提交")
        else:
            return error_response(msg=result.get("error", "撤单失败"), code=400, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/cancel-by-stock/{stock_code}")
async def cancel_orders_by_stock(stock_code: str):
    """
    撤销指定股票的所有可撤委托
    
    Args:
        stock_code: 股票代码
    
    Returns:
        批量撤单结果
    """
    try:
        result = qmt_service.cancel_orders_by_stock(stock_code)
        if result.get("success"):
            return success_response(result, msg=result.get("message", "撤单完成"))
        else:
            return error_response(msg=result.get("message", "撤单失败"), code=400, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/cancel-all")
async def cancel_all_orders():
    """
    撤销所有可撤委托
    
    Returns:
        批量撤单结果
    """
    try:
        result = qmt_service.cancel_all_orders()
        if result.get("success"):
            return success_response(result, msg=result.get("message", "撤单完成"))
        else:
            return error_response(msg=result.get("message", "撤单失败"), code=400, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 事件总线状态 ====================

@router.get("/event-bus/status")
async def get_event_bus_status():
    """
    获取QMT事件总线状态
    
    Returns:
        事件总线状态，包含模式（redis/memory）、连接状态、订阅者数量等
    """
    try:
        from app.services.qmt_service import qmt_event_bus
        status = qmt_event_bus.get_status()
        return success_response(status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
