"""
测试股票代码解析功能
验证带后缀的股票代码能否正确识别
"""
import sys
sys.path.append('.')

from app.data.stock_data import StockDataFetcher

def test_chinese_stock():
    """测试中国A股代码识别"""
    service = StockDataFetcher()
    
    test_cases = [
        ('300568.SZ', True, '创业板带后缀'),
        ('600519.SH', True, '上海股票带后缀'),
        ('000001.SZ', True, '深圳股票带后缀'),
        ('300568.BJ', True, '北交所股票'),
        ('600519', True, '纯数字代码'),
        ('AAPL', False, '美股代码'),
        ('12345', False, '5位数字'),
        ('1234567', False, '7位数字'),
        ('', False, '空字符串'),
    ]
    
    print("=" * 60)
    print("测试中国A股代码识别")
    print("=" * 60)
    
    for symbol, expected, desc in test_cases:
        result = service._is_chinese_stock(symbol)
        status = "✅" if result == expected else "❌"
        print(f"{status} {desc:20} | {symbol:15} | 期望:{expected:5} | 实际:{result:5}")

def test_hk_stock():
    """测试港股代码识别"""
    service = StockDataFetcher()
    
    test_cases = [
        ('00700.HK', True, '腾讯带后缀'),
        ('700.HK', True, '腾讯短代码带后缀'),
        ('HK00700', True, '带HK前缀'),
        ('HK700', True, '短代码带HK前缀'),
        ('00700', True, '5位纯数字'),
        ('700', True, '短格式'),
        ('AAPL', False, '美股代码'),
        ('600519', False, '6位数字（A股）'),
        ('', False, '空字符串'),
    ]
    
    print("\n" + "=" * 60)
    print("测试港股代码识别")
    print("=" * 60)
    
    for symbol, expected, desc in test_cases:
        result = service._is_hk_stock(symbol)
        status = "✅" if result == expected else "❌"
        print(f"{status} {desc:20} | {symbol:15} | 期望:{expected:5} | 实际:{result:5}")

def test_normalize_hk_code():
    """测试港股代码规范化"""
    service = StockDataFetcher()
    
    test_cases = [
        ('700', '00700', '短代码'),
        ('00700', '00700', '标准代码'),
        ('HK700', '00700', 'HK前缀'),
        ('HK00700', '00700', 'HK前缀标准'),
        ('700.HK', '00700', '.HK后缀'),
        ('00700.HK', '00700', '.HK后缀标准'),
    ]
    
    print("\n" + "=" * 60)
    print("测试港股代码规范化")
    print("=" * 60)
    
    for symbol, expected, desc in test_cases:
        result = service._normalize_hk_code(symbol)
        status = "✅" if result == expected else "❌"
        print(f"{status} {desc:20} | {symbol:15} -> {result:10} | 期望:{expected}")

if __name__ == '__main__':
    test_chinese_stock()
    test_hk_stock()
    test_normalize_hk_code()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
