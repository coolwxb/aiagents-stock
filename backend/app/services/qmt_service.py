"""  
QMT交易服务
基于 xtquant 官方文档实现
参考: https://dict.thinktrader.net/nativeApi/code_examples.html
"""
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session

from app.models.config import AppConfig


class TradeAction(Enum):
    """交易动作枚举"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "market"
    LIMIT = "limit"


class QMTService:
    """QMT交易服务类"""
    
    # 单例实例
    _instance = None
    _xttrader = None
    _account = None
    _connected = False
    _config = {}  # 缓存配置
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 尝试导入miniQMT模块
        self.xttrader_module = None
        self.xtdata_module = None
        self.xttype_module = None
        
        self._try_import_qmt()
    
    def _try_import_qmt(self):
        """尝试导入QMT模块"""
        try:
            from xtquant import xttrader, xtdata
            from xtquant.xttype import StockAccount
            from xtquant.xttrader import XtQuantTraderCallback
            
            self.xttrader_module = xttrader
            self.xtdata_module = xtdata
            self.StockAccount = StockAccount
            self.XtQuantTraderCallback = XtQuantTraderCallback
            
            print("miniQMT模块加载成功")
        except ImportError as e:
            print(f"miniQMT模块未安装: {e}")
            print("将使用模拟模式")
    
    def load_config(self, db: Session):
        """
        从数据库加载QMT配置
        
        Args:
            db: 数据库会话
        """
        try:
            # 查询QMT相关配置
            config_keys = [
                'MINIQMT_ENABLED',
                'MINIQMT_ACCOUNT_ID',
                'MINIQMT_ACCOUNT_TYPE',
                'MINIQMT_USERDATA_PATH'
            ]
            
            configs = db.query(AppConfig).filter(AppConfig.key.in_(config_keys)).all()
            
            # 转换为字典并缓存
            QMTService._config = {cfg.key: cfg.value for cfg in configs}
            
            # 设置默认值
            QMTService._config.setdefault('MINIQMT_ENABLED', 'false')
            QMTService._config.setdefault('MINIQMT_ACCOUNT_ID', '')
            QMTService._config.setdefault('MINIQMT_ACCOUNT_TYPE', 'STOCK')
            QMTService._config.setdefault('MINIQMT_USERDATA_PATH', 'E:\\zhongjin_qmt\\userdata_mini')
            
            self.logger.info(f"QMT配置已从数据库加载: enabled={QMTService._config.get('MINIQMT_ENABLED')}")
            
        except Exception as e:
            self.logger.error(f"加载QMT配置失败: {e}")
            # 使用默认配置
            QMTService._config = {
                'MINIQMT_ENABLED': 'false',
                'MINIQMT_ACCOUNT_ID': '',
                'MINIQMT_ACCOUNT_TYPE': 'STOCK',
                'MINIQMT_USERDATA_PATH': 'E:\\zhongjin_qmt\\userdata_mini'
            }
    
    @property
    def enabled(self) -> bool:
        """获取QMT启用状态"""
        return QMTService._config.get('MINIQMT_ENABLED', 'false').lower() == 'true'
    
    @property
    def account_id(self) -> str:
        """获取账户ID"""
        return QMTService._config.get('MINIQMT_ACCOUNT_ID', '')
    
    @property
    def account_type(self) -> str:
        """获取账户类型"""
        return QMTService._config.get('MINIQMT_ACCOUNT_TYPE', 'STOCK')
    
    @property
    def userdata_path(self) -> str:
        """获取用户数据路径"""
        return QMTService._config.get('MINIQMT_USERDATA_PATH', 'E:\\zhongjin_qmt\\userdata_mini')
    
    def connect(self) -> Tuple[bool, str]:
        """
        连接到MiniQMT（按照官方文档标准流程）
        
        Returns:
            (成功标志, 消息)
        """
        if not self.enabled:
            self.logger.info("QMT未启用，使用模拟模式")
            return False, "QMT未启用"
        
        if QMTService._connected:
            return True, "已连接"
        
        if not self.account_id:
            return False, "账户ID未配置，请在环境配置中设置"
        
        try:
            # 1. 创建回调类（简化版）
            class SimpleCallback(self.XtQuantTraderCallback):
                def on_disconnected(self):
                    logging.getLogger(__name__).warning("QMT连接断开")
                
                def on_stock_order(self, order):
                    logging.getLogger(__name__).info(f"委托回报: {order.order_remark}")
                
                def on_stock_trade(self, trade):
                    logging.getLogger(__name__).info(f"成交回报: {trade.order_remark}")
                
                def on_order_error(self, order_error):
                    logging.getLogger(__name__).error(
                        f"委托失败: {order_error.order_remark} {order_error.error_msg}"
                    )
            
            # 2. 创建API实例（使用时间戳作为session_id）
            session_id = int(time.time() * 1000)
            QMTService._xttrader = self.xttrader_module.XtQuantTrader(
                self.userdata_path,
                session_id
            )
            
            # 3. 注册回调
            callback = SimpleCallback()
            QMTService._xttrader.register_callback(callback)
            
            # 4. 启动交易线程
            QMTService._xttrader.start()
            
            # 5. 建立连接
            connect_result = QMTService._xttrader.connect()
            
            if connect_result == 0:
                # 6. 创建账户对象
                QMTService._account = self.StockAccount(self.account_id)
                
                # 7. 订阅账户
                QMTService._xttrader.subscribe(QMTService._account)
                
                QMTService._connected = True
                self.logger.info(f"miniQMT连接成功，账户: {self.account_id}, session: {session_id}")
                return True, f"已连接到账户 {self.account_id}"
            else:
                self.logger.error(f"miniQMT连接失败，错误码: {connect_result}")
                return False, f"连接失败，错误码: {connect_result}"
                
        except Exception as e:
            self.logger.error(f"连接miniQMT失败: {e}")
            return False, f"连接失败: {str(e)}"
    
    def disconnect(self):
        """断开连接"""
        if QMTService._xttrader:
            try:
                QMTService._xttrader.stop()
                QMTService._connected = False
                QMTService._xttrader = None
                QMTService._account = None
                self.logger.info("miniQMT已断开连接")
            except Exception as e:
                self.logger.error(f"断开连接失败: {e}")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return QMTService._connected and self.enabled
    
    def get_account_info(self) -> Dict:
        """
        获取账户信息（按照官方XtAsset数据结构）
        
        XtAsset官方字段:
        - account_id: 资金账户
        - cash: 可用资金
        - frozen_cash: 冻结资金
        - market_value: 持仓市值
        - total_asset: 总资产
        
        Returns:
            账户信息字典
        """
        if not self.is_connected():
            return {
                'available_cash': 0,
                'total_value': 0,
                'market_value': 0,
                'frozen_cash': 0,
                'positions_count': 0,
                'total_profit_loss': 0,
                'connected': False,
                'message': 'QMT未连接'
            }
        
        try:
            # 使用query_stock_asset查询资金（官方接口）
            asset = QMTService._xttrader.query_stock_asset(QMTService._account)
            
            # 获取所有持仓并计算总盈亏
            positions_list = self.get_all_positions()
            
            # 计算总浮动盈亏（汇总所有持仓盈亏）
            total_profit_loss = sum(pos.get('profit_loss', 0) for pos in positions_list)
            
            return {
                'account_id': self.account_id,
                'available_cash': asset.cash if hasattr(asset, 'cash') else 0,
                'total_value': asset.total_asset if hasattr(asset, 'total_asset') else 0,
                'market_value': asset.market_value if hasattr(asset, 'market_value') else 0,
                'frozen_cash': asset.frozen_cash if hasattr(asset, 'frozen_cash') else 0,
                'positions_count': len(positions_list),
                'total_profit_loss': total_profit_loss,
                'connected': True
            }
            
        except Exception as e:
            self.logger.error(f"获取账户信息失败: {e}")
            return {
                'available_cash': 0,
                'total_value': 0,
                'market_value': 0,
                'frozen_cash': 0,
                'positions_count': 0,
                'total_profit_loss': 0,
                'connected': False,
                'error': str(e)
            }
    
    def get_all_positions(self) -> List[Dict]:
        """
        获取所有持仓（按照官方XtPosition数据结构）
        
        XtPosition官方字段（实际可用）:
        - account_id: 资金账户
        - stock_code: 证券代码
        - volume: 持仓数量
        - can_use_volume: 可用数量（可卖）
        - open_price: 开仓价（成本价）
        - market_value: 持仓市值
        
        注意: 
        1. XtPosition没有stock_name字段，需要从行情数据获取
        2. XtPosition没有avg_price字段，使用open_price作为成本价
        3. XtPosition没有unrealized_profit字段，需要自己计算盈亏
        
        Returns:
            持仓列表
        """
        if not self.is_connected():
            return []
        
        try:
            # 使用query_stock_positions查询持仓（官方接口）
            positions = QMTService._xttrader.query_stock_positions(QMTService._account)
            
            if not positions:
                return []
            
            result = []
            for pos in positions:
                # XtPosition官方字段（实际可用）
                stock_code = pos.stock_code if hasattr(pos, 'stock_code') else ''
                quantity = pos.volume if hasattr(pos, 'volume') else 0
                can_sell = pos.can_use_volume if hasattr(pos, 'can_use_volume') else 0
                cost_price = pos.open_price if hasattr(pos, 'open_price') else 0  # 使用open_price作为成本价
                market_value_from_qmt = pos.market_value if hasattr(pos, 'market_value') else 0
                
                # 获取股票名称（从xtdata获取）
                stock_name = ''
                if stock_code:
                    try:
                        # 使用xtdata获取股票名称
                        instrument_detail = self.xtdata_module.get_instrument_detail(stock_code)
                        if instrument_detail:
                            stock_name = instrument_detail.get('InstrumentName', '')
                    except Exception as e:
                        self.logger.debug(f"获取{stock_code}名称失败: {e}")
                
                # 计算持仓天数
                holding_days = 0
                buy_date = ''
                if hasattr(pos, 'open_date') and pos.open_date:
                    try:
                        buy_date = str(pos.open_date)
                        open_date = datetime.strptime(buy_date, '%Y%m%d')
                        holding_days = (datetime.now() - open_date).days
                    except:
                        pass
                
                # 获取当前价（从xtdata获取实时行情）
                current_price = 0
                if stock_code:
                    try:
                        # 使用xtdata获取实时行情
                        tick = self.xtdata_module.get_full_tick([stock_code])
                        if tick and stock_code in tick:
                            current_price = tick[stock_code].get('lastPrice', 0)
                    except Exception as e:
                        self.logger.debug(f"获取{stock_code}实时行情失败: {e}")
                
                # 如果没有获取到实时价，使用成本价估算
                if current_price == 0 and cost_price > 0:
                    current_price = cost_price
                
                # 计算盈亏（自己计算）
                profit_loss_pct = 0
                profit_loss = 0
                
                if cost_price > 0 and current_price > 0:
                    profit_loss_pct = (current_price - cost_price) / cost_price * 100
                    profit_loss = (current_price - cost_price) * quantity
                
                # 市值（优先使用QMT返回的市值）
                market_value = market_value_from_qmt
                if market_value == 0 and current_price > 0:
                    market_value = current_price * quantity
                
                result.append({
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'quantity': quantity,
                    'can_sell': can_sell,
                    'cost_price': cost_price,
                    'current_price': current_price,
                    'market_value': market_value,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct,
                    'holding_days': holding_days,
                    'buy_date': buy_date
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取所有持仓失败: {e}")
            return []
    
    def get_position(self, stock_code: str) -> Optional[Dict]:
        """
        获取指定股票的持仓信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            持仓信息，如果未持有则返回None
        """
        positions = self.get_all_positions()
        
        # 查找指定股票
        for pos in positions:
            if pos['stock_code'] == stock_code or pos['stock_code'] == self._format_stock_code(stock_code):
                return pos
        
        return None
    
    def buy_stock(self, stock_code: str, quantity: int, 
                 price: float = 0, order_type: str = 'market') -> Dict:
        """
        买入股票
        
        Args:
            stock_code: 股票代码
            quantity: 数量（必须是100的整数倍）
            price: 价格（限价单时使用）
            order_type: 订单类型 ('market': 市价, 'limit': 限价)
            
        Returns:
            订单结果
        """
        if not self.is_connected():
            return {
                'success': False,
                'error': 'QMT未连接',
                'message': '模拟模式：买入订单已记录但未实际执行'
            }
        
        # 检查数量是否是100的整数倍
        if quantity % 100 != 0:
            return {
                'success': False,
                'error': 'A股买入数量必须是100的整数倍（1手=100股）'
            }
        
        try:
            # 构造完整股票代码
            full_code = self._format_stock_code(stock_code)
            
            # 导入常量
            from xtquant import xtconstant
            
            # 根据订单类型选择
            if order_type == 'market':
                price_type = xtconstant.MARKET_PEER_PRICE_FIRST
            else:
                price_type = xtconstant.FIX_PRICE
            
            # 异步下单
            order_id = QMTService._xttrader.order_stock_async(
                account=QMTService._account,
                stock_code=full_code,
                order_type=xtconstant.STOCK_BUY,
                order_volume=quantity,
                price_type=price_type,
                price=price,
                strategy_name='monitor',
                order_remark=f'买入{stock_code}'
            )
            
            if order_id > 0:
                self.logger.info(f"买入订单已提交: {stock_code}, 数量: {quantity}, 订单号: {order_id}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'stock_code': stock_code,
                    'quantity': quantity,
                    'price': price,
                    'order_type': order_type,
                    'message': '买入订单已提交'
                }
            else:
                return {
                    'success': False,
                    'error': f'下单失败，订单号: {order_id}'
                }
                
        except Exception as e:
            self.logger.error(f"买入股票失败 {stock_code}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sell_stock(self, stock_code: str, quantity: int, 
                  price: float = 0, order_type: str = 'market') -> Dict:
        """
        卖出股票
        
        Args:
            stock_code: 股票代码
            quantity: 数量
            price: 价格（限价单时使用）
            order_type: 订单类型 ('market': 市价, 'limit': 限价)
            
        Returns:
            订单结果
        """
        if not self.is_connected():
            return {
                'success': False,
                'error': 'QMT未连接',
                'message': '模拟模式：卖出订单已记录但未实际执行'
            }
        
        try:
            # 检查是否有持仓
            position = self.get_position(stock_code)
            if not position:
                return {
                    'success': False,
                    'error': f'未持有股票 {stock_code}'
                }
            
            # 检查可卖数量（T+1限制）
            if quantity > position['can_sell']:
                return {
                    'success': False,
                    'error': f'可卖数量不足（可卖: {position["can_sell"]}股，T+1限制）'
                }
            
            # 构造完整股票代码
            full_code = self._format_stock_code(stock_code)
            
            # 导入常量
            from xtquant import xtconstant
            
            # 根据订单类型选择
            if order_type == 'market':
                price_type = xtconstant.MARKET_PEER_PRICE_FIRST
            else:
                price_type = xtconstant.FIX_PRICE
            
            # 异步下单
            order_id = QMTService._xttrader.order_stock_async(
                account=QMTService._account,
                stock_code=full_code,
                order_type=xtconstant.STOCK_SELL,
                order_volume=quantity,
                price_type=price_type,
                price=price,
                strategy_name='monitor',
                order_remark=f'卖出{stock_code}'
            )
            
            if order_id > 0:
                self.logger.info(f"卖出订单已提交: {stock_code}, 数量: {quantity}, 订单号: {order_id}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'stock_code': stock_code,
                    'quantity': quantity,
                    'price': price,
                    'order_type': order_type,
                    'message': '卖出订单已提交'
                }
            else:
                return {
                    'success': False,
                    'error': f'下单失败，订单号: {order_id}'
                }
                
        except Exception as e:
            self.logger.error(f"卖出股票失败 {stock_code}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_stock_code(self, stock_code: str) -> str:
        """
        格式化股票代码（添加市场后缀）
        
        Args:
            stock_code: 股票代码（如：600519）
            
        Returns:
            完整代码（如：600519.SH）
        """
        # 如果已经包含市场后缀，直接返回
        if '.' in stock_code:
            return stock_code
        
        # 沪市：6开头
        if stock_code.startswith('6'):
            return f"{stock_code}.SH"
        # 深市：0、3开头
        elif stock_code.startswith(('0', '3')):
            return f"{stock_code}.SZ"
        else:
            return stock_code


# 全局QMT服务实例
qmt_service = QMTService()
