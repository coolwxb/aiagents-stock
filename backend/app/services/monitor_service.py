"""
智能盯盘服务
提供监控任务管理、AI决策、交易执行等功能
使用 backend 内部模块，不依赖 old 目录
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, List, Optional
from datetime import datetime, time
import logging
import threading
import json
import os

from app.models.monitor import MonitorTask
from app.agents.deepseek_client import DeepSeekClient
from app.services.qmt_service import qmt_service
from app.services.notification_service import get_notification_service
from app.data.data_source import data_source_manager
from app.data.stock_data import StockDataFetcher


class MonitorService:
    """智能盯盘服务类"""
    
    # 类级别的监控线程管理
    _monitoring_threads = {}
    _stop_flags = {}
    _deepseek_client = None
    _data_fetcher = None
    _qmt_connected = False
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # 延迟初始化引擎（避免循环导入）
        if MonitorService._deepseek_client is None:
            self._init_engine()
    
    def _init_engine(self):
        """初始化监控引擎和数据获取模块"""
        try:
            # 初始化AI决策模块（使用 backend 的 DeepSeekClient）
            MonitorService._deepseek_client = DeepSeekClient()
            
            # 初始化数据获取模块（使用 backend 的 StockDataFetcher）
            MonitorService._data_fetcher = data_source_manager
            
            # 从数据库加载QMT配置
            qmt_service.load_config(self.db)
            
            # 从数据库加载通知配置
            notification_service = get_notification_service(db=self.db)
            
            # 尝试连接QMT（如果启用）
            if qmt_service.enabled and not MonitorService._qmt_connected:
                success, msg = qmt_service.connect()
                if success:
                    MonitorService._qmt_connected = True
                    self.logger.info(f"QMT连接成功: {msg}")
                else:
                    self.logger.warning(f"MonitorService  QMT连接失败: {msg}，将使用模拟模式")
            
            self.logger.info("智能盯盘引擎初始化完成（使用backend内部模块）")
        except Exception as e:
            self.logger.error(f"初始化智能盯盘引擎失败: {e}")
            raise
    
    async def get_tasks(self, enabled_only: bool = False) -> List[Dict]:
        """
        获取监控任务列表
        
        Args:
            enabled_only: 是否只返回启用的任务
            
        Returns:
            任务列表
        """
        try:
            query = self.db.query(MonitorTask)
            
            if enabled_only:
                query = query.filter(MonitorTask.status == 'running')
            
            tasks = query.order_by(desc(MonitorTask.created_at)).all()
            
            result = []
            for task in tasks:
                # 解析quant_config JSON
                quant_config = None
                if task.quant_config:
                    try:
                        quant_config = json.loads(task.quant_config)
                    except:
                        quant_config = None
                
                task_dict = {
                    'id': task.id,
                    'task_name': task.task_name,
                    'stock_code': task.stock_code,
                    'stock_name': task.stock_name,
                    'status': task.status,
                    'strategy': task.strategy or 'GS',
                    'check_interval': task.check_interval,
                    'auto_trade': task.auto_trade,
                    'trading_hours_only': task.trading_hours_only,
                    'entry_min': task.entry_min,
                    'entry_max': task.entry_max,
                    'take_profit': task.take_profit,
                    'stop_loss': task.stop_loss,
                    'notification_enabled': task.notification_enabled,
                    'quant_config': quant_config,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                    'is_running': task.stock_code in MonitorService._monitoring_threads
                }
                result.append(task_dict)
            
            return result
        except Exception as e:
            self.logger.error(f"获取监控任务列表失败: {e}")
            raise
    
    async def create_task(self, task_data: Dict) -> Dict:
        """
        创建监控任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            创建的任务信息
        """
        try:
            # 字段映射：支持symbol和stock_code两种字段名
            stock_code = task_data.get('stock_code') or task_data.get('symbol')
            if not stock_code:
                raise ValueError("股票代码不能为空")
            
            # 检查是否已存在相同股票代码的任务
            existing = self.db.query(MonitorTask).filter(
                MonitorTask.stock_code == stock_code
            ).first()
            
            if existing:
                raise ValueError(f"股票代码 {stock_code} 已存在监控任务")
            
            # 映射status字段：running -> running, paused/stopped -> stopped
            status = 'running' if task_data.get('status') == 'running' else 'stopped'
            
            # 处理quant_config，将字典转为JSON字符串
            quant_config_str = None
            if task_data.get('quant_config'):
                try:
                    quant_config_str = json.dumps(task_data['quant_config'])
                except:
                    quant_config_str = None
            
            # 创建新任务
            new_task = MonitorTask(
                task_name=task_data.get('task_name') or task_data.get('name') or stock_code,
                stock_code=stock_code,
                stock_name=task_data.get('stock_name') or task_data.get('name', ''),
                strategy=task_data.get('strategy') or 'GS',
                status=status,
                check_interval=task_data.get('check_interval', 300),
                auto_trade=task_data.get('auto_trade') or task_data.get('quant_enabled', False),
                trading_hours_only=task_data.get('trading_hours_only', True),
                entry_min=task_data.get('entry_min'),
                entry_max=task_data.get('entry_max'),
                take_profit=task_data.get('take_profit'),
                stop_loss=task_data.get('stop_loss'),
                notification_enabled=task_data.get('notification_enabled', False),
                quant_config=quant_config_str
            )
            
            self.db.add(new_task)
            self.db.commit()
            self.db.refresh(new_task)
            
            # 解析quant_config返回
            quant_config = None
            if new_task.quant_config:
                try:
                    quant_config = json.loads(new_task.quant_config)
                except:
                    quant_config = None
            
            return {
                'id': new_task.id,
                'task_name': new_task.task_name,
                'stock_code': new_task.stock_code,
                'stock_name': new_task.stock_name,
                'status': new_task.status,
                'strategy': new_task.strategy,
                'check_interval': new_task.check_interval,
                'auto_trade': new_task.auto_trade,
                'trading_hours_only': new_task.trading_hours_only,
                'entry_min': new_task.entry_min,
                'entry_max': new_task.entry_max,
                'take_profit': new_task.take_profit,
                'stop_loss': new_task.stop_loss,
                'notification_enabled': new_task.notification_enabled,
                'quant_config': quant_config,
                'created_at': new_task.created_at.isoformat() if new_task.created_at else None
            }
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"创建监控任务失败: {e}")
            raise
    
    async def update_task(self, task_id: int, task_data: Dict) -> Dict:
        """
        更新任务配置
        
        Args:
            task_id: 任务ID
            task_data: 更新的数据
            
        Returns:
            更新后的任务信息
        """
        try:
            task = self.db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")
            
            # 更新字段
            if 'task_name' in task_data:
                task.task_name = task_data['task_name']
            if 'check_interval' in task_data:
                task.check_interval = task_data['check_interval']
            if 'strategy' in task_data:
                task.strategy = task_data['strategy']
            if 'auto_trade' in task_data:
                task.auto_trade = task_data['auto_trade']
            if 'trading_hours_only' in task_data:
                task.trading_hours_only = task_data['trading_hours_only']
            if 'entry_min' in task_data:
                task.entry_min = task_data['entry_min']
            if 'entry_max' in task_data:
                task.entry_max = task_data['entry_max']
            if 'take_profit' in task_data:
                task.take_profit = task_data['take_profit']
            if 'stop_loss' in task_data:
                task.stop_loss = task_data['stop_loss']
            if 'notification_enabled' in task_data:
                task.notification_enabled = task_data['notification_enabled']
            if 'quant_config' in task_data:
                try:
                    task.quant_config = json.dumps(task_data['quant_config'])
                except:
                    task.quant_config = None
            
            task.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(task)
            
            # 解析quant_config返回
            quant_config = None
            if task.quant_config:
                try:
                    quant_config = json.loads(task.quant_config)
                except:
                    quant_config = None
            
            return {
                'id': task.id,
                'task_name': task.task_name,
                'stock_code': task.stock_code,
                'stock_name': task.stock_name,
                'status': task.status,
                'strategy': task.strategy,
                'check_interval': task.check_interval,
                'auto_trade': task.auto_trade,
                'trading_hours_only': task.trading_hours_only,
                'entry_min': task.entry_min,
                'entry_max': task.entry_max,
                'take_profit': task.take_profit,
                'stop_loss': task.stop_loss,
                'notification_enabled': task.notification_enabled,
                'quant_config': quant_config,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None
            }
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"更新任务失败: {e}")
            raise
    
    async def delete_task(self, task_id: int) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        try:
            task = self.db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")
            
            # 如果任务正在运行，先停止
            if task.stock_code in MonitorService._monitoring_threads:
                await self._stop_monitor_thread(task.stock_code)
            
            self.db.delete(task)
            self.db.commit()
            
            return True
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"删除任务失败: {e}")
            raise
    
    async def start_task(self, task_id: int) -> Dict:
        """
        启动监控任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        try:
            task = self.db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")
            
            # 检查是否已在运行
            if task.stock_code in MonitorService._monitoring_threads:
                return {
                    'status': 'already_running',
                    'message': f"任务 {task.stock_code} 已在运行中"
                }
            
            # 启动监控线程
            await self._start_monitor_thread(
                stock_code=task.stock_code,
                check_interval=task.check_interval,
                auto_trade=task.auto_trade,
                trading_hours_only=task.trading_hours_only,
                strategy=task.strategy or 'GS'
            )
            
            # 更新任务状态
            task.status = 'running'
            task.updated_at = datetime.now()
            self.db.commit()
            
            return {
                'status': 'started',
                'message': f"任务 {task.stock_code} 已启动",
                'task_id': task.id,
                'stock_code': task.stock_code
            }
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"启动任务失败: {e}")
            raise
    
    async def stop_task(self, task_id: int) -> Dict:
        """
        停止监控任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        try:
            task = self.db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")
            
            # 停止监控线程
            if task.stock_code in MonitorService._monitoring_threads:
                await self._stop_monitor_thread(task.stock_code)
            
            # 更新任务状态
            task.status = 'stopped'
            task.updated_at = datetime.now()
            self.db.commit()
            
            return {
                'status': 'stopped',
                'message': f"任务 {task.stock_code} 已停止",
                'task_id': task.id,
                'stock_code': task.stock_code
            }
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"停止任务失败: {e}")
            raise
    
    async def get_task_status(self, task_id: int) -> Dict:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态详情
        """
        try:
            task = self.db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")
            
            is_running = task.stock_code in MonitorService._monitoring_threads
            
            # 解析quant_config
            quant_config = None
            if task.quant_config:
                try:
                    quant_config = json.loads(task.quant_config)
                except:
                    quant_config = None
            
            return {
                'id': task.id,
                'task_name': task.task_name,
                'stock_code': task.stock_code,
                'stock_name': task.stock_name,
                'status': task.status,
                'is_running': is_running,
                'check_interval': task.check_interval,
                'auto_trade': task.auto_trade,
                'trading_hours_only': task.trading_hours_only,
                'entry_min': task.entry_min,
                'entry_max': task.entry_max,
                'take_profit': task.take_profit,
                'stop_loss': task.stop_loss,
                'notification_enabled': task.notification_enabled,
                'quant_config': quant_config,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None
            }
        except Exception as e:
            self.logger.error(f"获取任务状态失败: {e}")
            raise
    
    async def get_positions(self) -> Dict:
        """
        获取持仓信息
        
        Returns:
            持仓详情（包括账户信息和持仓列表）
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
                'message': account_info.get('message', 'QMT未连接') if not account_info.get('connected') else 'success'
            }
        except Exception as e:
            self.logger.error(f"获取持仓信息失败: {e}")
            # 返回空数据而不是抛出异常
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
    
    async def get_history(self, stock_code: Optional[str] = None, 
                          page: int = 1, page_size: int = 20) -> Dict:
        """
        获取AI决策历史
        
        Args:
            stock_code: 股票代码（可选，不传则返回所有）
            page: 页码
            page_size: 每页数量
            
        Returns:
            决策历史列表
        """
        try:
            # TODO: 需要迁移 AI决策历史表到 PostgreSQL
            # 目前返回空数据
            return {
                'decisions': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'message': 'AI决策历史表尚未迁移，请等待后续版本'
            }
        except Exception as e:
            self.logger.error(f"获取决策历史失败: {e}")
            return {
                'decisions': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'error': str(e)
            }
    
    async def get_stock_quote(self, stock_code: str) -> Dict:
        """
        获取股票实时行情
        
        Args:
            stock_code: 股票代码
            
        Returns:
            实时行情信息，包含价格、名称等
        """
        try:
            import asyncio
            # 使用 StockDataFetcher 获取实时行情
            if MonitorService._data_fetcher is None:
                MonitorService._data_fetcher = StockDataFetcher()
            
            # 获取实时行情
            quote = await asyncio.to_thread(
                MonitorService._data_fetcher.get_realtime_quote,
                stock_code
            )
            
            if quote is None:
                raise ValueError(f"无法获取股票 {stock_code} 的实时行情")
            
            # 获取股票基本信息
            stock_info = await asyncio.to_thread(
                MonitorService._data_fetcher.get_stock_info,
                stock_code
            )
            
            # 合并信息
            result = {
                'stock_code': stock_code,
                'stock_name': quote.get('name') or stock_info.get('name', ''),
                'current_price': quote.get('price', 0),
                'change': quote.get('change', 0),
                'change_percent': quote.get('change_percent', 0),
                'volume': quote.get('volume', 0),
                'high': quote.get('high', 0),
                'low': quote.get('low', 0),
                'open': quote.get('open', 0),
                'pre_close': quote.get('pre_close', 0),
            }
            
            return result
        except Exception as e:
            self.logger.error(f"获取股票行情失败 {stock_code}: {e}")
            raise ValueError(f"获取股票行情失败: {str(e)}")
    
    async def _start_monitor_thread(self, stock_code: str, check_interval: int,
                                    auto_trade: bool, trading_hours_only: bool,
                                    strategy: str = 'GS'):
        """
        启动监控线程
        
        Args:
            stock_code: 股票代码
            check_interval: 检查间隔（秒）
            auto_trade: 是否自动交易
            trading_hours_only: 是否仅交易时段监控
        """
        if stock_code in MonitorService._monitoring_threads:
            self.logger.warning(f"监控线程 {stock_code} 已在运行中")
            return
        
        # 创建停止标志
        stop_flag = threading.Event()
        MonitorService._stop_flags[stock_code] = stop_flag
        
        # 创建监控线程
        thread = threading.Thread(
            target=self._monitor_loop,
            args=(stock_code, check_interval, auto_trade, trading_hours_only, strategy, stop_flag),
            daemon=True
        )
        
        MonitorService._monitoring_threads[stock_code] = thread
        thread.start()
        
        self.logger.info(f"监控线程 {stock_code} 已启动")
    
    async def _stop_monitor_thread(self, stock_code: str):
        """
        停止监控线程
        
        Args:
            stock_code: 股票代码
        """
        if stock_code not in MonitorService._monitoring_threads:
            self.logger.warning(f"监控线程 {stock_code} 未运行")
            return
        
        # 设置停止标志
        MonitorService._stop_flags[stock_code].set()
        
        # 等待线程结束
        MonitorService._monitoring_threads[stock_code].join(timeout=5)
        
        # 清理
        del MonitorService._monitoring_threads[stock_code]
        del MonitorService._stop_flags[stock_code]
        
        self.logger.info(f"监控线程 {stock_code} 已停止")
    
    def _monitor_loop(self, stock_code: str, check_interval: int,
                     auto_trade: bool, trading_hours_only: bool,
                     strategy: str, stop_flag: threading.Event):
        """
        监控循环（在独立线程中运行）
        
        Args:
            stock_code: 股票代码
            check_interval: 检查间隔
            auto_trade: 是否自动交易
            trading_hours_only: 是否仅交易时段
            stop_flag: 停止标志
        """
        self.logger.info(f"[{stock_code}] 监控循环已启动")
        
        while not stop_flag.is_set():
            try:
                # 执行分析（调用 smart_monitor_engine 的逻辑）
                result = self._analyze_stock(
                    stock_code=stock_code,
                    auto_trade=auto_trade,
                    trading_hours_only=trading_hours_only,
                    strategy=strategy
                )
                
                if result.get('success'):
                    self.logger.info(f"[{stock_code}] 分析完成: {result['decision']['action']}")
                else:
                    self.logger.error(f"[{stock_code}] 分析失败: {result.get('error')}")
                
            except Exception as e:
                self.logger.error(f"[{stock_code}] 监控循环异常: {e}")
            
            # 等待下一次检查
            stop_flag.wait(check_interval)
        
        self.logger.info(f"[{stock_code}] 监控循环已退出")
    
    def _analyze_stock(
                    self,
                    stock_code: str, 
                    auto_trade: bool = False,
                    trading_hours_only: bool = True,
                    strategy: str = 'GS') -> Dict:
        """
        分析股票（使用 backend 内部模块）
        
        Args:
            stock_code: 股票代码
            auto_trade: 是否自动交易
            trading_hours_only: 是否仅交易时段
            
        Returns:
            分析结果
        """
        try:
            # 1. 检查交易时段
            now = datetime.now()
            current_time = now.time()
            
            # 交易时段：9:30-11:30, 13:00-15:00
            # morning_start = time(9, 30)
            # morning_end = time(11, 30)
            # afternoon_start = time(13, 0)
            # afternoon_end = time(15, 0)
            
            # is_trading_hours = (
            #     (morning_start <= current_time <= morning_end) or
            #     (afternoon_start <= current_time <= afternoon_end)
            # )
            
            # if trading_hours_only and not is_trading_hours:
            #     return {
            #         'success': False,
            #         'skipped': True,
            #         'error': '非交易时段，跳过分析'
            #     }

            self.logger.info(f"[{stock_code}] 按照策略{strategy}进行分析")
                
            # 获取股票基本信息
            stock_info = data_source_manager.get_stock_basic_info(stock_code)
            if not stock_info or stock_info.get('error'):
                return {
                    'success': False,
                    'error': '获取股票信息失败'
                }

            
            # 根据任务配置的策略选择决策逻辑
            if (strategy or '').upper() == 'AI':
                pass
                # 获取技术指标
                # indicators = get_technical_indicators(stock_code)
                # decision = self._make_ai_decision(stock_code, stock_info, indicators)
            else:
                decision = self._make_strategy_decision(stock_code)
            
            # 4. 执行交易（如果开启自动交易）
            execution_result = None
            if auto_trade:
                execution_result = self._execute_decision(
                    stock_code=stock_code,
                    decision=decision,
                    market_data=stock_info,
                   
                )
            
            # 5. 发送通知（如果需要）
            # TODO: 根据任务配置决定是否发送通知
            self._send_notification(stock_code, stock_info.get('name', ''), decision, execution_result, stock_info)
            
            return {
                'success': True,
                'stock_code': stock_code,
                'stock_name': stock_info.get('name', ''),
                'decision': decision,
                'market_data': stock_info,
                'indicators': indicators,
                'execution_result': execution_result
            } 
                
        except Exception as e:
            self.logger.error(f"分析股票失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _make_strategy_decision(self, stock_code: str) -> Dict:
        """
        根据策略选择决策逻辑
        """
        try:
            from app.policy.gs import load_xtquant_kline,compute_g_buy_sell
           
            kline_df = load_xtquant_kline(stock_code,'', '', period='1d', count=200)
            out = compute_g_buy_sell(kline_df)
            # 获取out 最后一条数据的 
            g_buy = 1
            # g_buy = out.tail(1)['g_buy']
            g_sell = out.tail(1)['g_sell']
            if g_buy == 1:
                action = 'BUY'
                confidence = 100
                reasoning = '策略买入'
            elif g_sell == 1:
                action = 'SELL'
                confidence = 100
                reasoning = '策略卖出'
            else :
                action = 'HOLD'
                confidence = 50
                reasoning = '策略持有'
            return {
                'action': action,
                'confidence': confidence,
                'reasoning': reasoning,
            }
        except Exception as e:
            self.logger.error(f"决策逻辑失败: {e}")
            return {
                'action': 'HOLD',
                'confidence': 50,
                'reasoning': f'决策失败: {str(e)}',
            }
    
    def _make_ai_decision(self, stock_code: str, stock_info: Dict, indicators: Dict) -> Dict:
        """
        AI决策逻辑（使用 DeepSeekClient）
        
        Args:
            stock_code: 股票代码
            stock_info: 股票信息
            indicators: 技术指标
            
        Returns:
            决策结果
        """
        try:
            if MonitorService._deepseek_client is None:
                MonitorService._deepseek_client = DeepSeekClient()
            
            # 获取账户信息
            account_info = qmt_service.get_account_info()
            
            # 检查是否已持仓
            position = qmt_service.get_position(stock_code)
            has_position = position is not None
            position_cost = position.get('cost_price', 0) if position else 0
            position_quantity = position.get('quantity', 0) if position else 0
            
            # 构建市场数据（兼容旧接口格式）
            market_data = {
                'name': stock_info.get('name', ''),
                'current_price': stock_info.get('current_price', 0),
                'change_pct': stock_info.get('change_percent', 0),
                'volume': stock_info.get('volume', 0),
                'ma5': indicators.get('ma5', 0),
                'ma20': indicators.get('ma20', 0),
                'rsi6': indicators.get('rsi', 50),
                'macd': indicators.get('macd', 0),
                **stock_info,
                **indicators
            }
            
            # 使用 DeepSeekClient 进行技术分析
            technical_report = MonitorService._deepseek_client.technical_analysis(
                stock_info, None, indicators
            )
            
            # 简化的AI决策：基于技术分析结果
            # 注意：这里使用简化的决策逻辑，完整版本应该调用 analyze_stock_and_decide
            # 但新的 DeepSeekClient 没有这个方法，所以使用技术分析结果进行决策
            
            current_price = stock_info.get('current_price', 0)
            ma5 = indicators.get('ma5', 0)
            ma20 = indicators.get('ma20', 0)
            rsi = indicators.get('rsi', 50)
            
            # 基于技术指标和AI分析结果做决策
            if has_position:
                # 有持仓：判断是否卖出
                if current_price < position_cost * 0.95:  # 止损
                    action = 'SELL'
                    confidence = 80
                    reasoning = f'触发止损，当前价{current_price:.2f}低于成本价{position_cost:.2f}的95%'
                elif current_price > position_cost * 1.10:  # 止盈
                    action = 'SELL'
                    confidence = 75
                    reasoning = f'达到止盈目标，当前价{current_price:.2f}高于成本价{position_cost:.2f}的10%'
                elif rsi > 70 or current_price < ma20:
                    action = 'SELL'
                    confidence = 70
                    reasoning = '技术指标显示超买或跌破均线，建议卖出'
                else:
                    action = 'HOLD'
                    confidence = 65
                    reasoning = '技术面稳定，继续持有'
            else:
                # 无持仓：判断是否买入
                if current_price > ma5 > ma20 and 30 < rsi < 70:
                    action = 'BUY'
                    confidence = 75
                    reasoning = '价格位于均线之上，RSI处于健康区间，技术面支持买入'
                else:
                    action = 'HOLD'
                    confidence = 60
                    reasoning = '技术信号不明确，建议观望'
            
            return {
                'action': action,
                'confidence': confidence,
                'reasoning': reasoning,
                'risk_level': 'medium',
                'position_size_pct': 20,
                'stop_loss_pct': 5,
                'take_profit_pct': 10,
                'key_price_levels': {
                    'support': ma20,
                    'resistance': indicators.get('bb_upper', current_price * 1.1)
                },
                'technical_analysis': technical_report[:200] + '...' if len(technical_report) > 200 else technical_report
            }
        except Exception as e:
            self.logger.error(f"AI决策失败: {e}")
            return {
                'action': 'HOLD',
                'confidence': 50,
                'reasoning': f'AI决策失败: {str(e)}',
                'risk_level': 'high',
                'position_size_pct': 0
            }
    
    def _execute_decision(self, stock_code: str, decision: Dict,
                         market_data: Dict) -> Dict:
        """
        执行AI决策
        
        Args:
            stock_code: 股票代码
            decision: AI决策
            market_data: 市场数据
            
        Returns:
            执行结果
        """

        # 先查找stock_code 的持仓信息
        position = qmt_service.get_position(stock_code)
        has_position = position is not None
   
        
        action = decision.get('action', '').upper()
        
        try:
            if action == 'BUY' :
                # 先判断是否持仓，如果持仓，则不买入
                if has_position:
                    return {   
                        'success': False,
                        'error': '已持仓，不买入'
                    }
                # 买入逻辑
                return self._execute_buy(stock_code, decision, market_data)

            elif action == 'SELL' and has_position:
                # 卖出逻辑
                if has_position: 
                    # 判断是否可以卖出
                    can_sell = position.get('can_use_volume', 0)
                    if can_sell <= 0:
                        return {
                            'success': False,
                            'error': 'T+1限制，今天买入的股票明天才能卖出'
                        }
                    
                return self._execute_sell(stock_code, decision, market_data)
            
            elif action == 'HOLD':
                # 持有，不操作
                return {
                    'success': True,
                    'action': 'HOLD',
                    'message': 'AI建议持有，未执行交易'
                }
            
            else:
                return {
                    'success': False,
                    'error': f'无效操作: {action} (has_position={has_position})'
                }
                
        except Exception as e:
            self.logger.error(f"[{stock_code}] 执行交易失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_buy(self, stock_code: str, decision: Dict, market_data: Dict) -> Dict:
        """执行买入"""
        try:
            # 获取账户信息
            account_info = qmt_service.get_account_info()
            available_cash = account_info.get('cash', 0)
            
            if available_cash <= 0:
                return {
                    'success': False,
                    'error': '账户可用资金不足'
                }
            
            # 计算买入金额
            # position_size_pct = decision.get('buy_amount', 20)
            # buy_amount = available_cash * (position_size_pct / 100)
            buy_amount = decision.get('buy_amount', 0)
            if buy_amount <= 0:
                return {
                    'success': False,
                    'error': '买入金额设置错误'
                }
            if buy_amount > available_cash:
                return {
                    'success': False,
                    'error': '买入金额大于账户可用资金'
                }
            
            # 计算买入数量（必须是100的整数倍）
            stock_quote = qmt_service.get_stock_quote(stock_code)
            if not stock_quote:
                return {
                    'success': False,
                    'error': '无法获取股票行情'
                }
            current_price = stock_quote.get('lastPrice', 0)
            if current_price <= 0:
                return {
                    'success': False,
                    'error': '股票行情价格为0，无法买入'
                }
            quantity = int(buy_amount / current_price / 100) * 100
            if quantity <= 0:
                return {
                    'success': False,
                    'error': '买入数量计算错误'
                }            
            # 执行买入
            result = qmt_service.buy_stock(
                stock_code=stock_code,
                quantity=quantity,
                price=current_price,
                order_type='market'
            )
            
            if result.get('success'):
                self.logger.info(f"[{stock_code}] 买入成功: {quantity}股 @ {current_price:.2f}元")
            else:
                self.logger.error(f"[{stock_code}] 买入失败: {result.get('error', '未知错误')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"[{stock_code}] 买入失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_sell(self, stock_code: str, decision: Dict, market_data: Dict) -> Dict:
        """执行卖出"""
        try:
            # 获取持仓
            position = qmt_service.get_position(stock_code)
            if not position:
                return {
                    'success': False,
                    'error': '未持有该股票'
                }

            # 可卖数量（考虑T+1限制）
            can_sell = position.get('can_use_volume', 0)
            if can_sell <= 0:
                return {
                    'success': False,
                    'error': 'T+1限制，今天买入的股票明天才能卖出'
                }
            
            # 执行卖出
            stock_quote = qmt_service.get_stock_quote(stock_code)
            if not stock_quote:
                return {
                    'success': False,
                    'error': '无法获取股票行情'
                }
            current_price = stock_quote.get('lastPrice', 0)
            if current_price <= 0:
                return {
                    'success': False,
                    'error': '股票行情价格为0，无法卖出'
                }
            
            result = qmt_service.sell_stock(
                stock_code=stock_code,
                quantity=can_sell,
                price=current_price,
                order_type='market'
            )
            
            if result.get('success'):
                # 计算盈亏
                cost_price = position.get('average_price', 0)
                if cost_price <= 0:
                    return {
                        'success': False,
                        'error': '持仓成本价格为0，无法计算盈亏'
                    }
                profit_loss = (current_price - cost_price) * can_sell
                
                self.logger.info(f"[{stock_code}] 卖出成功: {can_sell}股 @ {current_price:.2f}元, "
                               f"盈亏: {profit_loss:+.2f}元")
            else:
                self.logger.error(f"[{stock_code}] 卖出失败: {result.get('error', '未知错误')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"[{stock_code}] 卖出失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_notification(self, stock_code: str, stock_name: str,
                          decision: Dict, execution_result: Optional[Dict],
                          market_data: Dict):
        """
        发送通知
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            decision: AI决策
            execution_result: 执行结果
            market_data: 市场数据
        """
        try:
            action = decision.get('action', '').upper()
            
            # 仅在买入或卖出时发送通知，持有信号不发送
            if action not in ['BUY', 'SELL']:
                self.logger.debug(f"[{stock_code}] 决策为{action}，不发送通知")
                return
            
            # 构建通知内容
            action_text = {
                'BUY': '🟢 买入',
                'SELL': '🔴 卖出'
            }.get(action, action)
            
            message = f"{action_text}信号 - {stock_name}({stock_code})"
            
            # 简化的AI决策内容
            reasoning = decision.get('reasoning', '')
            reasoning_summary = reasoning[:150] + '...' if len(reasoning) > 150 else reasoning
            
            # 提取关键价位信息
            key_levels = decision.get('key_price_levels', {})
            support = key_levels.get('support', 'N/A')
            resistance = key_levels.get('resistance', 'N/A')
            
            # 构建详细内容
            content = f"""【{action_text}信号】{stock_name}({stock_code})

