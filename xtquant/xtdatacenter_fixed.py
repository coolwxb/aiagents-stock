#coding:utf-8

import os as _OS_
import sys
import platform

# 检查操作系统
is_windows = platform.system() == 'Windows'
is_linux = platform.system() == 'Linux'

# 尝试导入datacenter模块，如果失败则提供替代方案
try:
    from . import datacenter as __dc
    DATACENTER_AVAILABLE = True
except ImportError:
    DATACENTER_AVAILABLE = False
    print("Warning: datacenter module not available, some features may be limited")
    
    # 创建模拟的datacenter模块
    class MockDatacenter:
        def __init__(self):
            self.init_status = -1
            
        def rpc_init(self, config_dir):
            print(f"Mock datacenter rpc_init called with config_dir: {config_dir}")
            return -1
            
        def get_local_server_port(self):
            return 58610
            
        def register_create_nparray(self, func):
            print("Mock register_create_nparray called")
            return 0
            
        def set_kline_mirror_enabled(self, markets):
            print(f"Mock set_kline_mirror_enabled called with markets: {markets}")
            
        def set_allow_optmize_address(self, addr_list):
            print(f"Mock set_allow_optmize_address called with addr_list: {addr_list}")
            
        def set_wholequote_market_list(self, market_list):
            print(f"Mock set_wholequote_market_list called with market_list: {market_list}")
            
        def set_future_realtime_mode(self, enable):
            print(f"Mock set_future_realtime_mode called with enable: {enable}")
            
        def set_init_markets(self, markets):
            print(f"Mock set_init_markets called with markets: {markets}")
            
        def set_index_mirror_enabled(self, enable):
            print(f"Mock set_index_mirror_enabled called with enable: {enable}")
            
        def set_index_mirror_markets(self, markets):
            print(f"Mock set_index_mirror_markets called with markets: {markets}")
            
        def set_kline_cutting_mode(self, mode):
            print(f"Mock set_kline_cutting_mode called with mode: {mode}")
            
        def set_quote_time_mode_v2(self, enable):
            print(f"Mock set_quote_time_mode_v2 called with enable: {enable}")
            
        def set_thousand_source_mode(self, mode):
            print(f"Mock set_thousand_source_mode called with mode: {mode}")
            
        def init(self, start_local_service=True):
            print(f"Mock datacenter init called with start_local_service: {start_local_service}")
            return 0
            
        def shutdown(self):
            print("Mock datacenter shutdown called")
            return 0
            
        def listen(self, ip='0.0.0.0', port=58610):
            print(f"Mock datacenter listen called with ip: {ip}, port: {port}")
            return port
            
        def load_config(self, config_file, section):
            print(f"Mock load_config called with config_file: {config_file}, section: {section}")
            return 0
            
        def init_client(self):
            print("Mock init_client called")
            return 0
    
    class MockIPythonApiClient:
        def __init__(self):
            pass
            
        def init(self):
            print("Mock IPythonApiClient init called")
            return 0
            
        def load_config(self, config_file, section):
            print(f"Mock IPythonApiClient load_config called with config_file: {config_file}, section: {section}")
            return 0
    
    __dc = MockDatacenter()
    __dc.IPythonApiClient = MockIPythonApiClient

__all__ = [
    'set_token',
    'set_data_home_dir',
    'init',
    'shutdown',
    'listen',
    'get_local_server_port',
    'register_create_nparray',
    'try_create_client',
    'RPCClient',
]

### config

__curdir = _OS_.path.dirname(_OS_.path.abspath(__file__))

__rpc_config_dir = _OS_.path.join(__curdir, 'config')
__rpc_config_file = _OS_.path.join(__curdir, 'xtdata.ini')

# 只有在datacenter可用时才调用rpc_init
if DATACENTER_AVAILABLE:
    __rpc_init_status = __dc.rpc_init(__rpc_config_dir)
    if __rpc_init_status < 0:
        print(f'Warning: rpc init failed, error_code:{__rpc_init_status}, configdir:{__rpc_config_dir}')
else:
    __rpc_init_status = -1
    print("Warning: Using mock datacenter, rpc_init skipped")

__config_dir = _OS_.path.join(__curdir, 'config')
__data_home_dir = 'data'

__quote_token = ''

init_complete = False

### function
get_local_server_port = __dc.get_local_server_port
register_create_nparray = __dc.register_create_nparray
RPCClient = __dc.IPythonApiClient

def try_create_client():
    '''
    尝试创建RPCClient，如果失败，会抛出异常
    '''
    if not DATACENTER_AVAILABLE:
        print("Warning: datacenter not available, using mock client")
        return MockIPythonApiClient()
        
    cl = RPCClient()
    cl.init()

    ec = cl.load_config(__rpc_config_file, 'client_xtdata')
    if ec < 0:
        raise Exception(f'load config failed, file:{__rpc_config_file}')
    return cl

