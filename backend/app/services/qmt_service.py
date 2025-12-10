"""  
QMT交易服务
基于 xtquant 官方文档实现
参考: https://dict.thinktrader.net/nativeApi/code_examples.html
"""
import logging
import time
import threading
import json
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session

from app.models.config import AppConfig
from app.utils.stock_code import add_market_suffix

# Redis 导入
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class TradeAction(Enum):
    """交易动作枚举"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus:
    """订单状态常量（来自xtconstant）"""
    UNREPORTED = 48       # 未报
    WAIT_REPORTING = 49   # 待报
    REPORTED = 50         # 已报
    REPORTED_CANCEL = 51  # 已报待撤
    PARTSUCC_CANCEL = 52  # 部成待撤
    PART_CANCEL = 53      # 部撤
    CANCELED = 54         # 已撤
    PART_SUCC = 55        # 部成
    SUCCEEDED = 56        # 已成
    JUNK = 57             # 废单
    UNKNOWN = 255         # 未知
    
    # 最终状态集合（不再变化的状态）
    FINAL_STATUS = {54, 56, 57, 53}
    
    @staticmethod
    def get_name(status: int) -> str:
        """获取状态名称"""
        names = {
            48: '未报', 49: '待报', 50: '已报', 51: '已报待撤',
            52: '部成待撤', 53: '部撤', 54: '已撤', 55: '部成',
            56: '已成', 57: '废单', 255: '未知'
        }
        return names.get(status, f'未知({status})')
    
    @staticmethod
    def is_final(status: int) -> bool:
        """判断是否为最终状态"""
        return status in OrderStatus.FINAL_STATUS
    
    @staticmethod
    def is_success(status: int) -> bool:
        """判断是否成功"""
        return status == OrderStatus.SUCCEEDED


class QMTEventBus:
    """
    QMT事件总线 - 基于Redis的发布订阅模式
    用于解耦回调和业务逻辑，支持跨进程通信
    
    当 Redis 不可用时，自动降级为内存模式
    
    Redis 配置从数据库 app_config 表中获取:
    - REDIS_ENABLED: 是否启用 Redis ('true'/'false')
    - REDIS_URL: Redis 连接地址 (如 'redis://localhost:6379/0')
    """
    
    # 事件类型常量
    EVENT_ORDER_STATUS = 'order_status'      # 订单状态变化
    EVENT_ORDER_ERROR = 'order_error'        # 下单错误
    EVENT_TRADE = 'trade'                    # 成交回报
    EVENT_CANCEL_ERROR = 'cancel_error'      # 撤单错误
    EVENT_DISCONNECTED = 'disconnected'      # 连接断开
    EVENT_ACCOUNT_STATUS = 'account_status'  # 账户状态
    
    # Redis 频道前缀
    CHANNEL_PREFIX = 'qmt:event:'
    
    # Redis 配置缓存
    _redis_config = {}
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_instance()
        return cls._instance
    
    def _init_instance(self):
        """初始化实例"""
        self._subscribers = {}  # 内存订阅者 {event_type: [callback, ...]}
        self._subscriber_lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Redis 相关
        self._redis_client: Optional[redis.Redis] = None
        self._redis_pubsub: Optional[redis.client.PubSub] = None
        self._redis_listener_thread: Optional[threading.Thread] = None
        self._redis_running = False
        self._use_redis = False
        
        # 注意：不在这里初始化 Redis，等待 load_config 被调用
        self.logger.info("QMT事件总线已初始化（内存模式），等待加载 Redis 配置")
    
    def load_config(self, db: Session):
        """
        从数据库加载 Redis 配置并初始化连接
        
        数据库配置项:
        - REDIS_ENABLED: 是否启用 ('true'/'false')
        - REDIS_HOST: 主机地址 (默认 'localhost')
        - REDIS_PORT: 端口 (默认 '6379')
        - REDIS_PASSWORD: 密码 (可选)
        - REDIS_DB: 数据库编号 (默认 '0')
        
        Args:
            db: 数据库会话
        """
        try:
            config_keys = ['REDIS_ENABLED', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD', 'REDIS_DB']
            configs = db.query(AppConfig).filter(AppConfig.key.in_(config_keys)).all()
            
            QMTEventBus._redis_config = {cfg.key: cfg.value for cfg in configs}
            
            # 设置默认值
            QMTEventBus._redis_config.setdefault('REDIS_ENABLED', 'false')
            QMTEventBus._redis_config.setdefault('REDIS_HOST', 'localhost')
            QMTEventBus._redis_config.setdefault('REDIS_PORT', '6379')
            QMTEventBus._redis_config.setdefault('REDIS_PASSWORD', '')
            QMTEventBus._redis_config.setdefault('REDIS_DB', '0')
            
            self.logger.info(f"Redis 配置已从数据库加载: enabled={self.redis_enabled}, host={self.redis_host}")
            
            # 初始化 Redis 连接
            self._init_redis()
            
        except Exception as e:
            self.logger.error(f"加载 Redis 配置失败: {e}")
            QMTEventBus._redis_config = {
                'REDIS_ENABLED': 'false',
                'REDIS_URL': 'redis://localhost:6379/0'
            }
    
    @property
    def redis_enabled(self) -> bool:
        """获取 Redis 启用状态"""
        return QMTEventBus._redis_config.get('REDIS_ENABLED', 'false').lower() == 'true'
    
    @property
    def redis_host(self) -> str:
        """获取 Redis 主机"""
        return QMTEventBus._redis_config.get('REDIS_HOST', 'localhost')
    
    @property
    def redis_port(self) -> int:
        """获取 Redis 端口"""
        try:
            return int(QMTEventBus._redis_config.get('REDIS_PORT', '6379'))
        except ValueError:
            return 6379
    
    @property
    def redis_password(self) -> Optional[str]:
        """获取 Redis 密码"""
        pwd = QMTEventBus._redis_config.get('REDIS_PASSWORD', '')
        return pwd if pwd else None
    
    @property
    def redis_db(self) -> int:
        """获取 Redis 数据库编号"""
        try:
            return int(QMTEventBus._redis_config.get('REDIS_DB', '0'))
        except ValueError:
            return 0
    
    def _init_redis(self):
        """初始化 Redis 连接"""
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis 模块未安装，使用内存模式")
            return
        
        if not self.redis_enabled:
            self.logger.info("Redis 未启用，使用内存模式")
            return
        
        try:
            self._redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                db=self.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            self._redis_client.ping()
            self._use_redis = True
            self.logger.info(f"Redis 事件总线连接成功: {self.redis_host}:{self.redis_port}")
            print(f"✅ QMT事件总线 Redis 连接成功: {self.redis_host}:{self.redis_port}")
        except Exception as e:
            self.logger.warning(f"Redis 连接失败，降级为内存模式: {e}")
            print(f"⚠️ Redis 连接失败，QMT事件总线使用内存模式: {e}")
            self._redis_client = None
            self._use_redis = False
    
    def _get_channel_name(self, event_type: str) -> str:
        """获取 Redis 频道名称"""
        return f"{self.CHANNEL_PREFIX}{event_type}"
    
    def _start_redis_listener(self):
        """启动 Redis 订阅监听线程"""
        if not self._use_redis or self._redis_running:
            return
        
        try:
            self._redis_pubsub = self._redis_client.pubsub()
            self._redis_running = True
            
            def listener_loop():
                """监听循环"""
                while self._redis_running:
                    try:
                        message = self._redis_pubsub.get_message(timeout=1.0)
                        if message and message['type'] == 'message':
                            channel = message['channel']
                            data_str = message['data']
                            
                            # 解析事件类型
                            event_type = channel.replace(self.CHANNEL_PREFIX, '')
                            
                            # 解析数据
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                self.logger.error(f"JSON 解析失败: {data_str}")
                                continue
                            
                            # 调用本地订阅者
                            self._notify_local_subscribers(event_type, data)
                    except Exception as e:
                        if self._redis_running:
                            self.logger.error(f"Redis 监听异常: {e}")
                            time.sleep(1)
            
            self._redis_listener_thread = threading.Thread(
                target=listener_loop,
                daemon=True,
                name="QMTEventBus-RedisListener"
            )
            self._redis_listener_thread.start()
            self.logger.info("Redis 事件监听线程已启动")
        except Exception as e:
            self.logger.error(f"启动 Redis 监听失败: {e}")
            self._redis_running = False
    
    def _stop_redis_listener(self):
        """停止 Redis 订阅监听"""
        self._redis_running = False
        if self._redis_pubsub:
            try:
                self._redis_pubsub.close()
            except:
                pass
            self._redis_pubsub = None
    
    def _notify_local_subscribers(self, event_type: str, data: Dict):
        """通知本地订阅者"""
        with self._subscriber_lock:
            subscribers = self._subscribers.get(event_type, []).copy()
        
        for callback in subscribers:
            try:
                threading.Thread(target=callback, args=(data,), daemon=True).start()
            except Exception as e:
                self.logger.error(f"本地回调执行失败 [{event_type}]: {e}")
    
    def subscribe(self, event_type: str, callback: Callable[[Dict], None]) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数，接收事件数据字典
        """
        with self._subscriber_lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                self.logger.debug(f"订阅事件: {event_type}")
        
        # Redis 模式下订阅频道
        if self._use_redis:
            try:
                channel = self._get_channel_name(event_type)
                if self._redis_pubsub is None:
                    self._start_redis_listener()
                self._redis_pubsub.subscribe(channel)
                self.logger.debug(f"Redis 订阅频道: {channel}")
            except Exception as e:
                self.logger.error(f"Redis 订阅失败: {e}")
    
    def unsubscribe(self, event_type: str, callback: Callable[[Dict], None]) -> None:
        """
        取消订阅
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        with self._subscriber_lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)
                    self.logger.debug(f"取消订阅: {event_type}")
                
                # 如果该事件类型没有订阅者了，取消 Redis 订阅
                if self._use_redis and not self._subscribers[event_type]:
                    try:
                        channel = self._get_channel_name(event_type)
                        if self._redis_pubsub:
                            self._redis_pubsub.unsubscribe(channel)
                    except Exception as e:
                        self.logger.error(f"Redis 取消订阅失败: {e}")
    
    def publish(self, event_type: str, data: Dict) -> None:
        """
        发布事件（广播给所有订阅者）
        
        Redis 模式：通过 Redis Pub/Sub 广播，支持跨进程
        内存模式：直接通知本地订阅者
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        # 添加事件元数据
        data['_event_type'] = event_type
        data['_timestamp'] = time.time()
        data['_datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self._use_redis:
            try:
                channel = self._get_channel_name(event_type)
                message = json.dumps(data, ensure_ascii=False, default=str)
                self._redis_client.publish(channel, message)
                self.logger.debug(f"Redis 发布事件: {event_type}")
            except Exception as e:
                self.logger.error(f"Redis 发布失败，降级为本地通知: {e}")
                self._notify_local_subscribers(event_type, data)
        else:
            # 内存模式：直接通知本地订阅者
            self._notify_local_subscribers(event_type, data)
    
    def publish_sync(self, event_type: str, data: Dict) -> None:
        """
        同步发布事件（在当前线程执行本地回调）
        
        注意：Redis 发布仍然是异步的，但本地回调会同步执行
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        data['_event_type'] = event_type
        data['_timestamp'] = time.time()
        data['_datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Redis 模式下也发布到 Redis
        if self._use_redis:
            try:
                channel = self._get_channel_name(event_type)
                message = json.dumps(data, ensure_ascii=False, default=str)
                self._redis_client.publish(channel, message)
            except Exception as e:
                self.logger.error(f"Redis 同步发布失败: {e}")
        
        # 同步执行本地回调
        with self._subscriber_lock:
            subscribers = self._subscribers.get(event_type, []).copy()
        
        for callback in subscribers:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"事件回调执行失败 [{event_type}]: {e}")
    
    def is_redis_mode(self) -> bool:
        """检查是否使用 Redis 模式"""
        return self._use_redis
    
    def get_status(self) -> Dict:
        """获取事件总线状态"""
        with self._subscriber_lock:
            subscriber_counts = {k: len(v) for k, v in self._subscribers.items()}
        
        return {
            'mode': 'redis' if self._use_redis else 'memory',
            'redis_enabled': self.redis_enabled,
            'redis_host': self.redis_host if self._use_redis else None,
            'redis_port': self.redis_port if self._use_redis else None,
            'redis_connected': self._use_redis and self._redis_client is not None,
            'listener_running': self._redis_running,
            'subscriber_counts': subscriber_counts
        }
    
    def close(self):
        """关闭事件总线"""
        self._stop_redis_listener()
        if self._redis_client:
            try:
                self._redis_client.close()
            except:
                pass
            self._redis_client = None
        self._use_redis = False
        self.logger.info("QMT事件总线已关闭")


# 全局事件总线实例
qmt_event_bus = QMTEventBus()


class QMTService:
    """QMT交易服务类"""
    
    # 单例实例
    _instance = None
    _xttrader = None
    _account = None
    _connected = False
    _config = {}  # 缓存配置
    
    # 全推数据存储（内存中）
    _whole_quote_data = {}  # {stock_code: {行情数据}}
    _whole_quote_lock = threading.Lock()  # 线程锁，保护数据更新
    _whole_quote_subscribed = False  # 是否已订阅全推
    _whole_quote_seq = None  # 全推订阅号
    
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
        """尝试导入QMT模块（路径已在 main.py 启动时初始化）"""
        try:
            from xtquant import xttrader, xtdata
            from xtquant.xttype import StockAccount
            from xtquant.xttrader import XtQuantTraderCallback
            
            self.xttrader_module = xttrader
            self.xtdata_module = xtdata
            self.StockAccount = StockAccount
            self.XtQuantTraderCallback = XtQuantTraderCallback
            
            self.logger.info("miniQMT模块加载成功")
            print("✅ miniQMT模块加载成功")
            
            # QMT加载成功后，初始化全推数据订阅
            self._init_whole_quote_subscribe()
            
        except ImportError as e:
            self.logger.warning(f"QMTService miniQMT模块未安装: {e}")
            print(f"⚠️ QMTService miniQMT模块未安装: {e}")
            print("将使用模拟模式")
        except Exception as e:
            self.logger.warning(f"QMTService 初始化失败: {e}")
            print(f"⚠️ QMTService 初始化失败: {e}")
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
            # 1. 创建回调类（通过事件总线广播消息）
            class MyXtQuantTraderCallback(self.XtQuantTraderCallback):
                def on_disconnected(self):
                    """连接断开回调"""
                    print("connection lost")
                    QMTService._connected = False
                    qmt_event_bus.publish(QMTEventBus.EVENT_DISCONNECTED, {
                        'message': '连接已断开'
                    })
                
                def on_account_status(self, status):
                    """账号状态信息推送"""
                    print(f"on_account_status: {status.account_id}, {status.account_type}, {status.status}")
                    qmt_event_bus.publish(QMTEventBus.EVENT_ACCOUNT_STATUS, {
                        'account_id': status.account_id,
                        'account_type': status.account_type,
                        'status': status.status
                    })
                
                def on_stock_order(self, order):
                    """
                    委托信息推送 - 核心订单状态回调
                    通过事件总线广播订单状态变化
                    """
                   
                    print(f"on_stock_order: {order.stock_code}, status={order.order_status}({OrderStatus.get_name(order.order_status)}), order_id={order.order_id}, sysid={order.order_sysid}")
                    qmt_event_bus.publish(QMTEventBus.EVENT_ORDER_STATUS, {
                        'order_id': order.order_id, #订单编号
                        'order_sysid': order.order_sysid, #柜台合同编号
                        'stock_code': order.stock_code,
                        'order_status': order.order_status,
                        'order_status_name': OrderStatus.get_name(order.order_status),
                        'is_final': OrderStatus.is_final(order.order_status),
                        'is_success': OrderStatus.is_success(order.order_status),
                        'order_volume': getattr(order, 'order_volume', 0),
                        'traded_volume': getattr(order, 'traded_volume', 0),
                        'traded_price': getattr(order, 'traded_price', 0),
                        'order_type': getattr(order, 'order_type', 0),
                        'price': getattr(order, 'price', 0)
                    })
                
                def on_stock_trade(self, trade):
                    """成交信息推送"""
                    print(f"on_stock_trade: {trade.stock_code}, order_id={trade.order_id}")
                    qmt_event_bus.publish(QMTEventBus.EVENT_TRADE, {
                        'account_id': trade.account_id,
                        'order_id': trade.order_id,
                        'order_sysid': trade.order_sysid,
                        'stock_code': trade.stock_code,
                        'traded_volume': getattr(trade, 'traded_volume', 0),
                        'traded_price': getattr(trade, 'traded_price', 0),
                        'trade_time': getattr(trade, 'trade_time', '')
                    })
                
                def on_order_error(self, order_error):
                    """下单失败信息推送"""
                    print(f"on_order_error: order_id={order_error.order_id}, error_id={order_error.error_id}, msg={order_error.error_msg}")
                    qmt_event_bus.publish(QMTEventBus.EVENT_ORDER_ERROR, {
                        'order_id': order_error.order_id,
                        'order_sysid': order_error.order_sysid,
                        'error_id': order_error.error_id,
                        'error_msg': order_error.error_msg
                    })
                
                def on_cancel_error(self, cancel_error):
                    """撤单失败信息推送"""
                    print(f"on_cancel_error: order_id={cancel_error.order_id}, error_id={cancel_error.error_id}, msg={cancel_error.error_msg}")
                    qmt_event_bus.publish(QMTEventBus.EVENT_CANCEL_ERROR, {
                        'order_id': cancel_error.order_id,
                        'order_sysid': cancel_error.order_sysid,
                        'error_id': cancel_error.error_id,
                        'error_msg': cancel_error.error_msg
                    })
                
                def on_order_stock_async_response(self, response):
                    """异步下单回报推送"""
                    print(f"on_order_stock_async_response: account={response.account_id}, order_id={response.order_id}, seq={response.seq}")
                
                def on_smt_appointment_async_response(self, response):
                    """预约委托异步回报"""
                    print(f"on_smt_appointment_async_response: account={response.account_id}, sysid={response.order_sysid}")

            
            # 2. 创建API实例（使用时间戳作为session_id）
            session_id = int(time.time() * 1000)
            QMTService._xttrader = self.xttrader_module.XtQuantTrader(
                self.userdata_path,
                session_id
            )
            
            # 3. 注册回调
            callback = MyXtQuantTraderCallback()
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
        # 取消全推数据订阅
        self.unsubscribe_whole_quote()
        
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
        买入股票（异步下单）
        
        订单提交后，最终成交状态通过事件总线广播：
        - 订阅 QMTEventBus.EVENT_ORDER_STATUS 获取订单状态变化
        - 当 order_status == 56 (OrderStatus.SUCCEEDED) 时表示成交成功
        
        Args:
            stock_code: 股票代码
            quantity: 数量（必须是100的整数倍）
            price: 价格（限价单时使用）
            order_type: 订单类型 ('market': 市价, 'limit': 限价)
            
        Returns:
            订单提交结果（注意：success=True仅表示订单提交成功，不代表成交）
        """
        # 检查连接状态，未连接则尝试重连
        if not self.is_connected():
            self.logger.info("QMT未连接，尝试重新连接...")
            success, msg = self.connect()
            if not success:
                return {
                    'success': False,
                    'submitted': False,
                    'error': f'QMT连接失败: {msg}',
                    'message': '模拟模式：买入订单已记录但未实际执行'
                }
        
        # 检查数量是否是100的整数倍
        if quantity % 100 != 0:
            return {
                'success': False,
                'submitted': False,
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
            
            # order_stock 返回: 成功时返回大于0的正整数, 失败时返回-1
            if order_id > 0:
                self.logger.info(f"买入订单已提交: {stock_code}, 数量: {quantity}, 订单号: {order_id}")
                return {
                    'success': True,
                    'submitted': True,
                    'order_id': order_id,
                    'stock_code': full_code,
                    'quantity': quantity,
                    'price': price,
                    'order_type': order_type,
                    'action': 'buy',
                    'message': '买入订单已提交，请通过事件总线订阅订单状态'
                }
            else:
                self.logger.error(f"买入订单提交失败: {stock_code}, 数量: {quantity}, 订单号: {order_id}")
                return {
                    'success': False,
                    'submitted': False,
                    'error': f'下单提交失败，订单号: {order_id}'
                }
        except Exception as e:
            self.logger.error(f"买入股票失败 {stock_code}: {e}")
            return {
                'success': False,
                'submitted': False,
                'error': str(e)
            }
    
    def sell_stock(self, stock_code: str, quantity: int, 
                  price: float = 0, order_type: str = 'market') -> Dict:
        """
        卖出股票（异步下单）
        
        订单提交后，最终成交状态通过事件总线广播：
        - 订阅 QMTEventBus.EVENT_ORDER_STATUS 获取订单状态变化
        - 当 order_status == 56 (OrderStatus.SUCCEEDED) 时表示成交成功
        
        Args:
            stock_code: 股票代码
            quantity: 数量
            price: 价格（限价单时使用）
            order_type: 订单类型 ('market': 市价, 'limit': 限价)
            
        Returns:
            订单提交结果（注意：success=True仅表示订单提交成功，不代表成交）
        """
        # 检查连接状态，未连接则尝试重连
        if not self.is_connected():
            self.logger.info("QMT未连接，尝试重新连接...")
            success, msg = self.connect()
            if not success:
                return {
                    'success': False,
                    'submitted': False,
                    'error': f'QMT连接失败: {msg}',
                    'message': '模拟模式：卖出订单已记录但未实际执行'
                }
        
        try:
            # 检查是否有持仓
            position = self.get_position(stock_code)
            if not position:
                return {
                    'success': False,
                    'submitted': False,
                    'error': f'未持有股票 {stock_code}'
                }
            
            # 检查可卖数量（T+1限制）
            if quantity > position['can_sell']:
                return {
                    'success': False,
                    'submitted': False,
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
                    'submitted': True,
                    'order_id': order_id,
                    'stock_code': full_code,
                    'quantity': quantity,
                    'price': price,
                    'order_type': order_type,
                    'action': 'sell',
                    'message': '卖出订单已提交，请通过事件总线订阅订单状态'
                }
            else:
                self.logger.error(f"卖出订单提交失败: {stock_code}, 数量: {quantity}, 订单号: {order_id}")
                return {
                    'success': False,
                    'submitted': False,
                    'error': f'下单提交失败，订单号: {order_id}'
                }
                
        except Exception as e:
            self.logger.error(f"卖出股票失败 {stock_code}: {e}")
            return {
                'success': False,
                'submitted': False,
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
        
        try:
            return add_market_suffix(stock_code)
        except (ValueError, TypeError):
            # 无法识别的代码，原样返回
            return stock_code
    
    def _init_whole_quote_subscribe(self):
        """
        初始化全推数据订阅
        参考文档: https://dict.thinktrader.net/nativeApi/xtdata.html?id=T87jC8#%E8%AE%A2%E9%98%85%E5%85%A8%E6%8E%A8%E8%A1%8C%E6%83%85
        """
        if not self.xtdata_module:
            self.logger.warning("xtdata模块未加载，无法订阅全推数据")
            return
        
        if QMTService._whole_quote_subscribed:
            print("全推数据已订阅，跳过重复订阅")
            return
        
        try:
            # 连接xtdata（如果未连接）
            try:
                self.xtdata_module.connect()
                print("xtdata连接成功")
            except Exception as e:
                print(f"xtdata连接失败（可能已连接）: {e}")
            
            # 定义全推数据回调函数
            # 使用闭包捕获logger引用
            logger_ref = self.logger
            index = 0
            def on_whole_quote_data(datas):
                """
                全推数据回调函数
                
                Args:
                    datas: 全推数据字典，格式为 {stock_code: {行情字段}}
                """
               
                try:
                    with QMTService._whole_quote_lock:
                        # 更新内存中的数据
                        for stock_code, quote_data in datas.items():
                            # 添加更新时间戳
                            quote_data['update_time'] = time.time()
                            quote_data['update_datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # 更新或新增数据
                            QMTService._whole_quote_data[stock_code] = quote_data
                        
                        
                
                except Exception as e:
                    print(f"处理全推数据回调失败: {e}")
            
            # 订阅全推行情（订阅沪深两市）
            # 可以订阅市场代码 ['SH', 'SZ'] 或具体股票代码列表
            market_list = ['SH', 'SZ']  # 订阅上海和深圳市场
            
            QMTService._whole_quote_seq = self.xtdata_module.subscribe_whole_quote(
                market_list,
                callback=on_whole_quote_data
            )
            
            if QMTService._whole_quote_seq:
                QMTService._whole_quote_subscribed = True
                print(f"全推数据订阅成功，订阅号: {QMTService._whole_quote_seq}, 市场: {market_list}")
                print(f"✅ 全推数据订阅成功，订阅号: {QMTService._whole_quote_seq}")
            else:
                print("全推数据订阅失败，返回订阅号为None")
                
        except Exception as e:
            print(f"初始化全推数据订阅失败: {e}")
            print(f"⚠️ 全推数据订阅失败: {e}")
    
    def unsubscribe_whole_quote(self):
        """
        取消全推数据订阅
        """
        if not QMTService._whole_quote_subscribed or not QMTService._whole_quote_seq:
            return
        
        try:
            if self.xtdata_module:
                self.xtdata_module.unsubscribe_quote(QMTService._whole_quote_seq)
                QMTService._whole_quote_subscribed = False
                QMTService._whole_quote_seq = None
                self.logger.info("全推数据订阅已取消")
        except Exception as e:
            self.logger.error(f"取消全推数据订阅失败: {e}")
    
    def get_whole_quote_data(self, stock_code: Optional[str] = None) -> Dict:
        """
        获取全推实时行情数据
        
        Args:
            stock_code: 股票代码（如：600519 或 600519.SH），如果为None则返回所有数据
        
        Returns:
            行情数据字典
            - 如果指定stock_code，返回该股票的行情数据
            - 如果stock_code为None，返回所有股票的行情数据
        """
        with QMTService._whole_quote_lock:
            if stock_code is None:
                # 返回所有数据
                return QMTService._whole_quote_data.copy()
            else:
                # 格式化股票代码
                full_code = self._format_stock_code(stock_code)
                
                # 尝试多种格式查找
                quote_data = None
                
                # 1. 直接查找完整代码
                if full_code in QMTService._whole_quote_data:
                    quote_data = QMTService._whole_quote_data[full_code]
                # 2. 查找原始代码
                elif stock_code in QMTService._whole_quote_data:
                    quote_data = QMTService._whole_quote_data[stock_code]
                # 3. 查找不带点的代码
                elif full_code.replace('.', '') in QMTService._whole_quote_data:
                    code_no_dot = full_code.replace('.', '')
                    quote_data = QMTService._whole_quote_data[code_no_dot]
                
                if quote_data:
                    return quote_data.copy()
                else:
                    return {}
    
    def get_stock_quote(self, stock_code: str) -> Optional[Dict]:
        """
        获取指定股票的实时行情（便捷方法）
        
        Args:
            stock_code: 股票代码（如：600519 或 600519.SH）
        
        Returns:
            行情数据字典，如果未找到返回None
        """
        quote_data = self.get_whole_quote_data(stock_code)
        return quote_data if quote_data else None
    
    def get_stocks_quote(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """
        批量获取多个股票的实时行情
        
        Args:
            stock_codes: 股票代码列表
        
        Returns:
            {stock_code: {行情数据}} 字典
        """
        result = {}
        for stock_code in stock_codes:
            quote_data = self.get_whole_quote_data(stock_code)
            if quote_data:
                result[stock_code] = quote_data
        return result
    
    def get_whole_quote_stats(self) -> Dict:
        """
        获取全推数据统计信息
        
        Returns:
            统计信息字典
        """
        with QMTService._whole_quote_lock:
            total_count = len(QMTService._whole_quote_data)
            
            # 获取最新更新时间
            latest_update_time = 0
            if QMTService._whole_quote_data:
                for data in QMTService._whole_quote_data.values():
                    update_time = data.get('update_time', 0)
                    if update_time > latest_update_time:
                        latest_update_time = update_time
            
            return {
                'subscribed': QMTService._whole_quote_subscribed,
                'subscription_seq': QMTService._whole_quote_seq,
                'total_stocks': total_count,
                'latest_update_time': latest_update_time,
                'latest_update_datetime': datetime.fromtimestamp(latest_update_time).strftime('%Y-%m-%d %H:%M:%S') if latest_update_time > 0 else None
            }
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票基础信息（合约基础信息）
        参考文档: https://dict.thinktrader.net/nativeApi/xtdata.html?id=T87jC8#%E5%9F%BA%E7%A1%80%E8%A1%8C%E6%83%85%E4%BF%A1%E6%81%AF
        
        Args:
            stock_code: 股票代码（如：600519 或 600519.SH）
        
        Returns:
            股票基础信息字典，包含以下字段（根据官方文档）:
            - InstrumentID: 合约代码
            - InstrumentName: 合约名称
            - ExchangeID: 合约市场代码
            - OpenDate: IPO日期
            - ExpireDate: 退市日或到期日
            - PreClose: 前收盘价格
            - UpStopPrice: 当日涨停价
            - DownStopPrice: 当日跌停价
            - FloatVolume: 流通股本
            - TotalVolume: 总股本
            - PriceTick: 最小变价单位
            - IsTrading: 合约是否可交易
            - 以及其他合约信息字段
        """
        if not self.xtdata_module:
            self.logger.warning("xtdata模块未加载，无法获取股票信息")
            return None
        
        try:
            # 格式化股票代码
            full_code = self._format_stock_code(stock_code)
            
            # 获取合约基础信息
            instrument_detail = self.xtdata_module.get_instrument_detail(full_code)
            
            if not instrument_detail:
                self.logger.debug(f"未获取到股票 {full_code} 的基础信息")
                return None
            
            # 返回完整的基础信息
            return instrument_detail.copy()
            
        except Exception as e:
            self.logger.error(f"获取股票基础信息失败 {stock_code}: {e}")
            return None
    
    def get_stocks_info(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """
        批量获取多个股票的基础信息
        
        Args:
            stock_codes: 股票代码列表
        
        Returns:
            {stock_code: {基础信息}} 字典，未找到的股票不会包含在结果中
        """
        result = {}
        for stock_code in stock_codes:
            info = self.get_stock_info(stock_code)
            if info:
                result[stock_code] = info
        return result
    
    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票基础信息（简化版，只返回常用字段）
        
        Args:
            stock_code: 股票代码（如：600519 或 600519.SH）
        
        Returns:
            包含常用基础信息的字典:
            - stock_code: 股票代码（带市场后缀）
            - stock_name: 股票名称
            - exchange: 交易所代码
            - ipo_date: IPO日期
            - expire_date: 退市日期
            - pre_close: 前收盘价
            - up_stop_price: 涨停价
            - down_stop_price: 跌停价
            - float_volume: 流通股本
            - total_volume: 总股本
            - price_tick: 最小变价单位
            - is_trading: 是否可交易
        """
        full_info = self.get_stock_info(stock_code)
        if not full_info:
            return None
        
        # 提取常用字段
        return {
            'stock_code': self._format_stock_code(stock_code),
            'stock_name': full_info.get('InstrumentName', ''),
            'exchange': full_info.get('ExchangeID', ''),
            'ipo_date': full_info.get('OpenDate', ''),
            'expire_date': full_info.get('ExpireDate', ''),
            'pre_close': full_info.get('PreClose', 0),
            'up_stop_price': full_info.get('UpStopPrice', 0),
            'down_stop_price': full_info.get('DownStopPrice', 0),
            'float_volume': full_info.get('FloatVolume', 0),
            'total_volume': full_info.get('TotalVolume', 0),
            'price_tick': full_info.get('PriceTick', 0),
            'is_trading': full_info.get('IsTrading', False),
            # 保留原始完整信息
            'full_info': full_info
        }
    
    def get_financial_data(self, stock_code: str, report_type: str = 'Income', 
                          start_date: str = '', end_date: str = '') -> Optional[Dict]:
        """
        获取财务数据
        参考文档: https://dict.thinktrader.net/nativeApi/xtdata.html?id=T87jC8#%E8%B4%A2%E5%8A%A1%E6%95%B0%E6%8D%AE%E6%8E%A5%E5%8F%A3
        财务数据字段列表: https://dict.thinktrader.net/nativeApi/xtdata.html?id=T87jC8#%E8%B4%A2%E5%8A%A1%E6%95%B0%E6%8D%AE%E5%AD%97%E6%AE%B5%E5%88%97%E8%A1%A8
        
        Args:
            stock_code: 股票代码（如：600519 或 600519.SH）
            report_type: 报表类型，可选值：
                - 'Balance': 资产负债表
                  主要字段: totalAssets(资产总计), totalLiab(负债合计), totalEquity(股东权益合计),
                           currentAssets(流动资产合计), nonCurrentAssets(非流动资产合计),
                           currentLiab(流动负债合计), nonCurrentLiab(非流动负债合计) 等
                
                - 'Income': 利润表
                  主要字段: revenue(营业收入), totalOperCost(营业总成本), operProfit(营业利润),
                           totProfit(利润总额), netProfit(净利润), netProfitExclMinIntInc(归母净利润),
                           revenueInc(营业收入), totalExpense(营业成本), saleExpense(销售费用),
                           financialExpense(财务费用), lessGerlAdminExp(管理费用) 等
                
                - 'CashFlow': 现金流量表
                  主要字段: netCashFlowOper(经营活动产生的现金流量净额),
                           netCashFlowInv(投资活动产生的现金流量净额),
                           netCashFlowFin(筹资活动产生的现金流量净额),
                           netCashFlow(现金及现金等价物净增加额) 等
                
                - 'PershareIndex': 主要指标
                  主要字段: eps(每股收益), bps(每股净资产), roe(净资产收益率),
                           roa(总资产收益率), grossProfitRate(销售毛利率),
                           netProfitRate(销售净利率) 等
                
                - 'Capital': 股本表
                  主要字段: totalShare(总股本), floatShare(流通股本), restrictedShare(限售股本) 等
                
                - 'Top10holder': 十大股东
                  主要字段: holderName(股东名称), holdRatio(持股比例), holdAmount(持股数量) 等
                
                - 'Top10flowholder': 十大流通股东
                  主要字段: holderName(股东名称), holdRatio(持股比例), holdAmount(持股数量) 等
                
                - 'Holdernum': 股东数
                  主要字段: shareholder(股东总数), shareholderA(A股东户数), shareholderB(B股东户数),
                           shareholderH(H股东户数), shareholderFloat(已流通股东户数) 等
            
            start_date: 开始日期（格式：'20240101'），空字符串表示不限制
            end_date: 结束日期（格式：'20241231'），空字符串表示不限制
        
        Returns:
            财务数据字典，格式为 {报表类型: {报告期: {字段: 值}}}
            例如: {'Income': {'20231231': {'revenue': 1000, 'netProfit': 500, ...}, ...}}
            
            注意: 字段名称使用QMT官方字段名（英文），具体字段列表请参考官方文档
        """
        if not self.xtdata_module:
            self.logger.warning("xtdata模块未加载，无法获取财务数据")
            return None
        
        try:
            # 格式化股票代码
            full_code = self._format_stock_code(stock_code)
            
            # 获取财务数据
            # QMT的get_financial_data返回格式: {报表类型: {报告期: {字段: 值}}}
            financial_data = self.xtdata_module.get_financial_data(
                stock_code=full_code,
                table_list=[report_type],
                start_time=start_date,
                end_time=end_date
            )
            
            if not financial_data:
                self.logger.debug(f"未获取到股票 {full_code} 的财务数据（类型: {report_type}）")
                return None
            
            # 返回财务数据（QMT返回的格式）
            return financial_data
            
        except Exception as e:
            self.logger.error(f"获取财务数据失败 {stock_code} (类型: {report_type}): {e}")
            return None
    
    def download_financial_data(self, stock_code: str, report_type: str = 'Income',
                               start_date: str = '', end_date: str = '') -> bool:
        """
        下载财务数据到本地
        参考文档: https://dict.thinktrader.net/nativeApi/xtdata.html?id=T87jC8#%E8%B4%A2%E5%8A%A1%E6%95%B0%E6%8D%AE%E6%8E%A5%E5%8F%A3
        
        下载后的数据会保存到本地，后续调用get_financial_data时会优先从本地读取
        
        Args:
            stock_code: 股票代码（如：600519 或 600519.SH）
            report_type: 报表类型，可选值：
                - 'Balance': 资产负债表
                - 'Income': 利润表
                - 'CashFlow': 现金流量表
                - 'PershareIndex': 主要指标
                - 'Capital': 股本表
                - 'Top10holder': 十大股东
                - 'Top10flowholder': 十大流通股东
                - 'Holdernum': 股东数
            start_date: 开始日期（格式：'20240101'），空字符串表示不限制
            end_date: 结束日期（格式：'20241231'），空字符串表示不限制
        
        Returns:
            bool: 下载是否成功
        """
        if not self.xtdata_module:
            self.logger.warning("xtdata模块未加载，无法下载财务数据")
            return False
        
        try:
            # 格式化股票代码
            full_code = self._format_stock_code(stock_code)
            
            # 下载财务数据
            result = self.xtdata_module.download_financial_data(
                stock_code=full_code,
                table_list=[report_type],
                start_time=start_date,
                end_time=end_date
            )
            
            if result:
                self.logger.info(f"财务数据下载成功: {full_code} (类型: {report_type})")
                return True
            else:
                self.logger.warning(f"财务数据下载失败: {full_code} (类型: {report_type})")
                return False
                
        except Exception as e:
            self.logger.error(f"下载财务数据失败 {stock_code} (类型: {report_type}): {e}")
            return False
    
    def get_financial_data_simple(self, stock_code: str, report_type: str = 'income') -> Optional[Dict]:
        """
        获取财务数据（简化版，兼容data_source_manager的接口）
        
        Args:
            stock_code: 股票代码
            report_type: 报表类型（'income'利润表, 'balance'资产负债表, 'cashflow'现金流量表）
        
        Returns:
            财务数据字典，如果失败返回None
        """
        # 映射报表类型到QMT格式
        type_mapping = {
            'income': 'Income',
            'balance': 'Balance',
            'cashflow': 'CashFlow'
        }
        
        qmt_report_type = type_mapping.get(report_type.lower(), 'Income')
        
        return self.get_financial_data(stock_code, qmt_report_type)
    
    @staticmethod
    def get_financial_fields_info(report_type: str) -> Dict[str, List[str]]:
        """
        获取财务数据字段信息说明
        
        参考文档: https://dict.thinktrader.net/nativeApi/xtdata.html?id=T87jC8#%E8%B4%A2%E5%8A%A1%E6%95%B0%E6%8D%AE%E5%AD%97%E6%AE%B5%E5%88%97%E8%A1%A8
        
        Args:
            report_type: 报表类型
        
        Returns:
            字段信息字典，包含字段名称列表和说明
        """
        fields_info = {
            'Balance': {
                'description': '资产负债表',
                'main_fields': [
                    'totalAssets - 资产总计',
                    'totalLiab - 负债合计',
                    'totalEquity - 股东权益合计',
                    'currentAssets - 流动资产合计',
                    'nonCurrentAssets - 非流动资产合计',
                    'currentLiab - 流动负债合计',
                    'nonCurrentLiab - 非流动负债合计',
                    'monetaryFunds - 货币资金',
                    'accountsReceivable - 应收账款',
                    'inventory - 存货',
                    'fixedAssets - 固定资产',
                    'intangibleAssets - 无形资产'
                ]
            },
            'Income': {
                'description': '利润表',
                'main_fields': [
                    'revenue - 营业收入',
                    'revenueInc - 营业收入（明细）',
                    'totalOperCost - 营业总成本',
                    'totalExpense - 营业成本',
                    'operProfit - 营业利润',
                    'totProfit - 利润总额',
                    'netProfit - 净利润',
                    'netProfitExclMinIntInc - 归母净利润',
                    'saleExpense - 销售费用',
                    'financialExpense - 财务费用',
                    'lessGerlAdminExp - 管理费用',
                    'incTax - 所得税',
                    'grossProfit - 毛利润'
                ]
            },
            'CashFlow': {
                'description': '现金流量表',
                'main_fields': [
                    'netCashFlowOper - 经营活动产生的现金流量净额',
                    'netCashFlowInv - 投资活动产生的现金流量净额',
                    'netCashFlowFin - 筹资活动产生的现金流量净额',
                    'netCashFlow - 现金及现金等价物净增加额',
                    'cashFlowOper - 经营活动产生的现金流量',
                    'cashFlowInv - 投资活动产生的现金流量',
                    'cashFlowFin - 筹资活动产生的现金流量'
                ]
            },
            'PershareIndex': {
                'description': '主要指标',
                'main_fields': [
                    'eps - 每股收益',
                    'bps - 每股净资产',
                    'roe - 净资产收益率',
                    'roa - 总资产收益率',
                    'grossProfitRate - 销售毛利率',
                    'netProfitRate - 销售净利率',
                    'debtToAssetRatio - 资产负债率',
                    'currentRatio - 流动比率',
                    'quickRatio - 速动比率'
                ]
            },
            'Capital': {
                'description': '股本表',
                'main_fields': [
                    'totalShare - 总股本',
                    'floatShare - 流通股本',
                    'restrictedShare - 限售股本',
                    'changeReason - 变动原因'
                ]
            },
            'Top10holder': {
                'description': '十大股东',
                'main_fields': [
                    'holderName - 股东名称',
                    'holdRatio - 持股比例',
                    'holdAmount - 持股数量',
                    'holdChange - 持股变化'
                ]
            },
            'Top10flowholder': {
                'description': '十大流通股东',
                'main_fields': [
                    'holderName - 股东名称',
                    'holdRatio - 持股比例',
                    'holdAmount - 持股数量',
                    'holdChange - 持股变化'
                ]
            },
            'Holdernum': {
                'description': '股东数',
                'main_fields': [
                    'shareholder - 股东总数',
                    'shareholderA - A股东户数',
                    'shareholderB - B股东户数',
                    'shareholderH - H股东户数',
                    'shareholderFloat - 已流通股东户数',
                    'shareholderOther - 未流通股东户数'
                ]
            }
        }
        
        return fields_info.get(report_type, {
            'description': '未知报表类型',
            'main_fields': []
        })
    
    # ==================== 委托查询相关方法 ====================
    # 参考文档: https://dict.thinktrader.net/nativeApi/xttrader.html?id=T87jC8#%E5%A7%94%E6%89%98%E6%9F%A5%E8%AF%A2
    
    def get_orders(self, cancelable_only: bool = False) -> List[Dict]:
        """
        查询当日所有委托
        
        参考文档: https://dict.thinktrader.net/nativeApi/xttrader.html?id=T87jC8#%E5%A7%94%E6%89%98%E6%9F%A5%E8%AF%A2
        
        XtOrder 委托结构体字段:
        - account_id: str - 资金账号
        - stock_code: str - 证券代码（如：600519.SH）
        - order_id: int - 订单编号（策略端生成）
        - order_sysid: str - 柜台合同编号（柜台生成）
        - order_time: int - 报单时间（时间戳）
        - order_type: int - 委托类型（23:买入, 24:卖出）
        - order_volume: int - 委托数量
        - price_type: int - 报价类型
        - price: float - 委托价格
        - traded_volume: int - 成交数量
        - traded_price: float - 成交均价
        - order_status: int - 委托状态（参见 OrderStatus 类）
        - status_msg: str - 委托状态描述
        - strategy_name: str - 策略名称
        - order_remark: str - 委托备注
        
        Args:
            cancelable_only: 是否只返回可撤单的委托
        
        Returns:
            委托列表，每个委托为字典格式
        """
        if not self.is_connected():
            self.logger.warning("QMT未连接，无法查询委托")
            return []
        
        try:
            # 使用 query_stock_orders 查询委托（官方接口）
            orders = QMTService._xttrader.query_stock_orders(
                QMTService._account,
                cancelable_only
            )
            
            if not orders:
                return []
            
            result = []
            for order in orders:
                # 获取股票名称
                stock_name = ''
                stock_code = getattr(order, 'stock_code', '')
                if stock_code and self.xtdata_module:
                    try:
                        instrument_detail = self.xtdata_module.get_instrument_detail(stock_code)
                        if instrument_detail:
                            stock_name = instrument_detail.get('InstrumentName', '')
                    except Exception as e:
                        self.logger.debug(f"获取{stock_code}名称失败: {e}")
                
                # 解析委托类型
                order_type_code = getattr(order, 'order_type', 0)
                order_type_name = '买入' if order_type_code == 23 else ('卖出' if order_type_code == 24 else f'未知({order_type_code})')
                
                # 解析委托状态
                order_status = getattr(order, 'order_status', 255)
                
                # 格式化委托时间
                order_time = getattr(order, 'order_time', 0)
                order_time_str = ''
                if order_time > 0:
                    try:
                        order_time_str = datetime.fromtimestamp(order_time).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        order_time_str = str(order_time)
                
                result.append({
                    'account_id': getattr(order, 'account_id', ''),
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'order_id': getattr(order, 'order_id', 0),
                    'order_sysid': getattr(order, 'order_sysid', ''),
                    'order_time': order_time,
                    'order_time_str': order_time_str,
                    'order_type': order_type_code,
                    'order_type_name': order_type_name,
                    'order_volume': getattr(order, 'order_volume', 0),
                    'price_type': getattr(order, 'price_type', 0),
                    'price': getattr(order, 'price', 0),
                    'traded_volume': getattr(order, 'traded_volume', 0),
                    'traded_price': getattr(order, 'traded_price', 0),
                    'order_status': order_status,
                    'order_status_name': OrderStatus.get_name(order_status),
                    'is_final': OrderStatus.is_final(order_status),
                    'is_success': OrderStatus.is_success(order_status),
                    'status_msg': getattr(order, 'status_msg', ''),
                    'strategy_name': getattr(order, 'strategy_name', ''),
                    'order_remark': getattr(order, 'order_remark', '')
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"查询委托失败: {e}")
            return []
    
    def get_cancelable_orders(self) -> List[Dict]:
        """
        查询当日可撤委托
        
        Returns:
            可撤委托列表
        """
        return self.get_orders(cancelable_only=True)
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """
        根据订单编号查询委托
        
        Args:
            order_id: 订单编号（策略端生成的 order_id）
        
        Returns:
            委托信息字典，如果未找到返回 None
        """
        orders = self.get_orders()
        for order in orders:
            if order.get('order_id') == order_id:
                return order
        return None
    
    def get_order_by_sysid(self, order_sysid: str) -> Optional[Dict]:
        """
        根据柜台合同编号查询委托
        
        Args:
            order_sysid: 柜台合同编号
        
        Returns:
            委托信息字典，如果未找到返回 None
        """
        orders = self.get_orders()
        for order in orders:
            if order.get('order_sysid') == order_sysid:
                return order
        return None
    
    def get_orders_by_stock(self, stock_code: str) -> List[Dict]:
        """
        查询指定股票的所有委托
        
        Args:
            stock_code: 股票代码（如：600519 或 600519.SH）
        
        Returns:
            该股票的委托列表
        """
        full_code = self._format_stock_code(stock_code)
        orders = self.get_orders()
        
        result = []
        for order in orders:
            order_stock_code = order.get('stock_code', '')
            # 匹配完整代码或原始代码
            if order_stock_code == full_code or order_stock_code == stock_code:
                result.append(order)
        
        return result
    
    def get_orders_by_status(self, status: int) -> List[Dict]:
        """
        查询指定状态的委托
        
        Args:
            status: 委托状态码（参见 OrderStatus 类）
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
        orders = self.get_orders()
        return [order for order in orders if order.get('order_status') == status]
    
    def get_pending_orders(self) -> List[Dict]:
        """
        查询未完成的委托（非最终状态）
        
        Returns:
            未完成的委托列表
        """
        orders = self.get_orders()
        return [order for order in orders if not order.get('is_final', False)]
    
    def get_completed_orders(self) -> List[Dict]:
        """
        查询已完成的委托（最终状态）
        
        Returns:
            已完成的委托列表
        """
        orders = self.get_orders()
        return [order for order in orders if order.get('is_final', False)]
    
    def get_successful_orders(self) -> List[Dict]:
        """
        查询成交成功的委托
        
        Returns:
            成交成功的委托列表
        """
        return self.get_orders_by_status(OrderStatus.SUCCEEDED)
    
    def get_canceled_orders(self) -> List[Dict]:
        """
        查询已撤销的委托
        
        Returns:
            已撤销的委托列表
        """
        return self.get_orders_by_status(OrderStatus.CANCELED)
    
    def get_failed_orders(self) -> List[Dict]:
        """
        查询废单
        
        Returns:
            废单列表
        """
        return self.get_orders_by_status(OrderStatus.JUNK)
    
    def get_orders_summary(self) -> Dict:
        """
        获取委托汇总信息
        
        Returns:
            委托汇总字典，包含各状态的委托数量和统计信息
        """
        orders = self.get_orders()
        
        # 统计各状态数量
        status_counts = {}
        for order in orders:
            status = order.get('order_status', 255)
            status_name = OrderStatus.get_name(status)
            status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        # 统计买卖方向
        buy_count = sum(1 for o in orders if o.get('order_type') == 23)
        sell_count = sum(1 for o in orders if o.get('order_type') == 24)
        
        # 统计成交金额
        total_traded_amount = sum(
            o.get('traded_volume', 0) * o.get('traded_price', 0) 
            for o in orders
        )
        
        return {
            'total_count': len(orders),
            'pending_count': len([o for o in orders if not o.get('is_final', False)]),
            'completed_count': len([o for o in orders if o.get('is_final', False)]),
            'success_count': len([o for o in orders if o.get('is_success', False)]),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'total_traded_amount': total_traded_amount,
            'status_counts': status_counts,
            'cancelable_count': len(self.get_cancelable_orders())
        }
    
    def cancel_order(self, order_id: int) -> Dict:
        """
        撤销委托
        
        参考文档: https://dict.thinktrader.net/nativeApi/xttrader.html?id=T87jC8#%E6%92%A4%E5%8D%95
        
        Args:
            order_id: 订单编号（策略端生成的 order_id）
        
        Returns:
            撤单结果字典
        """
        if not self.is_connected():
            return {
                'success': False,
                'error': 'QMT未连接'
            }
        
        try:
            # 先查询订单是否存在且可撤
            order = self.get_order_by_id(order_id)
            if not order:
                return {
                    'success': False,
                    'error': f'未找到订单 {order_id}'
                }
            
            if order.get('is_final', False):
                return {
                    'success': False,
                    'error': f'订单已处于最终状态（{order.get("order_status_name")}），无法撤单'
                }
            
            # 执行撤单
            result = QMTService._xttrader.cancel_order_stock(
                QMTService._account,
                order_id
            )
            
            # cancel_order_stock 返回: 成功返回0, 失败返回-1
            if result == 0:
                self.logger.info(f"撤单请求已提交: order_id={order_id}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'message': '撤单请求已提交，请通过事件总线订阅撤单结果'
                }
            else:
                self.logger.error(f"撤单请求失败: order_id={order_id}, result={result}")
                return {
                    'success': False,
                    'error': f'撤单请求失败，返回码: {result}'
                }
                
        except Exception as e:
            self.logger.error(f"撤单失败 order_id={order_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_order_by_sysid(self, order_sysid: str) -> Dict:
        """
        根据柜台合同编号撤销委托
        
        Args:
            order_sysid: 柜台合同编号
        
        Returns:
            撤单结果字典
        """
        # 先查找对应的 order_id
        order = self.get_order_by_sysid(order_sysid)
        if not order:
            return {
                'success': False,
                'error': f'未找到柜台合同编号为 {order_sysid} 的订单'
            }
        
        return self.cancel_order(order.get('order_id'))
    
    def cancel_all_orders(self) -> Dict:
        """
        撤销所有可撤委托
        
        Returns:
            批量撤单结果字典
        """
        cancelable_orders = self.get_cancelable_orders()
        
        if not cancelable_orders:
            return {
                'success': True,
                'message': '没有可撤的委托',
                'canceled_count': 0,
                'failed_count': 0,
                'results': []
            }
        
        results = []
        canceled_count = 0
        failed_count = 0
        
        for order in cancelable_orders:
            order_id = order.get('order_id')
            result = self.cancel_order(order_id)
            results.append({
                'order_id': order_id,
                'stock_code': order.get('stock_code'),
                **result
            })
            
            if result.get('success'):
                canceled_count += 1
            else:
                failed_count += 1
        
        return {
            'success': failed_count == 0,
            'message': f'撤单完成: 成功 {canceled_count} 笔, 失败 {failed_count} 笔',
            'canceled_count': canceled_count,
            'failed_count': failed_count,
            'results': results
        }
    
    def cancel_orders_by_stock(self, stock_code: str) -> Dict:
        """
        撤销指定股票的所有可撤委托
        
        Args:
            stock_code: 股票代码
        
        Returns:
            批量撤单结果字典
        """
        full_code = self._format_stock_code(stock_code)
        cancelable_orders = self.get_cancelable_orders()
        
        # 筛选指定股票的委托
        target_orders = [
            o for o in cancelable_orders 
            if o.get('stock_code') == full_code or o.get('stock_code') == stock_code
        ]
        
        if not target_orders:
            return {
                'success': True,
                'message': f'股票 {stock_code} 没有可撤的委托',
                'canceled_count': 0,
                'failed_count': 0,
                'results': []
            }
        
        results = []
        canceled_count = 0
        failed_count = 0
        
        for order in target_orders:
            order_id = order.get('order_id')
            result = self.cancel_order(order_id)
            results.append({
                'order_id': order_id,
                'stock_code': order.get('stock_code'),
                **result
            })
            
            if result.get('success'):
                canceled_count += 1
            else:
                failed_count += 1
        
        return {
            'success': failed_count == 0,
            'message': f'股票 {stock_code} 撤单完成: 成功 {canceled_count} 笔, 失败 {failed_count} 笔',
            'canceled_count': canceled_count,
            'failed_count': failed_count,
            'results': results
        }


# 全局QMT服务实例
qmt_service = QMTService()