📊 市场信息
• 当前价: ¥{market_data.get('current_price', 0):.2f}
• 涨跌幅: {market_data.get('change_percent', 0):+.2f}%
• 成交量: {market_data.get('volume', 0):,.0f}手

🤖 AI决策
• 操作: {action_text}
• 信心度: {decision.get('confidence', 0)}%
• 风险: {decision.get('risk_level', '中')}

💡 核心理由
{reasoning_summary}

📈 关键价位
• 支撑位: {support}
• 阻力位: {resistance}
• 止盈: {decision.get('take_profit_pct', 'N/A')}%
• 止损: {decision.get('stop_loss_pct', 'N/A')}%

📉 技术指标
• MA5: {market_data.get('ma5', 0):.2f} / MA20: {market_data.get('ma20', 0):.2f}
• RSI: {market_data.get('rsi', 0):.1f}"""
            
            if execution_result:
                if execution_result.get('success'):
                    content += f"\n\n✅ 操作已自动执行"
                else:
                    content += f"\n\n⚠️ 执行失败: {execution_result.get('error')}"
            
            content += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 构建通知数据
            notification_data = {
                'symbol': stock_code,
                'name': stock_name,
                'type': '智能盯盘',
                'message': message,
                'details': content,
                'triggered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 使用通知服务发送（传入数据库会话以从数据库加载配置）
            notification_service = get_notification_service(db=self.db)
            success = notification_service.send_notification(notification_data)
            
            if success:
                self.logger.info(f"[{stock_code}] {action_text}通知已发送")
            else:
                self.logger.warning(f"[{stock_code}] {action_text}通知发送失败（可能未配置通知渠道）")
            
        except Exception as e:
            self.logger.error(f"[{stock_code}] 发送通知失败: {e}")

    