def set_token(token = ''):
    '''
    设置用于登录行情服务的token，此接口应该先于init调用
    token获取地址：https://xuntou.net/#/userInfo?product=xtquant
    迅投投研服务平台 - 用户中心 - 个人设置 - 接口TOKEN
    '''
    global __quote_token
    __quote_token = token
    return

def set_data_home_dir(data_home_dir):
    '''
    设置数据存储目录，此接口应该先于init调用
    datacenter启动后，会在data_home_dir目录下建立若干目录存储数据
    如果不设置存储目录，会使用默认路径
    在datacenter作为独立行情服务的场景下，data_home_dir可以任意设置
    如果想使用现有数据，data_home_dir对应QMT的f'{安装目录}'，或对应极简模式的f'{安装目录}/userdata_mini'
    '''
    global __data_home_dir
    __data_home_dir = data_home_dir
    return

def set_config_dir(config_dir):
    '''
    设置配置文件目录，此接口应该先于init调用
    通常情况配置文件内置，不需要调用这个接口
    '''
    global __config_dir
    __config_dir = config_dir
    return

def set_kline_mirror_enabled(enable):
    '''
    设置K线全推功能是否开启，此接口应该先于init调用
    此功能默认关闭，启用后，实时K线数据将优先从K线全推获取
    此功能仅vip用户可用
    '''
    __dc.set_kline_mirror_enabled(['SH', 'SZ'] if enable else [])
    return

def set_kline_mirror_markets(markets):
    '''
    设置开启指定市场的K线全推，此接口应该先于init调用
    '''
    __dc.set_kline_mirror_enabled(markets)
    return

def set_allow_optmize_address(allow_list = []):
    '''
    设置连接池,使服务器只在连接池内优选
    '''
    __dc.set_allow_optmize_address(allow_list)
    return

def set_wholequote_market_list(market_list = []):
    '''
    设置全推市场列表，此接口应该先于init调用
    '''
    __dc.set_wholequote_market_list(market_list)
    return

def set_future_realtime_mode(enable):
    '''
    设置期货实时模式，此接口应该先于init调用
    '''
    __dc.set_future_realtime_mode(enable)
    return

def set_init_markets(markets = []):
    '''
    设置初始化市场列表，此接口应该先于init调用
    '''
    __dc.set_init_markets(markets)
    return

def set_index_mirror_enabled(enable):
    '''
    设置指数全推功能是否开启，此接口应该先于init调用
    '''
    __dc.set_index_mirror_enabled(enable)
    return

def set_index_mirror_markets(markets):
    '''
    设置开启指定市场的指数全推，此接口应该先于init调用
    '''
    __dc.set_index_mirror_markets(markets)
    return

def set_kline_cutting_mode(mode):
    '''
    设置K线切割模式，此接口应该先于init调用
    mode: 0-自然日切割，1-交易日切割
    '''
    __dc.set_kline_cutting_mode(mode)
    return

def set_quote_time_mode_v2(enable):
    '''
    设置行情时间模式v2，此接口应该先于init调用
    '''
    __dc.set_quote_time_mode_v2(enable)
    return

def set_thousand_source_mode(mode):
    '''
    设置千档行情源模式，此接口应该先于init调用
    mode: 0-关闭，1-开启
    '''
    __dc.set_thousand_source_mode(mode)
    return

def init(start_local_service = True):
    '''
    初始化datacenter
    如果start_local_service为True，会额外启动一个默认本地监听，以支持datacenter作为独立行情服务时的xtdata内置连接
    '''
    global init_complete
    
    if not DATACENTER_AVAILABLE:
        print("Warning: datacenter not available, using mock initialization")
        init_complete = True
        return 0
    
    try:
        # 初始化datacenter
        result = __dc.init(start_local_service)
        if result == 0:
            init_complete = True
            print("Datacenter initialized successfully")
        else:
            print(f"Datacenter initialization failed with code: {result}")
        return result
    except Exception as e:
        print(f"Error during datacenter initialization: {e}")
        return -1

def shutdown():
    '''
    关闭datacenter
    '''
    global init_complete
    
    if not DATACENTER_AVAILABLE:
        print("Warning: datacenter not available, mock shutdown")
        init_complete = False
        return 0
    
    try:
        result = __dc.shutdown()
        init_complete = False
        return result
    except Exception as e:
        print(f"Error during datacenter shutdown: {e}")
        return -1

def listen(ip = '0.0.0.0', port = 58610):
    '''
    启动监听服务
    '''
    if not DATACENTER_AVAILABLE:
        print(f"Warning: datacenter not available, mock listening on {ip}:{port}")
        return port
    
    try:
        return __dc.listen(ip, port)
    except Exception as e:
        print(f"Error during listen: {e}")
        return port 