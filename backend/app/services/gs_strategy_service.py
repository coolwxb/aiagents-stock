"""
GS策略服务
提供股票池管理、监控任务管理、持仓查询和交易历史统计功能
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.db.gs_strategy_db import gs_strategy_db
from app.services.qmt_service import qmt_service


class GSStrategyService:
    """GS策略服务类"""
    
    def __init__(self, db=None):
        """
        初始化GS策略服务
        
        Args:
            db: 数据库会话（保留参数以兼容现有代码，但不使用）
        """
        self.db_instance = gs_strategy_db
        self.logger = logging.getLogger(__name__)
    
    # ==================== 股票池管理方法 ====================
    
    def get_stock_pool(self) -> List[Dict]:
        """
        获取股票池列表
        
        Returns:
            股票池列表，包含stock_code, stock_name, created_at等字段
        """
        try:
            return self.db_instance.get_stock_pool()
        except Exception as e:
            self.logger.error(f"获取股票池列表失败: {e}")
            raise

    def add_to_stock_pool(self, stock_code: str) -> Dict:
        """
        添加股票到股票池（自动获取股票名称）
        
        Args:
            stock_code: 股票代码
            
        Returns:
            添加的股票信息
            
        Raises:
            ValueError: 股票代码已存在或无法获取股票信息
        """
        try:
            # 自动获取股票名称
            stock_info = self.get_stock_info(stock_code)
            stock_name = stock_info.get('stock_name', '')
            
            if not stock_name:
                raise ValueError(f"无法获取股票代码 {stock_code} 的名称")
            
            stock_id = self.db_instance.add_stock(stock_code, stock_name)
            
            return {
                'id': stock_id,
                'stock_code': stock_code,
                'stock_name': stock_name,
                'created_at': datetime.now().isoformat()
            }
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"添加股票到股票池失败: {e}")
            raise
    
    def remove_from_stock_pool(self, stock_id: int) -> bool:
        """
        从股票池中删除股票（级联删除关联的监控任务）
        
        Args:
            stock_id: 股票池记录ID
            
        Returns:
            是否删除成功
            
        Raises:
            ValueError: 股票不存在
        """
        try:
            return self.db_instance.remove_stock(stock_id)
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"从股票池删除股票失败: {e}")
            raise
    
    def search_stock_pool(self, keyword: str) -> List[Dict]:
        """
        搜索股票池
        
        Args:
            keyword: 搜索关键词（匹配股票代码或名称）
            
        Returns:
            匹配的股票列表
        """
        try:
            return self.db_instance.search_stock_pool(keyword)
        except Exception as e:
            self.logger.error(f"搜索股票池失败: {e}")
            raise
    
    def get_stock_info(self, stock_code: str) -> Dict:
        """
        获取股票信息（通过QMT接口）
        
        Args:
            stock_code: 股票代码（6位数字）
            
        Returns:
            股票信息，包含股票名称
            
        Raises:
            ValueError: 股票代码无效或未找到股票信息
        """
        try:
            # 调用QMT服务获取股票信息
            stock_info = qmt_service.get_stock_info(stock_code)
            if not stock_info:
                raise ValueError(f"未找到股票代码 {stock_code} 的信息")
            
            # QMT返回的字段名为InstrumentName（合约名称）
            stock_name = stock_info.get('InstrumentName', '')
            
            if not stock_name:
                raise ValueError(f"未找到股票代码 {stock_code} 的名称信息")
            
            return {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'instrument_id': stock_info.get('InstrumentID', ''),
                'exchange_id': stock_info.get('ExchangeID', ''),
                'pre_close': stock_info.get('PreClose'),
                'is_trading': stock_info.get('IsTrading', False)
            }
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"获取股票信息失败: {e}")
            raise ValueError(f"获取股票信息失败: {str(e)}")

    # ==================== 监控任务管理方法 ====================
    
    def get_monitors(self) -> List[Dict]:
        """
        获取所有监控任务列表（包含运行时长计算）
        
        Returns:
            监控任务列表
        """
        try:
            monitors = self.db_instance.get_monitors()
            
            result = []
            now = datetime.now()
            
            for monitor in monitors:
                # 计算运行时长（仅当状态为running且有started_at时）
                running_duration = None
                if monitor['status'] == 'running' and monitor.get('started_at'):
                    try:
                        started_at = datetime.fromisoformat(monitor['started_at'])
                        delta = now - started_at
                        running_duration = int(delta.total_seconds())
                    except:
                        pass
                
                monitor['running_duration'] = running_duration
                result.append(monitor)
            
            return result
        except Exception as e:
            self.logger.error(f"获取监控任务列表失败: {e}")
            raise
    
    def create_monitor(self, stock_id: int, interval: int = 300) -> Dict:
        """
        创建监控任务
        
        Args:
            stock_id: 股票池记录ID
            interval: 监测间隔（秒），默认300秒
            
        Returns:
            创建的监控任务信息
            
        Raises:
            ValueError: 股票不存在或已有监控任务
        """
        try:
            # 获取股票池记录
            stock = self.db_instance.get_stock_by_id(stock_id)
            
            if not stock:
                raise ValueError(f"股票池中未找到ID为 {stock_id} 的股票")
            
            # 检查是否已存在该股票的监控任务
            monitors = self.db_instance.get_monitors()
            for m in monitors:
                if m['stock_code'] == stock['stock_code']:
                    raise ValueError(f"股票 {stock['stock_code']} 已在监控队列中")
            
            # 创建监控任务
            monitor_id = self.db_instance.create_monitor(
                stock_pool_id=stock_id,
                stock_code=stock['stock_code'],
                stock_name=stock['stock_name'],
                interval=interval
            )
            
            # 启动调度器线程
            from app.services.gs_scheduler import gs_scheduler
            gs_scheduler.start_monitor(
                monitor_id=monitor_id,
                interval=interval,
                stock_code=stock['stock_code'],
                stock_name=stock['stock_name']
            )
            
            return {
                'id': monitor_id,
                'stock_pool_id': stock_id,
                'stock_code': stock['stock_code'],
                'stock_name': stock['stock_name'],
                'interval': interval,
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'execution_count': 0,
                'created_at': datetime.now().isoformat()
            }
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"创建监控任务失败: {e}")
            raise
    
    def update_monitor(self, monitor_id: int, data: Dict) -> Dict:
        """
        更新监控任务配置
        
        Args:
            monitor_id: 监控任务ID
            data: 更新的数据（可包含interval等字段）
            
        Returns:
            更新后的监控任务信息
            
        Raises:
            ValueError: 监控任务不存在
        """
        try:
            # 更新监控任务
            success = self.db_instance.update_monitor(monitor_id, **data)
            
            if not success:
                raise ValueError(f"监控任务 {monitor_id} 不存在")
            
            # 获取更新后的监控任务
            monitor = self.db_instance.get_monitor_by_id(monitor_id)
            
            # 计算运行时长
            running_duration = None
            if monitor['status'] == 'running' and monitor.get('started_at'):
                try:
                    started_at = datetime.fromisoformat(monitor['started_at'])
                    delta = datetime.now() - started_at
                    running_duration = int(delta.total_seconds())
                except:
                    pass
            
            monitor['running_duration'] = running_duration
            return monitor
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"更新监控任务失败: {e}")
            raise
    
    def delete_monitor(self, monitor_id: int) -> bool:
        """
        删除监控任务
        
        Args:
            monitor_id: 监控任务ID
            
        Returns:
            是否删除成功
            
        Raises:
            ValueError: 监控任务不存在
        """
        try:
            # 先停止调度器线程
            from app.services.gs_scheduler import gs_scheduler
            gs_scheduler.stop_monitor(monitor_id)
            
            # 删除监控任务
            return self.db_instance.delete_monitor(monitor_id)
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"删除监控任务失败: {e}")
            raise
    
    def start_monitor(self, monitor_id: int) -> Dict:
        """
        启动监控任务
        
        Args:
            monitor_id: 监控任务ID
            
        Returns:
            更新后的监控任务信息
            
        Raises:
            ValueError: 监控任务不存在
        """
        try:
            monitor = self.db_instance.get_monitor_by_id(monitor_id)
            
            if not monitor:
                raise ValueError(f"监控任务 {monitor_id} 不存在")
            
            # 更新状态和启动时间
            self.db_instance.update_monitor(
                monitor_id,
                status='running',
                started_at=datetime.now().isoformat()
            )
            
            # 启动调度器线程
            from app.services.gs_scheduler import gs_scheduler
            gs_scheduler.start_monitor(
                monitor_id=monitor_id,
                interval=monitor['interval'],
                stock_code=monitor['stock_code'],
                stock_name=monitor['stock_name']
            )
            
            return {
                'id': monitor_id,
                'stock_code': monitor['stock_code'],
                'stock_name': monitor['stock_name'],
                'interval': monitor['interval'],
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'execution_count': monitor.get('execution_count', 0)
            }
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"启动监控任务失败: {e}")
            raise
    
    def stop_monitor(self, monitor_id: int) -> Dict:
        """
        停止监控任务（保留配置）
        
        Args:
            monitor_id: 监控任务ID
            
        Returns:
            更新后的监控任务信息
            
        Raises:
            ValueError: 监控任务不存在
        """
        try:
            monitor = self.db_instance.get_monitor_by_id(monitor_id)
            
            if not monitor:
                raise ValueError(f"监控任务 {monitor_id} 不存在")
            
            # 停止调度器线程
            from app.services.gs_scheduler import gs_scheduler
            gs_scheduler.stop_monitor(monitor_id)
            
            # 只更新状态，保留其他配置
            self.db_instance.update_monitor(monitor_id, status='stopped')
            
            return {
                'id': monitor_id,
                'stock_code': monitor['stock_code'],
                'stock_name': monitor['stock_name'],
                'interval': monitor['interval'],
                'status': 'stopped',
                'started_at': monitor.get('started_at'),
                'execution_count': monitor.get('execution_count', 0)
            }
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"停止监控任务失败: {e}")
            raise

    # ==================== 持仓和历史统计方法 ====================
    
    def get_positions(self) -> Dict:
        """
        获取QMT持仓信息
        
        Returns:
            持仓信息，包含账户概览和持仓列表
        """
        try:
            # 获取QMT账户信息
            account_info = qmt_service.get_account_info()
            
            # 获取QMT持仓列表
            positions = qmt_service.get_all_positions()
            
            return {
                'account_info': {
                    'account_id': account_info.get('account_id', ''),
                    'available_cash': account_info.get('available_cash', 0),
                    'total_value': account_info.get('total_value', 0),
                    'market_value': account_info.get('market_value', 0),
                    'frozen_cash': account_info.get('frozen_cash', 0),
                    'positions_count': account_info.get('positions_count', 0),
                    'total_profit_loss': account_info.get('total_profit_loss', 0),
                    'connected': account_info.get('connected', False)
                },
                'positions': positions,
                'total_count': len(positions),
                'message': 'success' if account_info.get('connected') else account_info.get('message', 'QMT未连接')
            }
        except Exception as e:
            self.logger.error(f"获取持仓信息失败: {e}")
            return {
                'account_info': {
                    'available_cash': 0,
                    'total_value': 0,
                    'market_value': 0,
                    'frozen_cash': 0,
                    'positions_count': 0,
                    'total_profit_loss': 0,
                    'connected': False
                },
                'positions': [],
                'total_count': 0,
                'message': f'获取失败: {str(e)}'
            }
    
    def get_trade_history(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """
        获取交易历史记录
        
        Args:
            start_date: 开始日期（格式：YYYY-MM-DD）
            end_date: 结束日期（格式：YYYY-MM-DD）
            
        Returns:
            交易历史列表
        """
        try:
            trades = self.db_instance.get_trade_history(start_date, end_date)
            
            result = []
            for trade in trades:
                # 解析trade_details JSON
                trade_details = None
                if trade.get('trade_details'):
                    try:
                        trade_details = json.loads(trade['trade_details'])
                    except:
                        trade_details = None
                
                trade['trade_details'] = trade_details
                result.append(trade)
            
            return result
        except Exception as e:
            self.logger.error(f"获取交易历史失败: {e}")
            raise
    
    def get_statistics(self) -> Dict:
        """
        获取交易统计数据
        
        Returns:
            统计数据，包含总交易数、胜率、总盈亏等
        """
        try:
            return self.db_instance.get_statistics()
        except Exception as e:
            self.logger.error(f"获取交易统计失败: {e}")
            raise
    
    def record_trade(self, monitor_id: int, action: str, price: float, 
                     quantity: int, order_id: str) -> Dict:
        """
        记录交易
        
        Args:
            monitor_id: 监控任务ID
            action: 交易动作（buy/sell）
            price: 成交价格
            quantity: 成交数量
            order_id: 订单ID
            
        Returns:
            交易记录信息
        """
        try:
            # 获取监控任务信息
            monitor = self.db_instance.get_monitor_by_id(monitor_id)
            
            if not monitor:
                raise ValueError(f"监控任务 {monitor_id} 不存在")
            
            now = datetime.now()
            
            if action.lower() == 'buy':
                # 创建新的交易记录（买入）
                trade_id = self.db_instance.create_trade(
                    monitor_id=monitor_id,
                    stock_code=monitor['stock_code'],
                    stock_name=monitor['stock_name'],
                    buy_price=price,
                    buy_quantity=quantity,
                    buy_order_id=order_id
                )
                
                return {
                    'id': trade_id,
                    'stock_code': monitor['stock_code'],
                    'stock_name': monitor['stock_name'],
                    'action': 'buy',
                    'price': price,
                    'quantity': quantity,
                    'order_id': order_id,
                    'time': now.isoformat(),
                    'status': 'open'
                }
            else:
                # 卖出：查找对应的未平仓交易记录
                open_trade = self.db_instance.get_open_trade_by_monitor(monitor_id)
                
                if open_trade:
                    # 完成交易
                    return self.complete_trade(open_trade['id'], price, quantity, order_id)
                else:
                    # 没有对应的买入记录，记录为独立卖出
                    self.logger.warning(f"监控任务 {monitor_id} 没有对应的买入记录")
                    return {
                        'stock_code': monitor['stock_code'],
                        'stock_name': monitor['stock_name'],
                        'action': 'sell',
                        'price': price,
                        'quantity': quantity,
                        'order_id': order_id,
                        'time': now.isoformat(),
                        'status': 'closed',
                        'message': '没有对应的买入记录'
                    }
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"记录交易失败: {e}")
            raise
    
    def complete_trade(self, trade_id: int, sell_price: float, 
                       sell_quantity: int, sell_order_id: str) -> Dict:
        """
        完成交易（计算盈亏）
        
        Args:
            trade_id: 交易记录ID
            sell_price: 卖出价格
            sell_quantity: 卖出数量
            sell_order_id: 卖出订单ID
            
        Returns:
            完成的交易记录信息
        """
        try:
            # 完成交易
            success = self.db_instance.complete_trade(trade_id, sell_price, sell_quantity, sell_order_id)
            
            if not success:
                raise ValueError(f"交易记录 {trade_id} 不存在")
            
            # 获取更新后的交易记录
            trades = self.db_instance.get_trade_history()
            trade = next((t for t in trades if t['id'] == trade_id), None)
            
            if trade:
                return {
                    'id': trade['id'],
                    'stock_code': trade['stock_code'],
                    'stock_name': trade['stock_name'],
                    'buy_price': trade.get('buy_price'),
                    'buy_quantity': trade.get('buy_quantity'),
                    'buy_time': trade.get('buy_time'),
                    'sell_price': trade.get('sell_price'),
                    'sell_quantity': trade.get('sell_quantity'),
                    'sell_time': trade.get('sell_time'),
                    'profit_loss': round(trade['profit_loss'], 2) if trade.get('profit_loss') else None,
                    'profit_loss_pct': round(trade['profit_loss_pct'], 2) if trade.get('profit_loss_pct') else None,
                    'status': trade['status']
                }
            else:
                raise ValueError(f"交易记录 {trade_id} 不存在")
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"完成交易失败: {e}")
            raise
    
    # ==================== 辅助方法 ====================
    
    def update_monitor_signal(self, monitor_id: int, signal: str) -> None:
        """
        更新监控任务的最后信号
        
        Args:
            monitor_id: 监控任务ID
            signal: 信号类型（buy/sell/hold）
        """
        try:
            monitor = self.db_instance.get_monitor_by_id(monitor_id)
            
            if monitor:
                execution_count = (monitor.get('execution_count') or 0) + 1
                self.db_instance.update_monitor(
                    monitor_id,
                    last_signal=signal,
                    last_signal_time=datetime.now().isoformat(),
                    execution_count=execution_count
                )
        except Exception as e:
            self.logger.error(f"更新监控信号失败: {e}")
    
    def get_running_monitors(self) -> List[Dict]:
        """
        获取所有运行中的监控任务（用于系统重启恢复）
        
        Returns:
            运行中的监控任务列表
        """
        try:
            return self.db_instance.get_running_monitors()
        except Exception as e:
            self.logger.error(f"获取运行中的监控任务失败: {e}")
            return []
