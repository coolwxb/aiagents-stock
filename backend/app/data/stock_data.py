"""
股票数据获取模块
封装DataSourceManager，提供统一的股票数据获取接口
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.data.data_source import DataSourceManager, data_source_manager


class StockDataFetcher:
    """股票数据获取类 - 封装DataSourceManager"""
    
    def __init__(self, data_source_manager_instance: DataSourceManager = None):
        """
        初始化股票数据获取器
        
        Args:
            data_source_manager_instance: 数据源管理器实例，如果为None则使用全局实例
        """
        self.data_source_manager = data_source_manager_instance or data_source_manager
    
    def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票基本信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票基本信息字典
        """
        try:
            # 标准化股票代码
            stock_code = self._normalize_stock_code(stock_code)
            
            # 使用数据源管理器获取基本信息
            info = self.data_source_manager.get_stock_basic_info(stock_code)
            
            if info:
                return info
            else:
                return {"error": f"无法获取股票 {stock_code} 的基本信息"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def get_stock_data(self, stock_code: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码
            period: 时间周期 ('1m', '3m', '6m', '1y', '2y', '5y')
            
        Returns:
            股票历史数据DataFrame
        """
        try:
            # 标准化股票代码
            stock_code = self._normalize_stock_code(stock_code)
            
            # 计算日期范围
            end_date = datetime.now()
            period_days = {
                '1m': 30,
                '3m': 90,
                '6m': 180,
                '1y': 365,
                '2y': 730,
                '5y': 1825
            }
            days = period_days.get(period, 365)
            start_date = end_date - timedelta(days=days)
            
            # 使用数据源管理器获取历史数据
            df = self.data_source_manager.get_stock_hist_data(
                symbol=stock_code,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )
            
            return df
            
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return None
    
    def get_realtime_quote(self, stock_code: str) -> Dict[str, Any]:
        """
        获取实时行情
        
        Args:
            stock_code: 股票代码
            
        Returns:
            实时行情数据字典
        """
        try:
            stock_code = self._normalize_stock_code(stock_code)
            return self.data_source_manager.get_realtime_quotes(stock_code)
        except Exception as e:
            return {"error": str(e)}
    
    def get_financial_data(self, stock_code: str, report_type: str = 'income') -> Optional[pd.DataFrame]:
        """
        获取财务数据
        
        Args:
            stock_code: 股票代码
            report_type: 报表类型 ('income', 'balance', 'cashflow')
            
        Returns:
            财务数据DataFrame
        """
        try:
            stock_code = self._normalize_stock_code(stock_code)
            return self.data_source_manager.get_financial_data(stock_code, report_type)
        except Exception as e:
            print(f"获取财务数据失败: {e}")
            return None
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            df: 股票历史数据DataFrame
            
        Returns:
            添加了技术指标的DataFrame
        """
        if df is None or df.empty:
            return df
        
        try:
            df = df.copy()
            
            # 确保列名是小写
            df.columns = [col.lower() for col in df.columns]
            
            # 计算移动平均线
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma10'] = df['close'].rolling(window=10).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma60'] = df['close'].rolling(window=60).mean()
            
            # 计算RSI
            df['rsi'] = self._calculate_rsi(df['close'], 14)
            
            # 计算MACD
            df['macd'], df['macd_signal'], df['macd_hist'] = self._calculate_macd(df['close'])
            
            # 计算布林带
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
            
            # 计算KDJ
            df['k'], df['d'], df['j'] = self._calculate_kdj(df)
            
            return df
            
        except Exception as e:
            print(f"计算技术指标失败: {e}")
            return df
    
    def get_latest_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取最新的技术指标值
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            最新技术指标字典
        """
        if df is None or df.empty:
            return {}
        
        try:
            latest = df.iloc[-1]
            
            indicators = {
                'close': float(latest.get('close', 0)),
                'ma5': float(latest.get('ma5', 0)) if pd.notna(latest.get('ma5')) else None,
                'ma10': float(latest.get('ma10', 0)) if pd.notna(latest.get('ma10')) else None,
                'ma20': float(latest.get('ma20', 0)) if pd.notna(latest.get('ma20')) else None,
                'ma60': float(latest.get('ma60', 0)) if pd.notna(latest.get('ma60')) else None,
                'rsi': float(latest.get('rsi', 0)) if pd.notna(latest.get('rsi')) else None,
                'macd': float(latest.get('macd', 0)) if pd.notna(latest.get('macd')) else None,
                'macd_signal': float(latest.get('macd_signal', 0)) if pd.notna(latest.get('macd_signal')) else None,
                'macd_hist': float(latest.get('macd_hist', 0)) if pd.notna(latest.get('macd_hist')) else None,
                'bb_upper': float(latest.get('bb_upper', 0)) if pd.notna(latest.get('bb_upper')) else None,
                'bb_middle': float(latest.get('bb_middle', 0)) if pd.notna(latest.get('bb_middle')) else None,
                'bb_lower': float(latest.get('bb_lower', 0)) if pd.notna(latest.get('bb_lower')) else None,
                'k': float(latest.get('k', 0)) if pd.notna(latest.get('k')) else None,
                'd': float(latest.get('d', 0)) if pd.notna(latest.get('d')) else None,
                'j': float(latest.get('j', 0)) if pd.notna(latest.get('j')) else None,
            }
            
            return indicators
            
        except Exception as e:
            print(f"获取最新指标失败: {e}")
            return {}
    
    def get_risk_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取风险数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            风险数据字典
        """
        try:
            from app.data.risk_data_fetcher import RiskDataFetcher
            fetcher = RiskDataFetcher()
            return fetcher.get_risk_data(stock_code)
        except Exception as e:
            return {"error": str(e), "data_success": False}
    
    def _normalize_stock_code(self, stock_code: str) -> str:
        """标准化股票代码"""
        # 移除可能的市场后缀
        if '.' in stock_code:
            stock_code = stock_code.split('.')[0]
        return stock_code.strip()
    
    def _is_chinese_stock(self, stock_code: str) -> bool:
        """判断是否为中国A股"""
        code = self._normalize_stock_code(stock_code)
        return code.isdigit() and len(code) == 6
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """计算MACD指标"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2):
        """计算布林带"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def _calculate_kdj(self, df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3):
        """计算KDJ指标"""
        low_list = df['low'].rolling(window=n).min()
        high_list = df['high'].rolling(window=n).max()
        rsv = (df['close'] - low_list) / (high_list - low_list) * 100
        
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d
        
        return k, d, j


# 工厂函数
def create_stock_data_fetcher(db_session=None, config: dict = None) -> StockDataFetcher:
    """
    创建股票数据获取器实例
    
    Args:
        db_session: 数据库会话（可选，用于从数据库加载配置）
        config: 配置字典（可选）
        
    Returns:
        StockDataFetcher实例
    """
    if config:
        dsm = DataSourceManager(config=config)
    else:
        dsm = data_source_manager
    
    return StockDataFetcher(data_source_manager_instance=dsm)
