"""
测试QMT数据源优先级
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data.data_source import data_source_manager

def test_historical_data():
    """测试历史数据获取"""
    print("\n" + "=" * 60)
    print("测试1: 获取历史数据")
    print("=" * 60)
    
    symbol = "600519"  # 贵州茅台
    start_date = "20240101"
    end_date = "20241231"
    
    print(f"\n测试股票: {symbol}")
    print(f"开始日期: {start_date}")
    print(f"结束日期: {end_date}")
    print("\n" + "-" * 60)
    
    # 获取历史数据
    df = data_source_manager.get_stock_hist_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        adjust='qfq'
    )
    
    print("\n" + "-" * 60)
    
    if df is not None and not df.empty:
        print(f"\n✅ 成功获取历史数据，共 {len(df)} 条记录")
        print(f"\n前3条数据:")
        print(df.head(3))
        print(f"\n数据列: {list(df.columns)}")
    else:
        print("\n❌ 获取历史数据失败")

def test_basic_info():
    """测试基本信息获取"""
    print("\n" + "=" * 60)
    print("测试2: 获取股票基本信息")
    print("=" * 60)
    
    symbol = "600519"  # 贵州茅台
    
    print(f"\n测试股票: {symbol}")
    print("\n" + "-" * 60)
    
    # 获取基本信息
    info = data_source_manager.get_stock_basic_info(symbol)
    
    print("\n" + "-" * 60)
    
    if info and info.get('name') != '未知':
        print(f"\n✅ 成功获取基本信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        print("\n❌ 获取基本信息失败")

def test_realtime_quotes():
    """测试实时行情获取"""
    print("\n" + "=" * 60)
    print("测试3: 获取实时行情")
    print("=" * 60)
    
    symbol = "600519"  # 贵州茅台
    
    print(f"\n测试股票: {symbol}")
    print("\n" + "-" * 60)
    
    # 获取实时行情
    quotes = data_source_manager.get_realtime_quotes(symbol)
    
    print("\n" + "-" * 60)
    
    if quotes and quotes.get('price', 0) > 0:
        print(f"\n✅ 成功获取实时行情:")
        for key, value in quotes.items():
            print(f"  {key}: {value}")
    else:
        print("\n❌ 获取实时行情失败")

def test_financial_data():
    """测试财务数据获取"""
    print("\n" + "=" * 60)
    print("测试4: 获取财务数据")
    print("=" * 60)
    
    symbol = "600519"  # 贵州茅台
    
    # 测试利润表
    print(f"\n测试股票: {symbol}")
    print("报表类型: 利润表 (income)")
    print("\n" + "-" * 60)
    
    df = data_source_manager.get_financial_data(symbol, report_type='income')
    
    print("\n" + "-" * 60)
    
    if df is not None and not df.empty:
        print(f"\n✅ 成功获取财务数据，共 {len(df)} 个报告期")
        print(f"\n数据列: {list(df.columns)[:10]}...")  # 只显示前10列
        print(f"\n最新报告期数据:")
        print(df.head(1))
    else:
        print("\n❌ 获取财务数据失败")

def main():
    """主测试函数"""
    print("=" * 60)
    print("QMT数据源优先级测试")
    print("=" * 60)
    
    print(f"\n数据源状态:")
    print(f"  QMT可用: {data_source_manager.qmt_available}")
    print(f"  MySQL可用: {data_source_manager.mysql_available}")
    print(f"  Tushare可用: {data_source_manager.tushare_available}")
    
    # 运行所有测试
    test_historical_data()
    test_basic_info()
    test_realtime_quotes()
    test_financial_data()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
