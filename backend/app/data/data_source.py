"""
数据源管理器
实现QMT、akshare和tushare的自动切换机制
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from app.utils.stock_code import add_market_suffix,remove_market_suffix





class DataSourceManager:
    """数据源管理器 - 实现QMT、mysql、akshare和tushare自动切换
    
    数据源优先级：
    1. 实时行情：QMT > Akshare > Tushare
    2. 历史数据：MySQL > Akshare > Tushare
    3. 基本信息：Akshare > Tushare
    4. 财务数据：Akshare > Tushare
    """
    
    def __init__(self, config: dict = None):
        """
        初始化数据源管理器
        
        Args:
            config: 配置字典，如果为None则从环境变量读取（兼容旧逻辑）
        """
        # 如果传入配置字典，优先使用配置字典
        if config is not None:
            self.tushare_token = config.get('TUSHARE_TOKEN', '')
            self.mysql_enabled = config.get('MYSQL_ENABLED', 'false').lower() == 'true'
            self.mysql_config = {
                'host': config.get('MYSQL_HOST', '127.0.0.1'),
                'port': int(config.get('MYSQL_PORT', '3306')),
                'user': config.get('MYSQL_USER', 'root'),
                'password': config.get('MYSQL_PASSWORD', ''),
                'database': config.get('MYSQL_DATABASE', 'choose_stock'),
                'stock_table': config.get('MYSQL_STOCK_TABLE', 'stock_history'),
            }
        else:
            # 兼容旧逻辑：从环境变量读取
            self.tushare_token = os.getenv('TUSHARE_TOKEN', '')
            self.mysql_enabled = os.getenv('MYSQL_ENABLED', 'false').lower() == 'true'
            self.mysql_config = {
                'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
                'port': int(os.getenv('MYSQL_PORT', '3306')),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'database': os.getenv('MYSQL_DATABASE', 'choose_stock'),
                'stock_table': os.getenv('MYSQL_STOCK_TABLE', 'stock_history'),
            }
        
        self.tushare_available = False
        self.tushare_api = None
        self.mysql_available = False
        self._pymysql = None
        
        if self.mysql_enabled:
            self._init_mysql()
        else:
            print("ℹ️ 未启用MySQL数据源")
            self.mysql_available = False
        
        # 初始化tushare
        if self.tushare_token:
            try:
                import tushare as ts
                ts.set_token(self.tushare_token)
                self.tushare_api = ts.pro_api()
                self.tushare_available = True
                print("✅ Tushare数据源初始化成功")
            except Exception as e:
                print(f"⚠️ Tushare数据源初始化失败: {e}")
                self.tushare_available = False
        else:
            print("ℹ️ 未配置Tushare Token,将仅使用Akshare数据源")

        
    
    def get_stock_hist_data(self, symbol,period:str ='1d', start_date=None, end_date=None,count:int = 0,adjust='qfq'):
        """
        获取股票历史数据（优先QMT，其次MySQL，本地失败后再降级 akshare -> tushare）
        
        Args:
            symbol: 股票代码（6位数字）
            period: 时间粒度
            start_date: 开始日期（格式：'20240101'或'2024-01-01'）
            end_date: 结束日期
            count: 查询数量
            adjust: 复权类型（'qfq'前复权, 'hfq'后复权, ''不复权）
            
        Returns:
            DataFrame: 包含日期、开盘、收盘、最高、最低、成交量等列
        """
        # 标准化日期格式
        if start_date:
            start_date = start_date.replace('-', '')
        if end_date:
            end_date = end_date.replace('-', '')
        else:
            end_date = datetime.now().strftime('%Y%m%d')
        
       
        # 1) 优先使用QMT行情（xtdata）
        try:
            from app.services.qmt_service import qmt_service
            import pandas as pd

            if qmt_service.xtdata_module:
                xt_code = add_market_suffix(symbol)
                print(f"[QMT] 正在获取 {symbol} 的历史数据（{xt_code}）...")

                # 确保已连接
                try:
                    qmt_service.xtdata_module.connect()
                except Exception:
                    pass

                def _fetch_xt_data():
                    # 先下载数据
                    qmt_service.xtdata_module.download_history_data(
                        stock_code=xt_code,
                        period = period,
                        start_time=start_date or '',
                        end_time=end_date or '',
                        incrementally=True
                    )
                    
                    return qmt_service.xtdata_module.get_market_data_ex(
                        field_list=["time", "open", "high", "low", "close", "volume", "amount"],
                        stock_list=[xt_code],
                        period=period,
                        start_time=start_date or '',
                        end_time=end_date or '',
                        dividend_type='none'
                    )

                data = _fetch_xt_data()

                # 若未取到数据，尝试先下载再取
                if data ==None:
                    print(f"[QMT] ⚠️ 未取到数据")
                    return data


                if data:
                    df = data[xt_code].copy()
                    # xtdata 返回字段包含 time/open/high/low/close/volume/amount
                    # 转换时间字段，指定中国时区
                    if 'time' in df.columns:
                        try:
                            # 转换为datetime并指定中国时区
                            df['date'] = pd.to_datetime(df['time'].astype(str), utc=False).dt.tz_localize('Asia/Shanghai')
                        except Exception:
                            try:
                                # 如果时区处理失败，尝试不带时区的转换
                                df['date'] = pd.to_datetime(df['time'].astype(str))
                            except Exception:
                                df['date'] = df['time']
                    else:
                        df['date'] = pd.NaT

                    df = df.rename(columns={
                        'open': 'open',
                        'high': 'high',
                        'low': 'low',
                        'close': 'close',
                        'volume': 'volume',
                        'amount': 'amount'
                    })

                    # 保留所需列并排序
                    keep_cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
                    df = df[keep_cols]
                    df = df.sort_values('date')

                    print(f"[QMT] ✅ 成功获取 {len(df)} 条数据")
                    return df
        except ImportError:
            print("[QMT] ⚠️ QMT服务未安装，跳过")
        except Exception as e:
            print(f"[QMT] ❌ 获取失败: {e}")
            import traceback
            traceback.print_exc()

        # 使用MySQL
        mysql_start_date = self._format_date_for_mysql(start_date)
        mysql_end_date = self._format_date_for_mysql(end_date)
        mysql_df = self._fetch_stock_hist_from_mysql(symbol, mysql_start_date, mysql_end_date)
        if mysql_df is not None:
            return mysql_df

        # MySQL不可用时优先使用akshare
        try:
            import akshare as ak
            print(f"[Akshare] 正在获取 {symbol} 的历史数据...")
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            if df is not None and not df.empty:
                # 标准化列名
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_change',
                    '涨跌额': 'change',
                    '换手率': 'turnover'
                })
                df['date'] = pd.to_datetime(df['date'])
                
                print(f"[Akshare] ✅ 成功获取 {len(df)} 条数据")
                print(df)
                return df
        except Exception as e:
            print(f"[Akshare] ❌ 获取失败: {e}")
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的历史数据（备用数据源）...")
                
                # 转换股票代码格式（添加市场后缀）
                ts_code = add_market_suffix(symbol)
                
                # 转换复权类型
                adj_dict = {'qfq': 'qfq', 'hfq': 'hfq', '': None}
                adj = adj_dict.get(adjust, 'qfq')
                
                # 格式化日期
                start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}" if start_date else None
                end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}" if end_date else None
                
                # 获取数据
                df = self.tushare_api.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    adj=adj
                )
                
                if df is not None and not df.empty:
                    # 标准化列名和数据格式
                    df = df.rename(columns={
                        'trade_date': 'date',
                        'vol': 'volume',
                        'amount': 'amount'
                    })
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    
                    # 转换成交量单位（tushare单位是手，转换为股）
                    df['volume'] = df['volume'] * 100
                    # 转换成交额单位（tushare单位是千元，转换为元）
                    df['amount'] = df['amount'] * 1000
                    
                    print(f"[Tushare] ✅ 成功获取 {len(df)} 条数据")
                    return df
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        # 两个数据源都失败
        print("❌ 所有数据源均获取失败")
        return None
    
    def get_stock_basic_info(self, symbol):
        """
        获取股票基本信息（优先QMT，失败时使用akshare，再失败时使用tushare）
        
        Args:
            symbol: 股票代码
            
        Returns:
            dict: 股票基本信息
        """
        info = {
            "symbol": symbol,
            "name": "未知",
            "industry": "未知",
            "market": "未知"
        }
        
        # 优先使用QMT服务（如果可用）
        try:
            from app.services.qmt_service import qmt_service
            
            if qmt_service.xtdata_module:
                print(f"[QMT] 正在获取 {symbol} 的基本信息...")
                
                # 使用QMT获取股票基础信息
                qmt_info = qmt_service.get_stock_basic_info(symbol)
                
                if qmt_info:
                    # 映射QMT数据到标准格式
                    info['name'] = qmt_info.get('stock_name', '未知')
                    info['market'] = qmt_info.get('exchange', '未知')
                    info['list_date'] = qmt_info.get('ipo_date', '')
                    info['pre_close'] = qmt_info.get('pre_close', 0)
                    info['up_stop_price'] = qmt_info.get('up_stop_price', 0)
                    info['down_stop_price'] = qmt_info.get('down_stop_price', 0)
                    info['float_volume'] = qmt_info.get('float_volume', 0)
                    info['total_volume'] = qmt_info.get('total_volume', 0)
                    info['price_tick'] = qmt_info.get('price_tick', 0)
                    info['is_trading'] = qmt_info.get('is_trading', False)
                    
                    # 如果有完整信息，尝试提取行业信息
                    full_info = qmt_info.get('full_info', {})
                    if full_info:
                        # QMT可能不包含行业信息，保留默认值
                        pass
                    
                    print(f"[QMT] ✅ 成功获取基本信息: {info.get('name', symbol)}")
                    return info
                else:
                    print(f"[QMT] ⚠️ 未找到 {symbol} 的基本信息")
        except ImportError:
            print(f"[QMT] ⚠️ QMT服务未安装，跳过")
        except Exception as e:
            print(f"[QMT] ❌ 获取失败: {e}")
            import traceback
            traceback.print_exc()
        
        # QMT失败或不可用，使用akshare
        try:
            import akshare as ak
            print(f"[Akshare] 正在获取 {symbol} 的基本信息...")
            
            stock_info = ak.stock_individual_info_em(symbol=symbol)
            print(stock_info)
            if stock_info is not None and not stock_info.empty:
                for _, row in stock_info.iterrows():
                    key = row['item']
                    value = row['value']
                    
                    if key == '股票简称':
                        info['name'] = value
                    elif key == '所处行业':
                        info['industry'] = value
                    elif key == '上市时间':
                        info['list_date'] = value
                    elif key == '总市值':
                        info['market_cap'] = value
                    elif key == '流通市值':
                        info['circulating_market_cap'] = value
                
                print(f"[Akshare] ✅ 成功获取基本信息")
                return info
        except Exception as e:
            print(f"[Akshare] ❌ 获取失败: {e}")
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的基本信息（备用数据源）...")
                
                ts_code = add_market_suffix(symbol)
                df = self.tushare_api.stock_basic(
                    ts_code=ts_code,
                    fields='ts_code,name,area,industry,market,list_date'
                )
                
                if df is not None and not df.empty:
                    info['name'] = df.iloc[0]['name']
                    info['industry'] = df.iloc[0]['industry']
                    info['market'] = df.iloc[0]['market']
                    info['list_date'] = df.iloc[0]['list_date']
                    
                    print(f"[Tushare] ✅ 成功获取基本信息")
                    return info
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        return info
    
    def get_realtime_quotes(self, symbol):
        """
        获取实时行情数据（优先QMT，失败时使用akshare，再失败时使用tushare）
        
        Args:
            symbol: 股票代码
            
        Returns:
            dict: 实时行情数据
        """
        quotes = {}
        
        # 优先使用QMT服务（如果可用）
        try:
            from app.services.qmt_service import qmt_service
            
            if qmt_service.is_connected():
                print(f"[QMT] 正在获取 {symbol} 的实时行情...")
                
                # 使用QMT获取实时行情（全推数据）
                quote_data = qmt_service.get_stock_quote(symbol)
                
                if quote_data:
                    # QMT全推数据实际字段格式：
                    # lastPrice, open, high, low, lastClose, amount, volume, pvolume等
                    last_price = quote_data.get('lastPrice', 0)
                    last_close = quote_data.get('lastClose') or quote_data.get('preClose') or quote_data.get('pre_close', 0)
                    
                    if last_price and last_price > 0:
                        # 转换QMT数据格式为标准格式
                        quotes = {
                            'symbol': symbol,
                            'name': quote_data.get('InstrumentName') or quote_data.get('name', ''),
                            'price': float(last_price),  # 最新价
                            'change_percent': 0,  # 稍后计算
                            'change': float(last_price) - float(last_close) if last_close else 0,  # 涨跌额
                            'volume': quote_data.get('volume', 0),  # 成交量（手）
                            'amount': quote_data.get('amount', 0),  # 成交额（元）
                            'high': quote_data.get('high', 0),  # 最高价
                            'low': quote_data.get('low', 0),  # 最低价
                            'open': quote_data.get('open', 0),  # 今开
                            'pre_close': float(last_close) if last_close else 0  # 昨收
                        }
                        
                        # 如果没有名称，尝试从instrument_detail获取
                        if not quotes['name'] and qmt_service.xtdata_module:
                            try:
                                instrument_detail = qmt_service.xtdata_module.get_instrument_detail(symbol)
                                if instrument_detail:
                                    quotes['name'] = instrument_detail.get('InstrumentName', '')
                            except:
                                pass
                        
                        # 计算涨跌幅（根据最新价和昨收）
                        if quotes.get('pre_close', 0) > 0:
                            quotes['change_percent'] = ((quotes['price'] - quotes['pre_close']) / quotes['pre_close']) * 100
                        
                        # 转换成交量单位（QMT返回的是手，转换为股）
                        if quotes.get('volume', 0) > 0:
                            quotes['volume'] = quotes['volume'] * 100
                        
                        print(f"[QMT] ✅ 成功获取实时行情: {quotes.get('name', symbol)} 价格={quotes.get('price', 0)} 涨跌幅={quotes.get('change_percent', 0):.2f}%")
                        return quotes
                    else:
                        print(f"[QMT] ⚠️ {symbol} 的价格数据无效: lastPrice={last_price}")
                else:
                    print(f"[QMT] ⚠️ 未找到 {symbol} 的实时行情数据")
        except ImportError:
            print(f"[QMT] ⚠️ QMT服务未安装，跳过")
        except Exception as e:
            print(f"[QMT] ❌ 获取失败: {e}")
            import traceback
            traceback.print_exc()
        
        # QMT失败或不可用，使用akshare
        try:
            import akshare as ak
            print(f"[Akshare] 正在获取 {symbol} 的实时行情...")
            
            df = ak.stock_zh_a_spot_em()
            print(df)
            stock_df = df[df['代码'] == symbol]
            
            if not stock_df.empty:
                row = stock_df.iloc[0]
                quotes = {
                    'symbol': symbol,
                    'name': row['名称'],
                    'price': row['最新价'],
                    'change_percent': row['涨跌幅'],
                    'change': row['涨跌额'],
                    'volume': row['成交量'],
                    'amount': row['成交额'],
                    'high': row['最高'],
                    'low': row['最低'],
                    'open': row['今开'],
                    'pre_close': row['昨收']
                }
                print(f"[Akshare] ✅ 成功获取实时行情")
                return quotes
        except Exception as e:
            print(f"[Akshare] ❌ 获取失败: {e}")
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的实时行情（备用数据源）...")
                
                ts_code = add_market_suffix(symbol)
                df = self.tushare_api.daily(
                    ts_code=ts_code,
                    start_date=datetime.now().strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                
                if df is not None and not df.empty:
                    row = df.iloc[0]
                    quotes = {
                        'symbol': symbol,
                        'price': row['close'],
                        'change_percent': row['pct_chg'],
                        'volume': row['vol'] * 100,
                        'amount': row['amount'] * 1000,
                        'high': row['high'],
                        'low': row['low'],
                        'open': row['open'],
                        'pre_close': row['pre_close']
                    }
                    print(f"[Tushare] ✅ 成功获取实时行情")
                    return quotes
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        return quotes
    
    def get_financial_data(self, symbol, report_type='income'):
        """
        获取财务数据（优先QMT，失败时使用akshare，再失败时使用tushare）
        
        Args:
            symbol: 股票代码
            report_type: 报表类型（'income'利润表, 'balance'资产负债表, 'cashflow'现金流量表）
            
        Returns:
            DataFrame: 财务数据
        """
        # 优先使用QMT服务（如果可用）
        try:
            from app.services.qmt_service import qmt_service
            import pandas as pd
            
            if qmt_service.xtdata_module:
                print(f"[QMT] 正在获取 {symbol} 的财务数据（类型: {report_type}）...")
                
                # 使用QMT获取财务数据
                qmt_financial = qmt_service.get_financial_data_simple(symbol, report_type)
                
                if qmt_financial:
                    # 将QMT返回的字典格式转换为DataFrame
                    # QMT返回格式: {报表类型: {报告期: {字段: 值}}}
                    # 例如: {'Income': {'20231231': {'revenue': 1000, ...}, ...}}
                    try:
                        if isinstance(qmt_financial, dict):
                            # 查找对应的报表类型
                            report_type_mapping = {
                                'income': 'Income',
                                'balance': 'Balance',
                                'cashflow': 'CashFlow'
                            }
                            qmt_report_type = report_type_mapping.get(report_type.lower(), 'Income')
                            
                            # 尝试从字典中提取对应报表类型的数据
                            if qmt_report_type in qmt_financial:
                                data = qmt_financial[qmt_report_type]
                                if isinstance(data, dict):
                                    # 转换为DataFrame，每行是一个报告期
                                    df = pd.DataFrame.from_dict(data, orient='index')
                                    df.index.name = '报告期'
                                    df = df.reset_index()
                                    print(f"[QMT] ✅ 成功获取财务数据: {len(df)} 条记录")
                                    return df
                            
                            # 如果没有找到对应报表类型，尝试查找第一个可用的报表类型
                            for key in qmt_financial.keys():
                                if isinstance(qmt_financial[key], dict):
                                    data = qmt_financial[key]
                                    df = pd.DataFrame.from_dict(data, orient='index')
                                    df.index.name = '报告期'
                                    df = df.reset_index()
                                    print(f"[QMT] ✅ 成功获取财务数据: {len(df)} 条记录")
                                    return df
                            
                            # 如果字典结构不同，尝试直接转换
                            # 可能是 {报告期: {字段: 值}} 格式
                            if all(isinstance(v, dict) for v in qmt_financial.values()):
                                df = pd.DataFrame.from_dict(qmt_financial, orient='index')
                                df.index.name = '报告期'
                                df = df.reset_index()
                                print(f"[QMT] ✅ 成功获取财务数据: {len(df)} 条记录")
                                return df
                                
                        elif isinstance(qmt_financial, pd.DataFrame):
                            # 如果已经是DataFrame，直接返回
                            print(f"[QMT] ✅ 成功获取财务数据: {len(qmt_financial)} 条记录")
                            return qmt_financial
                            
                    except Exception as e:
                        print(f"[QMT] ⚠️ 数据格式转换失败: {e}")
                        import traceback
                        traceback.print_exc()
                        # 继续尝试其他数据源
                else:
                    print(f"[QMT] ⚠️ 未找到 {symbol} 的财务数据")
        except ImportError:
            print(f"[QMT] ⚠️ QMT服务未安装，跳过")
        except Exception as e:
            print(f"[QMT] ❌ 获取失败: {e}")
            import traceback
            traceback.print_exc()
        
        # QMT失败或不可用，使用akshare
        try:
            import akshare as ak
            print(f"[Akshare] 正在获取 {symbol} 的财务数据...")
            
            if report_type == 'income':
                df = ak.stock_financial_report_sina(stock=symbol, symbol="利润表")
            elif report_type == 'balance':
                df = ak.stock_financial_report_sina(stock=symbol, symbol="资产负债表")
            elif report_type == 'cashflow':
                df = ak.stock_financial_report_sina(stock=symbol, symbol="现金流量表")
            else:
                df = None
            
            if df is not None and not df.empty:
                print(f"[Akshare] ✅ 成功获取财务数据")
                print(df)
                return df
        except Exception as e:
            print(f"[Akshare] ❌ 获取失败: {e}")
        
        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的财务数据（备用数据源）...")
                
                ts_code = add_market_suffix(symbol)
                
                if report_type == 'income':
                    df = self.tushare_api.income(ts_code=ts_code)
                elif report_type == 'balance':
                    df = self.tushare_api.balancesheet(ts_code=ts_code)
                elif report_type == 'cashflow':
                    df = self.tushare_api.cashflow(ts_code=ts_code)
                else:
                    df = None
                
                if df is not None and not df.empty:
                    print(f"[Tushare] ✅ 成功获取财务数据")
                    return df
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")
        
        return None
    
    def _init_mysql(self):
        """初始化MySQL配置"""
        if not self.mysql_enabled:
            print("ℹ️ 未启用MySQL数据源")
            return
        try:
            import pymysql
            self._pymysql = pymysql
            # 测试一次连接，确认配置可用
            conn = self._get_mysql_connection()
            if conn:
                conn.close()
                self.mysql_available = True
                print("✅ MySQL数据源初始化成功")
        except Exception as e:
            print(f"⚠️ MySQL数据源初始化失败: {e}")
            self.mysql_available = False

    def _get_mysql_connection(self):
        """创建MySQL连接"""
        if not self.mysql_enabled:
            return None
        if not self._pymysql:
            try:
                import pymysql
                self._pymysql = pymysql
            except Exception as e:
                print(f"⚠️ 无法导入pymysql模块: {e}")
                return None
        try:
            return self._pymysql.connect(
                host=self.mysql_config['host'],
                port=self.mysql_config['port'],
                user=self.mysql_config['user'],
                password=self.mysql_config['password'],
                database=self.mysql_config['database'],
                cursorclass=self._pymysql.cursors.DictCursor
            )
        except Exception as e:
            print(f"⚠️ 连接MySQL失败: {e}")
            return None

    def _fetch_stock_hist_from_mysql(self, symbol, start_date=None, end_date=None):
        """
        从MySQL行情库获取历史数据
        Args:
            symbol: 6位股票代码
            start_date: YYYY-MM-DD 格式
            end_date: YYYY-MM-DD 格式
        """
        if not self.mysql_available:
            return None
        conn = self._get_mysql_connection()
        if conn is None:
            return None
        try:
            table = self.mysql_config['stock_table']
            query = f"""
                SELECT 
                    trade_date,
                    open_price AS open,
                    close_price AS close,
                    high_price AS high,
                    low_price AS low,
                    volume,
                    amount,
                    amplitude,
                    pct_chg,
                    price_chg,
                    turnover_rate
                FROM `{table}`
                WHERE stock_code = %s
                  AND (deleted = 0 OR deleted IS NULL)
            """
            params = [symbol]
            if start_date:
                query += " AND trade_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND trade_date <= %s"
                params.append(end_date)
            query += " ORDER BY trade_date"

            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

            if not rows:
                print(f"[MySQL] ⚠️ 未找到 {symbol} 对应的数据")
                return None

            df = pd.DataFrame(rows)
            df = df.rename(columns={
                'trade_date': 'date',
                'pct_chg': 'pct_change',
                'price_chg': 'change',
                'turnover_rate': 'turnover'
            })
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize('Asia/Shanghai')
            print(f"[MySQL] ✅ 成功获取 {len(df)} 条数据")
            return df
        except Exception as e:
            print(f"[MySQL] ❌ 获取失败: {e}")
            return None
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _format_date_for_mysql(self, date_str):
        """将YYYYMMDD格式转换为YYYY-MM-DD"""
        if not date_str:
            return None
        try:
            if '-' in date_str:
                return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
            return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
        except Exception:
            return None



class _DataSourceManagerSingleton:
    """数据源管理器单例包装器"""
    _instance: DataSourceManager = None
    
    @classmethod
    def get_instance(cls, config: dict = None) -> DataSourceManager:
        """
        获取数据源管理器单例实例
        
        Args:
            config: 可选配置字典，首次创建时使用
        
        Returns:
            DataSourceManager实例
        """
        if cls._instance is None:
            cls._instance = DataSourceManager(config=config)
        return cls._instance
    
    @classmethod
    def reset(cls):
        """重置单例（仅用于测试）"""
        cls._instance = None


def init_source_manager(config: dict = None) -> DataSourceManager:
    """
    获取数据源管理器实例（单例模式）
    
    Args:
        config: 可选配置字典，仅首次创建时生效
    
    Returns:
        DataSourceManager实例
    """
    return _DataSourceManagerSingleton.get_instance(config)


# 全局单例实例（懒加载）
data_source_manager = _DataSourceManagerSingleton.get_instance()
