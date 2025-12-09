"""
GS策略监控调度器
负责管理监控任务的线程调度、策略执行和信号处理
"""
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional

import pandas as pd

from app.policy.gs import compute_g_buy_sell, load_xtquant_kline
from app.services.notification_service import get_notification_service
from app.services.qmt_service import qmt_event_bus, QMTEventBus, OrderStatus


class GSScheduler:
    """
    GS策略监控调度器
    
    使用单例模式管理所有监控任务的线程
    """
    
    # 单例实例
    _instance = None
    
    # 类级别的线程管理
    _monitoring_threads: Dict[int, threading.Thread] = {}
    _stop_flags: Dict[int, threading.Event] = {}
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = logging.getLogger(__name__)
        self._initialized = True
        
        # 订阅订单状态事件
        self._subscribe_order_events()
        
        self.logger.info("GS策略调度器初始化完成")
    
    def _subscribe_order_events(self):
        """订阅QMT订单状态事件"""
        qmt_event_bus.subscribe(QMTEventBus.EVENT_ORDER_STATUS, self._on_order_status)
        qmt_event_bus.subscribe(QMTEventBus.EVENT_ORDER_ERROR, self._on_order_error)
        self.logger.info("已订阅QMT订单状态事件")
    
    def _on_order_status(self, data: Dict):
        """
        处理订单状态变化事件
        
        Args:
            data: 订单状态数据，包含:
                - order_id: 订单ID
                - order_status: 状态码
                - order_status_name: 状态名称
                - is_final: 是否最终状态
                - is_success: 是否成功(状态码56)
                - stock_code: 股票代码
                - traded_volume: 成交数量
                - traded_price: 成交价格
        """
        from app.db.gs_strategy_db import gs_strategy_db
        
        try:
            order_id = str(data.get('order_id', ''))
            order_status = data.get('order_status')
            order_status_name = data.get('order_status_name', '')
            is_final = data.get('is_final', False)
            is_success = data.get('is_success', False)
            stock_code = data.get('stock_code', '')
            
            self.logger.info(f"收到订单状态更新: order_id={order_id}, status={order_status}({order_status_name}), is_final={is_final}")
            
            if not order_id:
                return
            
            # 查找对应的交易记录（买入或卖出）
            trade = gs_strategy_db.get_trade_by_order_id(order_id)
            
            if not trade:
                self.logger.debug(f"未找到订单 {order_id} 对应的交易记录")
                return
            
            monitor_id = trade.get('monitor_id')
            
            # 判断是买入还是卖出订单
            is_buy_order = trade.get('buy_order_id') == order_id
            is_sell_order = trade.get('sell_order_id') == order_id
            
            update_data = {}
            
            if is_buy_order:
                update_data['buy_order_status'] = order_status
                update_data['buy_order_status_name'] = order_status_name
                
                # 如果买入成功，更新成交价格
                if is_success:
                    traded_price = data.get('traded_price', 0)
                    if traded_price > 0:
                        update_data['buy_price'] = traded_price
                    self.logger.info(f"买入订单成交: {stock_code}, order_id={order_id}")
                elif is_final and not is_success:
                    # 买入失败（已撤、废单等）
                    self.logger.warning(f"买入订单未成交: {stock_code}, status={order_status_name}")
                    
            elif is_sell_order:
                update_data['sell_order_status'] = order_status
                update_data['sell_order_status_name'] = order_status_name
                
                # 如果卖出成功，更新成交价格和盈亏
                if is_success:
                    traded_price = data.get('traded_price', 0)
                    if traded_price > 0:
                        update_data['sell_price'] = traded_price
                        # 重新计算盈亏
                        buy_price = trade.get('buy_price', 0)
                        buy_quantity = trade.get('buy_quantity', 0)
                        if buy_price and buy_quantity:
                            update_data['profit_loss'] = (traded_price - buy_price) * buy_quantity
                            update_data['profit_loss_pct'] = ((traded_price - buy_price) / buy_price) * 100
                    self.logger.info(f"卖出订单成交: {stock_code}, order_id={order_id}")
                elif is_final and not is_success:
                    self.logger.warning(f"卖出订单未成交: {stock_code}, status={order_status_name}")
            
            # 更新交易记录
            if update_data:
                gs_strategy_db.update_trade_history(trade['id'], update_data)
                self.logger.debug(f"已更新交易记录 {trade['id']}: {update_data}")
            
            # 更新监控任务的委托状态
            if monitor_id:
                monitor_update = {
                    'pending_order_status': order_status,
                    'pending_order_status_name': order_status_name
                }
                # 如果是最终状态，清除待处理订单信息
                if is_final:
                    monitor_update['pending_order_id'] = None
                    monitor_update['pending_order_type'] = None
                    monitor_update['pending_order_status'] = None
                    monitor_update['pending_order_status_name'] = None
                    self.logger.info(f"监控任务 {monitor_id} 委托已完成，清除待处理状态")
                
                gs_strategy_db.update_monitor(monitor_id, **monitor_update)
                
        except Exception as e:
            self.logger.error(f"处理订单状态事件失败: {e}")
    
    def _on_order_error(self, data: Dict):
        """
        处理订单错误事件
        
        Args:
            data: 错误数据，包含:
                - order_id: 订单ID
                - error_id: 错误码
                - error_msg: 错误信息
        """
        from app.db.gs_strategy_db import gs_strategy_db
        
        try:
            order_id = str(data.get('order_id', ''))
            error_msg = data.get('error_msg', '')
            
            self.logger.error(f"订单错误: order_id={order_id}, error={error_msg}")
            
            if not order_id:
                return
            
            # 查找对应的交易记录
            trade = gs_strategy_db.get_trade_by_order_id(order_id)
            
            if not trade:
                return
            
            monitor_id = trade.get('monitor_id')
            
            # 判断是买入还是卖出订单
            is_buy_order = trade.get('buy_order_id') == order_id
            
            update_data = {}
            if is_buy_order:
                update_data['buy_order_status'] = OrderStatus.JUNK  # 废单
                update_data['buy_order_status_name'] = f'失败: {error_msg}'
            else:
                update_data['sell_order_status'] = OrderStatus.JUNK
                update_data['sell_order_status_name'] = f'失败: {error_msg}'
            
            gs_strategy_db.update_trade_history(trade['id'], update_data)
            
            # 清除监控任务的待处理订单状态（订单失败）
            if monitor_id:
                gs_strategy_db.update_monitor(
                    monitor_id,
                    pending_order_id=None,
                    pending_order_type=None,
                    pending_order_status=None,
                    pending_order_status_name=None
                )
                self.logger.info(f"监控任务 {monitor_id} 订单失败，清除待处理状态")
            
        except Exception as e:
            self.logger.error(f"处理订单错误事件失败: {e}")

    # ==================== 监控线程管理方法 ====================
    
    def start_monitor(self, monitor_id: int, interval: int, stock_code: str, stock_name: str) -> bool:
        """
        启动监控任务线程
        
        Args:
            monitor_id: 监控任务ID
            interval: 监测间隔（秒）
            stock_code: 股票代码
            stock_name: 股票名称
            
        Returns:
            是否启动成功
        """
        with self._lock:
            # 检查是否已有运行中的线程
            if monitor_id in self._monitoring_threads:
                existing_thread = self._monitoring_threads[monitor_id]
                if existing_thread.is_alive():
                    self.logger.warning(f"监控任务 {monitor_id} 已在运行中")
                    return False
            
            # 创建停止标志
            stop_flag = threading.Event()
            self._stop_flags[monitor_id] = stop_flag
            
            # 创建并启动监控线程
            thread = threading.Thread(
                target=self._monitor_loop,
                args=(monitor_id, interval, stock_code, stock_name, stop_flag),
                name=f"GSMonitor-{monitor_id}-{stock_code}",
                daemon=True
            )
            
            self._monitoring_threads[monitor_id] = thread
            thread.start()
            
            self.logger.info(f"监控任务 {monitor_id} ({stock_code}) 已启动，间隔: {interval}秒")
            return True
    
    def stop_monitor(self, monitor_id: int, timeout: float = 5.0) -> bool:
        """
        停止监控任务线程
        
        Args:
            monitor_id: 监控任务ID
            timeout: 等待线程结束的超时时间（秒）
            
        Returns:
            是否停止成功
        """
        with self._lock:
            # 检查是否存在该监控任务
            if monitor_id not in self._stop_flags:
                self.logger.warning(f"监控任务 {monitor_id} 不存在或已停止")
                return True
            
            # 设置停止标志
            stop_flag = self._stop_flags[monitor_id]
            stop_flag.set()
            
            # 等待线程结束
            if monitor_id in self._monitoring_threads:
                thread = self._monitoring_threads[monitor_id]
                if thread.is_alive():
                    thread.join(timeout=timeout)
                    
                    if thread.is_alive():
                        self.logger.warning(f"监控任务 {monitor_id} 线程未能在 {timeout}秒内结束")
                    else:
                        self.logger.info(f"监控任务 {monitor_id} 已停止")
                
                # 清理线程引用
                del self._monitoring_threads[monitor_id]
            
            # 清理停止标志
            del self._stop_flags[monitor_id]
            
            return True
    
    def is_monitor_running(self, monitor_id: int) -> bool:
        """
        检查监控任务是否正在运行
        
        Args:
            monitor_id: 监控任务ID
            
        Returns:
            是否正在运行
        """
        with self._lock:
            if monitor_id not in self._monitoring_threads:
                return False
            
            thread = self._monitoring_threads[monitor_id]
            return thread.is_alive()
    
    def get_running_monitors(self) -> Dict[int, bool]:
        """
        获取所有监控任务的运行状态
        
        Returns:
            {monitor_id: is_running} 字典
        """
        with self._lock:
            return {
                monitor_id: thread.is_alive()
                for monitor_id, thread in self._monitoring_threads.items()
            }
    
    def _monitor_loop(self, monitor_id: int, interval: int, stock_code: str, 
                      stock_name: str, stop_flag: threading.Event):
        """
        监控任务主循环
        
        Args:
            monitor_id: 监控任务ID
            interval: 监测间隔（秒）
            stock_code: 股票代码
            stock_name: 股票名称
            stop_flag: 停止标志事件
        """
        self.logger.info(f"监控线程启动: {monitor_id} ({stock_code})")
        
        while not stop_flag.is_set():
            try:
                # 执行策略分析
                self._execute_strategy(monitor_id, stock_code, stock_name)
                
            except Exception as e:
                self.logger.error(f"监控任务 {monitor_id} 执行异常: {e}")
            
            # 等待下一次执行，使用 wait 以便能够响应停止信号
            stop_flag.wait(timeout=interval)
        
        self.logger.info(f"监控线程结束: {monitor_id} ({stock_code})")

    # ==================== 策略执行方法 ====================
    
    def _execute_strategy(self, monitor_id: int, stock_code: str, stock_name: str):
        """
        执行GS策略分析
        
        Args:
            monitor_id: 监控任务ID
            stock_code: 股票代码
            stock_name: 股票名称
        """
        from app.db.gs_strategy_db import gs_strategy_db
        
        try:
            # 获取监控任务（使用gs_strategy_db）
            monitor = gs_strategy_db.get_monitor(monitor_id)
            if not monitor:
                self.logger.error(f"监控任务 {monitor_id} 不存在")
                return
            
            # 获取K线数据并计算GS信号
            signal_data = self._compute_gs_signal(stock_code)
            
            if signal_data is None:
                self.logger.warning(f"无法获取 {stock_code} 的K线数据")
                return
            
            # 更新执行次数
            execution_count = (monitor.get('execution_count') or 0) + 1
            
            # 处理信号
            g_buy = signal_data.get('g_buy', 0)
            g_sell = signal_data.get('g_sell', 0)

            g_buy =1
            
            if g_buy == 1:
                # 买入信号
                gs_strategy_db.update_monitor(
                    monitor_id,
                    last_signal='buy',
                    last_signal_time=datetime.now().isoformat(),
                    execution_count=execution_count
                )
                
                # 处理买入
                self._handle_buy_signal(monitor_id, stock_code, stock_name, signal_data)
                
            elif g_sell == 1:
                # 卖出信号
                gs_strategy_db.update_monitor(
                    monitor_id,
                    last_signal='sell',
                    last_signal_time=datetime.now().isoformat(),
                    execution_count=execution_count
                )
                
                # 处理卖出
                self._handle_sell_signal(monitor_id, stock_code, stock_name, signal_data)
                
            else:
                # 持有信号
                gs_strategy_db.update_monitor(
                    monitor_id,
                    last_signal='hold',
                    last_signal_time=datetime.now().isoformat(),
                    execution_count=execution_count
                )
                
                self.logger.debug(f"{stock_code} 无交易信号")
            
        except Exception as e:
            self.logger.error(f"执行策略失败 {stock_code}: {e}")
    
    def _compute_gs_signal(self, stock_code: str) -> Optional[Dict]:
        """
        计算GS买卖信号
        
        Args:
            stock_code: 股票代码
            
        Returns:
            信号数据字典，包含 g_buy, g_sell, close, BB, A 等字段
        """
        try:
            # 获取日期范围（最近200个交易日）
            end_date = datetime.now().strftime('%Y-%m-%d')
            # 往前推300天以确保有足够的数据
            start_date = (datetime.now() - pd.Timedelta(days=300)).strftime('%Y-%m-%d')
            
            # 加载K线数据
            df = load_xtquant_kline(stock_code, start_date, end_date, period='1d', count=200)
            
            if df is None or df.empty:
                self.logger.warning(f"获取 {stock_code} K线数据为空")
                return None
            
            # 计算GS信号
            df_result = compute_g_buy_sell(df)
            
            if df_result is None or df_result.empty:
                return None
            
            # 获取最新一行数据
            latest = df_result.iloc[-1]
            
            return {
                'g_buy': int(latest.get('g_buy', 0)),
                'g_sell': int(latest.get('g_sell', 0)),
                'close': float(latest.get('close', 0)),
                'open': float(latest.get('open', 0)),
                'high': float(latest.get('high', 0)),
                'low': float(latest.get('low', 0)),
                'BB': float(latest.get('BB', 0)) if pd.notna(latest.get('BB')) else 0,
                'A': float(latest.get('A', 0)) if pd.notna(latest.get('A')) else 0,
                'date': str(df_result.index[-1])
            }
            
        except Exception as e:
            self.logger.error(f"计算GS信号失败 {stock_code}: {e}")
            return None
    
    def _handle_buy_signal(self, monitor_id: int, stock_code: str, stock_name: str, 
                           signal_data: Dict):
        """
        处理买入信号
        
        Args:
            monitor_id: 监控任务ID
            stock_code: 股票代码
            stock_name: 股票名称
            signal_data: 信号数据
        """
        from app.db.gs_strategy_db import gs_strategy_db
        
        self.logger.info(f"检测到买入信号: {stock_code} ({stock_name})")
        
        # 检查是否有待处理的委托（防止重复下单）
        monitor = gs_strategy_db.get_monitor(monitor_id)
        if monitor:
            pending_order_id = monitor.get('pending_order_id')
            pending_order_status = monitor.get('pending_order_status')
            
            if pending_order_id and pending_order_status is not None:
                # 检查是否为非最终状态（未报、待报、已报、部成等）
                if not OrderStatus.is_final(pending_order_status):
                    self.logger.warning(
                        f"监控任务 {monitor_id} 有待处理的委托 (order_id={pending_order_id}, "
                        f"status={OrderStatus.get_name(pending_order_status)})，跳过本次买入"
                    )
                    return
        
        # 获取当前价格
        current_price = signal_data.get('close', 0)
        
        # 默认买入数量（可以根据配置调整）
        buy_quantity = 100  # 1手
        
        # 调用QMT买入接口
        from app.utils.qmt_client import qmt_client
        order_result = qmt_client.buy(stock_code, buy_quantity, current_price, 'market')
        
        # success 不代表最终成交，只代下单成功
        if order_result.get('success'):
            order_id = str(order_result.get('order_id', ''))
            
            # 更新监控任务的待处理委托状态
            gs_strategy_db.update_monitor(
                monitor_id,
                pending_order_id=order_id,
                pending_order_type='buy',
                pending_order_status=OrderStatus.REPORTED,
                pending_order_status_name='已报'
            )
            
            # 记录交易到gs_strategy_db（初始状态为"已报"，等待回调更新最终状态）
            gs_strategy_db.add_trade_history(
                monitor_id=monitor_id,
                stock_code=stock_code,
                stock_name=stock_name,
                buy_price=current_price,
                buy_quantity=buy_quantity,
                buy_time=datetime.now().isoformat(),
                buy_order_id=order_id,
                buy_order_status=OrderStatus.REPORTED,  # 初始状态：已报
                buy_order_status_name='已报',
                status='open',
                trade_details=json.dumps(signal_data, ensure_ascii=False)
            )
            
            self.logger.info(f"买入订单已提交: {stock_code}, 价格: {current_price}, 数量: {buy_quantity}, 等待成交回调")
            
            # 发送通知
            try:
                self._send_trade_notification(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    action='买入',
                    price=current_price,
                    quantity=buy_quantity,
                    order_id=order_id,
                    signal_data=signal_data
                )
            except Exception as e:
                self.logger.error(f"发送买入通知失败: {e}")
        else:
            error_msg = order_result.get('error', '未知错误')
            self.logger.error(f"买入订单失败: {stock_code}, 错误: {error_msg}")
            
            # 发送失败通知
            try:
                self._send_trade_notification(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    action='买入失败',
                    price=current_price,
                    quantity=buy_quantity,
                    order_id='',
                    signal_data=signal_data,
                    error=error_msg
                )
            except Exception as e:
                self.logger.error(f"发送买入失败通知失败: {e}")
    
    def _handle_sell_signal(self, monitor_id: int, stock_code: str, stock_name: str, 
                            signal_data: Dict):
        """
        处理卖出信号
        
        Args:
            monitor_id: 监控任务ID
            stock_code: 股票代码
            stock_name: 股票名称
            signal_data: 信号数据
        """
        from app.db.gs_strategy_db import gs_strategy_db
        from app.utils.qmt_client import qmt_client
        
        self.logger.info(f"检测到卖出信号: {stock_code} ({stock_name})")
        
        # 检查是否有待处理的委托（防止重复下单）
        monitor = gs_strategy_db.get_monitor(monitor_id)
        if monitor:
            pending_order_id = monitor.get('pending_order_id')
            pending_order_status = monitor.get('pending_order_status')
            
            if pending_order_id and pending_order_status is not None:
                # 检查是否为非最终状态
                if not OrderStatus.is_final(pending_order_status):
                    self.logger.warning(
                        f"监控任务 {monitor_id} 有待处理的委托 (order_id={pending_order_id}, "
                        f"status={OrderStatus.get_name(pending_order_status)})，跳过本次卖出"
                    )
                    return
        
        # 获取当前价格
        current_price = signal_data.get('close', 0)
        
        # 查询持仓
        position = qmt_client.get_position(stock_code)
        
        if not position or position.get('can_sell', 0) <= 0:
            self.logger.warning(f"无可卖持仓: {stock_code}")
            return
        
        sell_quantity = position.get('can_sell', 0)
        
        # 调用QMT卖出接口
        order_result = qmt_client.sell(stock_code, sell_quantity, current_price, 'market')
        
        if order_result.get('success'):
            order_id = str(order_result.get('order_id', ''))
            
            # 更新监控任务的待处理委托状态
            gs_strategy_db.update_monitor(
                monitor_id,
                pending_order_id=order_id,
                pending_order_type='sell',
                pending_order_status=OrderStatus.REPORTED,
                pending_order_status_name='已报'
            )
            
            # 查找对应的未平仓交易记录
            open_trade = gs_strategy_db.get_open_trade(monitor_id)
            
            profit_loss = None
            profit_loss_pct = None
            
            if open_trade:
                # 计算盈亏（预估，最终以成交回调为准）
                buy_price = open_trade.get('buy_price', 0)
                buy_quantity = open_trade.get('buy_quantity', 0)
                if buy_price and buy_quantity:
                    profit_loss = (current_price - buy_price) * buy_quantity
                    profit_loss_pct = ((current_price - buy_price) / buy_price) * 100
                
                # 更新交易详情
                trade_details = json.loads(open_trade.get('trade_details', '{}') or '{}')
                trade_details['sell_signal'] = signal_data
                
                # 更新交易记录（初始状态为"已报"，等待回调更新最终状态）
                gs_strategy_db.update_trade_history(open_trade['id'], {
                    'sell_price': current_price,
                    'sell_quantity': sell_quantity,
                    'sell_time': datetime.now().isoformat(),
                    'sell_order_id': order_id,
                    'sell_order_status': OrderStatus.REPORTED,  # 初始状态：已报
                    'sell_order_status_name': '已报',
                    'status': 'closed',
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct,
                    'trade_details': json.dumps(trade_details, ensure_ascii=False)
                })
            else:
                # 没有对应的买入记录，创建独立的卖出记录
                gs_strategy_db.add_trade_history(
                    monitor_id=monitor_id,
                    stock_code=stock_code,
                    stock_name=stock_name,
                    sell_price=current_price,
                    sell_quantity=sell_quantity,
                    sell_time=datetime.now().isoformat(),
                    sell_order_id=order_id,
                    sell_order_status=OrderStatus.REPORTED,  # 初始状态：已报
                    sell_order_status_name='已报',
                    status='closed',
                    trade_details=json.dumps(signal_data, ensure_ascii=False)
                )
            
            self.logger.info(f"卖出订单已提交: {stock_code}, 价格: {current_price}, 数量: {sell_quantity}")
            
            # 发送通知
            try:
                self._send_trade_notification(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    action='卖出',
                    price=current_price,
                    quantity=sell_quantity,
                    order_id=order_id,
                    signal_data=signal_data,
                    profit_loss=profit_loss,
                    profit_loss_pct=profit_loss_pct
                )
            except Exception as e:
                self.logger.error(f"发送卖出通知失败: {e}")
        else:
            error_msg = order_result.get('error', '未知错误')
            self.logger.error(f"卖出订单失败: {stock_code}, 错误: {error_msg}")
            
            # 发送失败通知
            try:
                self._send_trade_notification(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    action='卖出失败',
                    price=current_price,
                    quantity=sell_quantity,
                    order_id='',
                    signal_data=signal_data,
                    error=error_msg
                )
            except Exception as e:
                self.logger.error(f"发送卖出失败通知失败: {e}")
    
    def _send_trade_notification(self, stock_code: str, stock_name: str, action: str,
                                  price: float, quantity: int, order_id: str,
                                  signal_data: Dict, error: str = None,
                                  profit_loss: float = None, profit_loss_pct: float = None):
        """
        发送交易通知
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            action: 交易动作
            price: 价格
            quantity: 数量
            order_id: 订单ID
            signal_data: 信号数据
            error: 错误信息（可选）
            profit_loss: 盈亏金额（可选）
            profit_loss_pct: 盈亏百分比（可选）
        """
        try:
            notification_service = get_notification_service()
            
            # 构建通知消息
            message = f"GS策略{action}信号"
            if error:
                message = f"GS策略{action}: {error}"
            
            details = f"""
股票代码: {stock_code}
股票名称: {stock_name}
交易动作: {action}
成交价格: {price:.2f}
成交数量: {quantity}
订单编号: {order_id or '无'}
"""
            
            if profit_loss is not None:
                details += f"盈亏金额: {profit_loss:.2f}\n"
            if profit_loss_pct is not None:
                details += f"盈亏比例: {profit_loss_pct:.2f}%\n"
            
            details += f"""
信号数据:
  收盘价: {signal_data.get('close', 0):.2f}
  BB基线: {signal_data.get('BB', 0):.2f}
  中枢A: {signal_data.get('A', 0):.2f}
  日期: {signal_data.get('date', '')}
"""
            
            notification = {
                'symbol': stock_code,
                'name': stock_name,
                'type': f'GS策略{action}',
                'message': message,
                'details': details,
                'triggered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            notification_service.send_notification(notification)
            
        except Exception as e:
            self.logger.error(f"发送交易通知失败: {e}")

    # ==================== 系统恢复方法 ====================
    
    def restore_running_monitors(self):
        """
        恢复所有运行中的监控任务
        
        在系统重启后调用此方法，恢复之前处于running状态的监控任务
        """
        from app.db.gs_strategy_db import gs_strategy_db
        
        try:
            # 查询所有状态为running的监控任务
            running_monitors = gs_strategy_db.get_running_monitors()
            
            if not running_monitors:
                self.logger.info("没有需要恢复的监控任务")
                return
            
            self.logger.info(f"发现 {len(running_monitors)} 个需要恢复的监控任务")
            
            restored_count = 0
            for monitor in running_monitors:
                try:
                    success = self.start_monitor(
                        monitor_id=monitor['id'],
                        interval=monitor['interval'],
                        stock_code=monitor['stock_code'],
                        stock_name=monitor['stock_name']
                    )
                    
                    if success:
                        restored_count += 1
                        self.logger.info(f"已恢复监控任务: {monitor['id']} ({monitor['stock_code']})")
                    else:
                        self.logger.warning(f"恢复监控任务失败: {monitor['id']} ({monitor['stock_code']})")
                        
                except Exception as e:
                    self.logger.error(f"恢复监控任务异常 {monitor['id']}: {e}")
            
            self.logger.info(f"监控任务恢复完成: 成功 {restored_count}/{len(running_monitors)}")
            
        except Exception as e:
            self.logger.error(f"恢复监控任务失败: {e}")
    
    def stop_all_monitors(self):
        """
        停止所有监控任务
        
        在系统关闭时调用此方法
        """
        with self._lock:
            monitor_ids = list(self._monitoring_threads.keys())
        
        self.logger.info(f"正在停止 {len(monitor_ids)} 个监控任务...")
        
        for monitor_id in monitor_ids:
            try:
                self.stop_monitor(monitor_id)
            except Exception as e:
                self.logger.error(f"停止监控任务 {monitor_id} 失败: {e}")
        
        self.logger.info("所有监控任务已停止")


# 全局调度器实例（单例）
gs_scheduler = GSScheduler()
