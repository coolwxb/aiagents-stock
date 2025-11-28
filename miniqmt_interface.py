#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniQMT量化交易接口
为监测板块提供量化交易功能预留接口
支持自动下单、仓位管理、策略执行等功能
"""

import json
from tkinter import NO
from turtle import pos
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from xtquant import xtdata
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from xtquant import xtconstant
import time

# 单例交易连接实例，由 get_xttrader 管理
xt_trader = None


class TradeAction(Enum):
    """交易动作枚举"""
    BUY = "buy"  # 买入
    SELL = "sell"  # 卖出
    HOLD = "hold"  # 持有
    
class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "market"  # 市价单
    LIMIT = "limit"  # 限价单
    STOP = "stop"  # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单

class PositionSide(Enum):
    """持仓方向枚举"""
    LONG = "long"  # 多头
    SHORT = "short"  # 空头
    NONE = "none"  # 无持仓

# 交易回调类
class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        """
        连接断开
        :return:
        """
        print("connection lost, 交易接口断开，即将重连")
        global xt_trader
        xt_trader = None
    
    def on_stock_order(self, order):
        print(f'委托回报: 股票代码:{order.stock_code} 账号:{order.account_id}, 订单编号:{order.order_id} 柜台合同编号:{order.order_sysid} \
            委托状态:{order.order_status} 成交数量:{order.order_status} 委托数量:{order.order_volume} 已成数量：{order.traded_volume}')
        
    def on_stock_trade(self, trade):
        print(f'成交回报: 股票代码:{trade.stock_code} 账号:{trade.account_id}, 订单编号:{trade.order_id} 柜台合同编号:{trade.order_sysid} \
            成交编号:{trade.traded_id} 成交数量:{trade.traded_volume} 委托数量:{trade.direction} ')

    def on_order_error(self, order_error):
        print(f"报单失败： 订单编号：{order_error.order_id} 下单失败具体信息:{order_error.error_msg} 委托备注:{order_error.order_remark}")

    def on_cancel_error(self, cancel_error):
        print(f"撤单失败: 订单编号：{cancel_error.order_id} 失败具体信息:{cancel_error.error_msg} 市场：{cancel_error.market}")

    def on_order_stock_async_response(self, response):
        print(f"异步下单的请求序号:{response.seq}, 订单编号：{response.order_id} ")

    def on_account_status(self, status):
        print(f"账号状态发生变化， 账号:{status.account_id} 最新状态：{status.status}")

# 创建交易接口
def create_trader(xt_acc,path, session_id):
    trader = XtQuantTrader(path, session_id,callback=MyXtQuantTraderCallback())
    trader.start()
    connect_result = trader.connect()
    trader.subscribe(xt_acc)
    return trader if connect_result == 0 else None

# 尝试连接交易接口
def try_connect(xt_acc,path):
    session_id_range = [i for i in range(100, 130)]

    import random
    random.shuffle(session_id_range)

    # 遍历尝试session_id列表尝试连接
    for session_id in session_id_range:
        trader = create_trader(xt_acc,path, session_id)
        if trader:
            print(f'连接成功，session_id:{session_id}')
            return trader
        else:
            print(f'连接失败，session_id:{session_id}，继续尝试下一个id')
            continue

    print('所有id都尝试后仍失败，放弃连接')
    return None

# 获取交易接口
def get_xttrader(xt_acc,path):
    global xt_trader
    if xt_trader is None:
        xt_trader = try_connect(xt_acc,path)
    return xt_trader   

class MiniQMTInterface:
    """
    MiniQMT量化交易接口类
    提供与MiniQMT的对接功能
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化接口
        
        Args:
            config: 配置字典，包含账户信息、连接参数等
        """
        self.config = config or {}
        self.connected = False
        self.account_id = None
        self.account_type = None # 账户类型 stock 股票账户，credit 信用账户
        self.userdata_path = None # 用户数据路径
        self.positions = {}  # 持仓信息
        self.orders = {}  # 订单信息
        self.enabled = self.config.get('enabled', False)
        self.stock_account = None
        self.xt_trader = None



        
    def connect(self, account_id: str = None, account_type: str = None, userdata_path: str = None) -> Tuple[bool, str]:
        """
        连接到MiniQMT
        
        Args:
            account_id: 交易账户ID
            
        Returns:
            (成功标志, 消息)
        """
        try:
            # 实现与MiniQMT的实际连接逻辑
            self.account_id = account_id or self.config.get('account_id')
            self.account_type = account_type or self.config.get('account_type', 'STOCK')
            self.userdata_path = userdata_path or self.config.get('userdata_path')
            
            if not self.account_id:
                return False, "账户ID未配置"
            if not self.account_type:
                return False, "账户类型未配置"
            if not self.userdata_path:
                return False, "用户数据路径未配置"
            
            # 连接MiniQMT
            self.stock_account = StockAccount(self.account_id, self.account_type)
            self.xt_trader = get_xttrader(self.stock_account, self.userdata_path)
            if not self.xt_trader:
                return False, "交易接口连接失败"
            self.connected = True
            return True, f"已连接到账户 {self.account_id}"
            
        except Exception as e:
            self.connected = False
            return False, f"连接失败: {str(e)}"
    
    def disconnect(self) -> bool:
        """断开连接"""
        try:
            if self.xt_trader:
                self.xt_trader.disconnect()
                self.xt_trader = None
            self.connected = False
            return True
        except Exception as e:
            print(f"断开连接失败: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected and self.enabled
    
    def get_account_info(self) -> Dict:
        """
        获取账户信息
        
        Returns:
            账户信息字典
        """
        if not self.is_connected():
            return {
                'error': '未连接到MiniQMT',
                'connected': False
            }
        
       
        # 从MiniQMT获取账户信息
        #取账号信息
        if self.account_type == 'STOCK':
            account_info = self.xt_trader.query_stock_asset(self.stock_account)
        elif self.account_type == 'CREDIT':
            account_info = self.xt_trader.query_credit_detail(self.credit_account)
        return {
            'account_id': account_info.account_id,
            'total_assets': account_info.total_asset,  # 总资产
            'available_cash': account_info.cash,  # 可用资金
            'market_value': account_info.market_value,  # 持仓市值
            'frozen_cash': account_info.frozen_cash,  # 冻结资金
            'profit_loss': account_info.total_asset-account_info.cash-account_info.frozen_cash-account_info.market_value,  # 盈亏
            'connected': True
        }
    
    def get_positions(self) -> List[Dict]:
        """
        获取当前持仓
        
        Returns:
            持仓列表
        """
        if not self.is_connected():
            return []
        
        
        # 从MiniQMT获取持仓信息
        if self.account_type == 'STOCK':
            positions = self.xt_trader.query_stock_positions(self.stock_account)
        elif self.account_type == 'CREDIT':
            positions = self.xt_trader.query_credit_subjects(self.credit_account)
        return positions
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        获取指定股票的持仓
        
        Args:
            symbol: 股票代码
            
        Returns:
            持仓信息字典，无持仓返回None
        """
        if not self.is_connected():
            return None
        # 遍历持仓信息
        for position in self.positions:
            if position.stock_code == symbol:
                # 获取持仓可用数量
                available_quantity = position.can_use_volume
                if available_quantity > 0:
                    return position.to_dict()
        return None
    
    def place_order(self, 
                   symbol: str, 
                   action: TradeAction,
                   quantity: int,
                   price: float = None,
                   order_type: OrderType = OrderType.MARKET) -> Tuple[bool, str, str]:
        """
        下单
        
        Args:
            symbol: 股票代码
            action: 交易动作
            quantity: 数量
            price: 价格（限价单时需要）
            order_type: 订单类型
            
        Returns:
            (成功标志, 消息, 订单ID)
        """
        if not self.is_connected():
            return False, "未连接到MiniQMT", ""
        
        # 参数验证
        if quantity <= 0:
            return False, "数量必须大于0", ""
        
        if order_type == OrderType.LIMIT and price is None:
            return False, "限价单必须指定价格", ""
        
        try:
            
            # 预留接口：通过MiniQMT下单
            if action == TradeAction.BUY:
                order_id = self.xt_trader.order_stock_async(self.stock_account,
                 symbol, xtconstant.STOCK_BUY, quantity, xtconstant.FIX_PRICE, price, 'strategy_name', f'买入{symbol}')

            elif action == TradeAction.SELL:
                order_id = self.xt_trader.order_stock_async(
                    self.stock_account, symbol, 
                    xtconstant.STOCK_SELL, quantity, xtconstant.FIX_PRICE, price, 'strategy_name', f'卖出{symbol}')
            if order_id == -1:
                return False, "下单失败", None
            return True, f"订单已提交: {order_id}", str(order_id)
            
        except Exception as e:
            return False, f"下单失败: {str(e)}", ""
    
    def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """
        撤销订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            (成功标志, 消息)
        """
        if not self.is_connected():
            return False, "未连接到MiniQMT"
        
        try:
            # 通过MiniQMT撤单
            cancel_result = self.xt_trader.cancel_order_stock_async(self.stock_account, order_id)
            if cancel_result == -1:
                return False, "撤单失败"
            return True, f"订单 {order_id} 已撤销", f"委托序号:{cancel_result}"
        except Exception as e:
            return False, f"撤单失败: {str(e)}"
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单信息字典
        """
        if not self.is_connected():
            return None
        
        # TODO: 实现查询订单状态逻辑
        return self.orders.get(order_id)
    
    def get_all_orders(self) -> List[Dict]:
        """
        获取所有订单
        
        Returns:
            订单列表
        """
        if not self.is_connected():
            return []
        
        return list(self.orders.values())
    
    def execute_strategy_signal(self, 
                                stock_id: int,
                                symbol: str,
                                signal: Dict,
                                position_size: float = 0.2) -> Tuple[bool, str]:
        """
        执行策略信号
        根据监测触发的信号自动执行交易
        
        Args:
            stock_id: 监测股票ID
            symbol: 股票代码
            signal: 信号字典，包含type, price, message等
            position_size: 仓位比例（默认20%）
            
        Returns:
            (成功标志, 执行结果消息)
        """
        if not self.is_connected():
            return False, "MiniQMT未连接，无法执行交易"
        
        signal_type = signal.get('type')
        current_price = signal.get('price')
        
        try:
            # 获取账户信息
            account_info = self.get_account_info()
            available_cash = account_info.get('available_cash', 0)
            
            # 根据信号类型执行不同操作
            if signal_type == 'entry':
                # 进场信号 - 买入
                buy_amount = available_cash * position_size
                quantity = int(buy_amount / current_price / 100) * 100  # A股100股为一手
                
                if quantity > 0:
                    success, msg, order_id = self.place_order(
                        symbol=symbol,
                        action=TradeAction.BUY,
                        quantity=quantity,
                        price=current_price,
                        order_type=OrderType.LIMIT
                    )
                    
                    if success:
                        return True, f"进场买入成功: {quantity}股 @ ¥{current_price}, 订单号: {order_id}"
                    else:
                        return False, f"进场买入失败: {msg}"
                else:
                    return False, "可用资金不足，无法买入"
            
            elif signal_type == 'take_profit':
                # 止盈信号 - 卖出
                position = self.get_position(symbol)
                if position and position.get('quantity', 0) > 0:
                    quantity = position['quantity']
                    
                    success, msg, order_id = self.place_order(
                        symbol=symbol,
                        action=TradeAction.SELL,
                        quantity=quantity,
                        price=current_price,
                        order_type=OrderType.LIMIT
                    )
                    
                    if success:
                        return True, f"止盈卖出成功: {quantity}股 @ ¥{current_price}, 订单号: {order_id}"
                    else:
                        return False, f"止盈卖出失败: {msg}"
                else:
                    return False, "无持仓，无需卖出"
            
            elif signal_type == 'stop_loss':
                # 止损信号 - 紧急卖出
                position = self.get_position(symbol)
                if position and position.get('quantity', 0) > 0:
                    quantity = position['quantity']
                    
                    # 止损使用市价单，快速成交
                    success, msg, order_id = self.place_order(
                        symbol=symbol,
                        action=TradeAction.SELL,
                        quantity=quantity,
                        order_type=OrderType.MARKET
                    )
                    
                    if success:
                        return True, f"止损卖出成功: {quantity}股, 订单号: {order_id}"
                    else:
                        return False, f"止损卖出失败: {msg}"
                else:
                    return False, "无持仓，无需止损"
            
            else:
                return False, f"未知的信号类型: {signal_type}"
                
        except Exception as e:
            return False, f"执行策略信号失败: {str(e)}"
    
    def calculate_position_size(self, 
                               symbol: str,
                               price: float,
                               max_position_pct: float = 0.2,
                               max_risk_pct: float = 0.02) -> int:
        """
        计算建议仓位大小
        
        Args:
            symbol: 股票代码
            price: 买入价格
            max_position_pct: 最大仓位比例（默认20%）
            max_risk_pct: 最大风险比例（默认2%）
            
        Returns:
            建议买入数量（股）
        """
        if not self.is_connected():
            return 0
        
        try:
            account_info = self.get_account_info()
            total_assets = account_info.get('total_assets', 0)
            available_cash = account_info.get('available_cash', 0)
            
            # 基于最大仓位计算
            max_position_value = total_assets * max_position_pct
            
            # 基于可用资金计算
            max_buy_value = min(max_position_value, available_cash)
            
            # 计算股数（A股100股为一手）
            quantity = int(max_buy_value / price / 100) * 100
            
            return quantity
            
        except Exception as e:
            print(f"计算仓位失败: {e}")
            return 0
    
    def get_risk_metrics(self, symbol: str) -> Dict:
        """
        获取风险指标
        
        Args:
            symbol: 股票代码
            
        Returns:
            风险指标字典
        """
        if not self.is_connected():
            return {}
        
        position = self.get_position(symbol)
        if not position:
            return {
                'has_position': False,
                'profit_loss': 0,
                'profit_loss_pct': 0,
                'risk_exposure': 0
            }
        
        # 计算盈亏
        cost_price = position.get('cost_price', 0)
        current_price = position.get('current_price', 0)
        quantity = position.get('quantity', 0)
        
        profit_loss = (current_price - cost_price) * quantity
        profit_loss_pct = (current_price - cost_price) / cost_price * 100 if cost_price > 0 else 0
        
        # 计算风险敞口
        account_info = self.get_account_info()
        total_assets = account_info.get('total_assets', 0)
        position_value = current_price * quantity
        risk_exposure = position_value / total_assets if total_assets > 0 else 0
        
        return {
            'has_position': True,
            'quantity': quantity,
            'cost_price': cost_price,
            'current_price': current_price,
            'position_value': position_value,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct,
            'risk_exposure': risk_exposure
        }
    
    def validate_trade(self, 
                      symbol: str,
                      action: TradeAction,
                      quantity: int,
                      price: float = None) -> Tuple[bool, str]:
        """
        验证交易是否可行
        
        Args:
            symbol: 股票代码
            action: 交易动作
            quantity: 数量
            price: 价格
            
        Returns:
            (可行标志, 原因)
        """
        if not self.is_connected():
            return False, "未连接到MiniQMT"
        
        # 检查数量
        if quantity <= 0:
            return False, "数量必须大于0"
        
        if quantity % 100 != 0:
            return False, "A股必须以100股（1手）为单位交易"
        
        # 获取账户信息
        account_info = self.get_account_info()
        
        if action == TradeAction.BUY:
            # 买入验证
            if price is None:
                return False, "买入需要指定价格"
            
            required_cash = quantity * price * 1.001  # 考虑手续费
            available_cash = account_info.get('available_cash', 0)
            
            if required_cash > available_cash:
                return False, f"资金不足: 需要¥{required_cash:.2f}, 可用¥{available_cash:.2f}"
            
            return True, "验证通过"
        
        elif action == TradeAction.SELL:
            # 卖出验证
            position = self.get_position(symbol)
            if not position:
                return False, "无持仓，无法卖出"
            
            available_quantity = position['can_use_volume']
            if quantity > available_quantity:
                return False, f"持仓不足: 需要{quantity}股, 可用{available_quantity}股"
            
            return True, "验证通过"
        
        return False, "未知的交易动作"


class QuantStrategyConfig:
    """量化策略配置"""
    
    def __init__(self):
        self.auto_trade_enabled = False  # 是否启用自动交易
        self.max_position_pct = 0.2  # 最大单个仓位比例
        self.max_total_position_pct = 0.8  # 最大总仓位比例
        self.max_risk_per_trade = 0.02  # 单笔最大风险比例
        self.min_trade_amount = 5000  # 最小交易金额
        self.use_stop_loss = True  # 是否使用止损
        self.use_take_profit = True  # 是否使用止盈
        self.trailing_stop_pct = 0.05  # 移动止损比例
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'auto_trade_enabled': self.auto_trade_enabled,
            'max_position_pct': self.max_position_pct,
            'max_total_position_pct': self.max_total_position_pct,
            'max_risk_per_trade': self.max_risk_per_trade,
            'min_trade_amount': self.min_trade_amount,
            'use_stop_loss': self.use_stop_loss,
            'use_take_profit': self.use_take_profit,
            'trailing_stop_pct': self.trailing_stop_pct
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """从字典创建"""
        config = cls()
        config.auto_trade_enabled = data.get('auto_trade_enabled', False)
        config.max_position_pct = data.get('max_position_pct', 0.2)
        config.max_total_position_pct = data.get('max_total_position_pct', 0.8)
        config.max_risk_per_trade = data.get('max_risk_per_trade', 0.02)
        config.min_trade_amount = data.get('min_trade_amount', 5000)
        config.use_stop_loss = data.get('use_stop_loss', True)
        config.use_take_profit = data.get('use_take_profit', True)
        config.trailing_stop_pct = data.get('trailing_stop_pct', 0.05)
        return config


# 全局MiniQMT接口实例
miniqmt = MiniQMTInterface()


def init_miniqmt(config: Dict = None) -> Tuple[bool, str]:
    """
    初始化MiniQMT接口
    
    Args:
        config: 配置字典
        
    Returns:
        (成功标志, 消息)
    """
    global miniqmt
    
    try:
        # 从配置文件或环境变量读取配置
        if config is None:
            try:
                from config import MINIQMT_CONFIG
                config = MINIQMT_CONFIG
            except ImportError:
                config = {
                    'enabled': False,
                    'account_id': None
                }
        
        miniqmt = MiniQMTInterface(config)
        
        # 如果启用，尝试连接
        if config.get('enabled', False):
            success, msg = miniqmt.connect()
            return success, msg
        else:
            return True, "MiniQMT接口已初始化（未启用）"
            
    except Exception as e:
        return False, f"初始化MiniQMT接口失败: {str(e)}"


def get_miniqmt_status() -> Dict:
    """
    获取MiniQMT接口状态
    
    Returns:
        状态字典
    """
    global miniqmt
    
    return {
        'enabled': miniqmt.enabled,
        'connected': miniqmt.connected,
        'account_id': miniqmt.account_id,
        'ready': miniqmt.is_connected()
    }


def main():
    """
    简易本地测试入口：
    1. 准备真实的账户配置（account_id/account_type/userdata_path）
    2. 运行脚本观察各接口方法的执行结果
    """
    sample_config = {
        'enabled': True,
        'account_id': '8004016386',
        'account_type': 'STOCK',
        'userdata_path': 'E:\\zhongjin_qmt\\userdata_mini'
    }

    success, message = init_miniqmt(sample_config)
    print(f'[MiniQMT] 初始化: {message}')

    status = get_miniqmt_status()
    print('[MiniQMT] 当前状态:')
    print(json.dumps(status, ensure_ascii=False, indent=2))

    if not success or not status.get('ready'):
        print('接口未就绪，确认MiniQMT客户端已启动、配置正确后再试。')
        return

    interface = miniqmt

    account_info = interface.get_account_info()
    print('[MiniQMT] 账户信息:')
    print(json.dumps(account_info, ensure_ascii=False, indent=2))

    positions = interface.get_positions()
    print(f'[MiniQMT] 当前持仓数量: {len(positions)}')
    

    demo_symbol = '600000.SH'
    target_price = 10.5
    quantity = interface.calculate_position_size(demo_symbol, target_price)
    print(f'[MiniQMT] 建议买入数量: {quantity}')

    valid, reason = interface.validate_trade(
        symbol=demo_symbol,
        action=TradeAction.BUY,
        quantity=quantity or 100,
        price=target_price
    )
    print(f'[MiniQMT] 买入验证: {valid}, 原因: {reason}')

    # risk_metrics = interface.get_risk_metrics(demo_symbol)
    # print('[MiniQMT] 风险指标:')
    # print(json.dumps(risk_metrics, ensure_ascii=False, indent=2))

    # signal = {
    #     'type': 'entry',
    #     'price': target_price,
    #     'message': '演示进场信号'
    # }
    # executed, exec_msg = interface.execute_strategy_signal(
    #     stock_id=1,
    #     symbol=demo_symbol,
    #     signal=signal,
    #     position_size=0.1
    # )
    # print(f'[MiniQMT] 信号执行: {executed}, 信息: {exec_msg}')


if __name__ == '__main__':
    main()
