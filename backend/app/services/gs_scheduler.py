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

from app.database import SessionLocal
from app.models.gs_strategy import GSMonitorTask, GSTradeHistory
from app.policy.gs import compute_g_buy_sell, load_xtquant_kline
from app.services.qmt_service import qmt_service
from app.services.notification_service import get_notification_service


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
        self.logger.info("GS策略调度器初始化完成")

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
        db = SessionLocal()
        try:
            # 获取监控任务
            monitor = db.query(GSMonitorTask).filter(GSMonitorTask.id == monitor_id).first()
            if not monitor:
                self.logger.error(f"监控任务 {monitor_id} 不存在")
                return
            
            # 获取K线数据并计算GS信号
            signal_data = self._compute_gs_signal(stock_code)
            
            if signal_data is None:
                self.logger.warning(f"无法获取 {stock_code} 的K线数据")
                return
            
            # 更新执行次数
            monitor.execution_count = (monitor.execution_count or 0) + 1
            
            # 处理信号
            g_buy = signal_data.get('g_buy', 0)
            g_sell = signal_data.get('g_sell', 0)
            
            if g_buy == 1:
                # 买入信号
                monitor.last_signal = 'buy'
                monitor.last_signal_time = datetime.now()
                
                # 处理买入
                # - 如果QMT买入成功，会在_handle_buy_signal中提交交易记录和信号更新
                # - 如果QMT买入失败，会抛出异常，触发回滚信号更新
                self._handle_buy_signal(monitor_id, stock_code, stock_name, signal_data, db)
                
            elif g_sell == 1:
                # 卖出信号
                monitor.last_signal = 'sell'
                monitor.last_signal_time = datetime.now()
                
                # 处理卖出
                # - 如果QMT卖出成功，会在_handle_sell_signal中提交交易记录和信号更新
                # - 如果QMT卖出失败，会抛出异常，触发回滚信号更新
                self._handle_sell_signal(monitor_id, stock_code, stock_name, signal_data, db)
                
            else:
                # 持有信号
                monitor.last_signal = 'hold'
                monitor.last_signal_time = datetime.now()
                db.commit()
                
                self.logger.debug(f"{stock_code} 无交易信号")
            
        except Exception as e:
            self.logger.error(f"执行策略失败 {stock_code}: {e}")
            db.rollback()
        finally:
            db.close()
    
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
                           signal_data: Dict, db):
        """
        处理买入信号
        
        Args:
            monitor_id: 监控任务ID
            stock_code: 股票代码
            stock_name: 股票名称
            signal_data: 信号数据
            db: 数据库会话
            
        Raises:
            Exception: 买入失败时抛出异常，触发事务回滚
        """
        self.logger.info(f"检测到买入信号: {stock_code} ({stock_name})")
        
        # 获取当前价格
        current_price = signal_data.get('close', 0)
        
        # 默认买入数量（可以根据配置调整）
        buy_quantity = 100  # 1手
        
        # 调用QMT买入接口
        order_result = qmt_service.buy_stock(
            stock_code=stock_code,
            quantity=buy_quantity,
            price=current_price,
            order_type='market'
        )
        
        if order_result.get('success'):
            order_id = str(order_result.get('order_id', ''))
            
            # 记录交易 - QMT交易成功后必须立即提交，确保交易记录不丢失
            trade = GSTradeHistory(
                monitor_id=monitor_id,
                stock_code=stock_code,
                stock_name=stock_name,
                buy_price=current_price,
                buy_quantity=buy_quantity,
                buy_time=datetime.now(),
                buy_order_id=order_id,
                status='open',
                trade_details=json.dumps(signal_data, ensure_ascii=False)
            )
            db.add(trade)
            # 立即提交，确保交易记录保存
            db.commit()
            
            self.logger.info(f"买入订单已提交: {stock_code}, 价格: {current_price}, 数量: {buy_quantity}")
            
            # 发送通知（通知失败不影响交易记录）
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
            
            # 发送失败通知（通知失败不影响异常抛出）
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
            
            # 抛出异常触发事务回滚（回滚信号更新）
            raise Exception(f"买入订单失败: {error_msg}")
    
    def _handle_sell_signal(self, monitor_id: int, stock_code: str, stock_name: str, 
                            signal_data: Dict, db):
        """
        处理卖出信号
        
        Args:
            monitor_id: 监控任务ID
            stock_code: 股票代码
            stock_name: 股票名称
            signal_data: 信号数据
            db: 数据库会话
            
        Raises:
            Exception: 卖出失败时抛出异常，触发事务回滚
        """
        self.logger.info(f"检测到卖出信号: {stock_code} ({stock_name})")
        
        # 获取当前价格
        current_price = signal_data.get('close', 0)
        
        # 查询持仓
        position = qmt_service.get_position(stock_code)
        
        if not position or position.get('can_sell', 0) <= 0:
            self.logger.warning(f"无可卖持仓: {stock_code}")
            raise Exception(f"无可卖持仓: {stock_code}")
        
        sell_quantity = position.get('can_sell', 0)
        
        # 调用QMT卖出接口
        order_result = qmt_service.sell_stock(
            stock_code=stock_code,
            quantity=sell_quantity,
            price=current_price,
            order_type='market'
        )
        
        if order_result.get('success'):
            order_id = str(order_result.get('order_id', ''))
            
            # 查找对应的未平仓交易记录
            open_trade = db.query(GSTradeHistory).filter(
                GSTradeHistory.monitor_id == monitor_id,
                GSTradeHistory.status == 'open'
            ).first()
            
            profit_loss = None
            profit_loss_pct = None
            
            if open_trade:
                # 更新交易记录
                open_trade.sell_price = current_price
                open_trade.sell_quantity = sell_quantity
                open_trade.sell_time = datetime.now()
                open_trade.sell_order_id = order_id
                open_trade.status = 'closed'
                
                # 计算盈亏
                if open_trade.buy_price and open_trade.buy_quantity:
                    open_trade.profit_loss = (current_price - open_trade.buy_price) * open_trade.buy_quantity
                    open_trade.profit_loss_pct = ((current_price - open_trade.buy_price) / open_trade.buy_price) * 100
                    profit_loss = open_trade.profit_loss
                    profit_loss_pct = open_trade.profit_loss_pct
                
                # 更新交易详情
                trade_details = json.loads(open_trade.trade_details) if open_trade.trade_details else {}
                trade_details['sell_signal'] = signal_data
                open_trade.trade_details = json.dumps(trade_details, ensure_ascii=False)
            else:
                # 没有对应的买入记录，创建独立的卖出记录
                trade = GSTradeHistory(
                    monitor_id=monitor_id,
                    stock_code=stock_code,
                    stock_name=stock_name,
                    sell_price=current_price,
                    sell_quantity=sell_quantity,
                    sell_time=datetime.now(),
                    sell_order_id=order_id,
                    status='closed',
                    trade_details=json.dumps(signal_data, ensure_ascii=False)
                )
                db.add(trade)
            
            # QMT交易成功后必须立即提交，确保交易记录不丢失
            db.commit()
            
            self.logger.info(f"卖出订单已提交: {stock_code}, 价格: {current_price}, 数量: {sell_quantity}")
            
            # 发送通知（通知失败不影响交易记录）
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
            
            # 发送失败通知（通知失败不影响异常抛出）
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
            
            # 抛出异常触发事务回滚（回滚信号更新）
            raise Exception(f"卖出订单失败: {error_msg}")
    
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
        db = SessionLocal()
        try:
            # 查询所有状态为running的监控任务
            running_monitors = db.query(GSMonitorTask).filter(
                GSMonitorTask.status == 'running'
            ).all()
            
            if not running_monitors:
                self.logger.info("没有需要恢复的监控任务")
                return
            
            self.logger.info(f"发现 {len(running_monitors)} 个需要恢复的监控任务")
            
            restored_count = 0
            for monitor in running_monitors:
                try:
                    success = self.start_monitor(
                        monitor_id=monitor.id,
                        interval=monitor.interval,
                        stock_code=monitor.stock_code,
                        stock_name=monitor.stock_name
                    )
                    
                    if success:
                        restored_count += 1
                        self.logger.info(f"已恢复监控任务: {monitor.id} ({monitor.stock_code})")
                    else:
                        self.logger.warning(f"恢复监控任务失败: {monitor.id} ({monitor.stock_code})")
                        
                except Exception as e:
                    self.logger.error(f"恢复监控任务异常 {monitor.id}: {e}")
            
            self.logger.info(f"监控任务恢复完成: 成功 {restored_count}/{len(running_monitors)}")
            
        except Exception as e:
            self.logger.error(f"恢复监控任务失败: {e}")
        finally:
            db.close()
    
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
