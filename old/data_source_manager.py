"""
数据源管理器
实现akshare和tushare的自动切换机制
"""

import os
import pandas as pd
from datetime import datetime, timedelta





class DataSourceManager:
    """数据源管理器 - 实现mysql、akshare和tushare自动切换"""
    
    def __init__(self):
        self.tushare_token = os.getenv('TUSHARE_TOKEN', '')
        self.tushare_available = False
        self.tushare_api = None
        self.mysql_enabled = os.getenv('MYSQL_ENABLED', 'false').lower() == 'true'
        self.mysql_available = False
        self.mysql_config = {
            'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'choose_stock'),
            'stock_table': os.getenv('MYSQL_STOCK_TABLE', 'stock_history'),
        }
        self._pymysql = None
        
        if self.mysql_enabled:
            self._init_mysql()
            return None
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
            print("ℹ️ 未配置Tushare Token，将仅使用Akshare数据源")

        
    
    def get_stock_hist_data(self, symbol, start_date=None, end_date=None, adjust='qfq'):
        """
        获取股票历史数据（优先mysql，失败时使用akshare，再失败时使用tushare）
        
        Args:
            symbol: 股票代码（6位数字）
            start_date: 开始日期（格式：'20240101'或'2024-01-01'）
            end_date: 结束日期
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
        
        mysql_start_date = self._format_date_for_mysql(start_date)
        mysql_end_date = self._format_date_for_mysql(end_date)

        # 优先使用MySQL
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
                ts_code = self._convert_to_ts_code(symbol)
                
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
        获取股票基本信息（优先akshare，失败时使用tushare）
        
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
        
        # 优先使用akshare
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
                
                ts_code = self._convert_to_ts_code(symbol)
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
        获取实时行情数据（优先akshare，失败时使用tushare）
        
        Args:
            symbol: 股票代码
            
        Returns:
            dict: 实时行情数据
        """
        quotes = {}
        
        # 优先使用akshare
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
                
                ts_code = self._convert_to_ts_code(symbol)
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
        获取财务数据（优先akshare，失败时使用tushare）
        
        Args:
            symbol: 股票代码
            report_type: 报表类型（'income'利润表, 'balance'资产负债表, 'cashflow'现金流量表）
            
        Returns:
            DataFrame: 财务数据
        """
        # 优先使用akshare
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
                
                ts_code = self._convert_to_ts_code(symbol)
                
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
    
    def _convert_to_ts_code(self, symbol):
        """
        将6位股票代码转换为tushare格式（带市场后缀）
        
        Args:
            symbol: 6位股票代码
            
        Returns:
            str: tushare格式代码（如：000001.SZ）
        """
        if not symbol or len(symbol) != 6:
            return symbol
        
        # 根据代码判断市场
        if symbol.startswith('6'):
            # 上海主板
            return f"{symbol}.SH"
        elif symbol.startswith('0') or symbol.startswith('3'):
            # 深圳主板和创业板
            return f"{symbol}.SZ"
        elif symbol.startswith('8') or symbol.startswith('4'):
            # 北交所
            return f"{symbol}.BJ"
        else:
            # 默认深圳
            return f"{symbol}.SZ"
    
    def _convert_from_ts_code(self, ts_code):
        """
        将tushare格式代码转换为6位代码
        
        Args:
            ts_code: tushare格式代码（如：000001.SZ）
            
        Returns:
            str: 6位股票代码
        """
        if '.' in ts_code:
            return ts_code.split('.')[0]
        return ts_code

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
            df['date'] = pd.to_datetime(df['date'])
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


# 全局数据源管理器实例
data_source_manager = DataSourceManager()

