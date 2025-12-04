#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 StockDataFetcher 多数据源支持
演示 MySQL、xtquant、AKShare、Tushare 的数据获取功能
支持从数据库加载配置
"""

import sys
import os

# 添加项目路径到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.data.stock_data import create_stock_data_fetcher
from app.database import SessionLocal
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_stock_data_fetcher_with_db_config():
    """测试使用数据库配置的股票数据获取器"""
    
    print("\n" + "="*80)
    print("使用数据库配置创建 StockDataFetcher")
    print("="*80)
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 使用工厂方法创建获取器（从数据库加载配置）
        fetcher = create_stock_data_fetcher(db_session=db)
        
        # 测试股票代码（贵州茅台）
        test_code = "600519"
        
        print(f"\n测试股票代码: {test_code} (贵州茅台)")
        print("-"*80)
        
        # 1. 测试获取股票基本信息
        print("\n1️⃣  测试获取股票基本信息...")
        print("-"*80)
        stock_info = fetcher.get_stock_info(test_code)
        if stock_info and 'error' not in stock_info:
            print("✅ 成功获取股票信息:")
            for key, value in stock_info.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ 获取失败: {stock_info.get('error', '未知错误')}")
        
        # 2. 测试获取历史数据
        print("\n2️⃣  测试获取历史数据（1年）...")
        print("-"*80)
        hist_data = fetcher.get_stock_data(test_code, period="1y")
        if hist_data is not None and not hist_data.empty:
            print(f"✅ 成功获取历史数据: {len(hist_data)} 条记录")
            print("\n最新5条数据:")
            print(hist_data.tail(5))
        else:
            print("❌ 获取失败")
        
        # 3. 测试获取实时行情
        print("\n3️⃣  测试获取实时行情...")
        print("-"*80)
        quote = fetcher.get_realtime_quote(test_code)
        if quote:
            print(f"✅ 成功获取实时行情 (数据源: {quote.get('source', 'unknown')}):")
            for key, value in quote.items():
                print(f"   {key}: {value}")
        else:
            print("❌ 获取失败")
        
        # 4. 测试获取财务数据
        print("\n4️⃣  测试获取财务数据...")
        print("-"*80)
        financial_data = fetcher.get_financial_data(test_code)
        if financial_data:
            print(f"✅ 成功获取财务数据 (数据源: {financial_data.get('source', 'unknown')}):")
            print(f"   股票代码: {financial_data.get('symbol')}")
            
            # 显示有哪些表
            tables = []
            if 'balance_sheet' in financial_data:
                tables.append(f"资产负债表({len(financial_data['balance_sheet'])}条)")
            if 'income_statement' in financial_data:
                tables.append(f"利润表({len(financial_data['income_statement'])}条)")
            if 'cash_flow' in financial_data:
                tables.append(f"现金流量表({len(financial_data['cash_flow'])}条)")
            if 'pershare_index' in financial_data:
                tables.append(f"每股指标({len(financial_data['pershare_index'])}条)")
            
            if tables:
                print(f"   包含表: {', '.join(tables)}")
        else:
            print("❌ 获取失败")
        
        # 5. 测试 xtquant 下载财务数据（如果启用）
        if fetcher.xtquant_available:
            print("\n5️⃣  测试 xtquant 下载财务数据...")
            print("-"*80)
            success = fetcher.download_financial_data_xtquant(
                test_code, 
                table_list=['Balance', 'Income', 'CashFlow']
            )
            if success:
                print("✅ 成功下载财务数据到本地")
            else:
                print("❌ 下载失败")
        else:
            print("\n5️⃣  xtquant 未启用，跳过下载测试")
        
        # 输出数据源状态总结
        print("\n" + "="*80)
        print("📊 数据源状态总结:")
        print(f"   MySQL:    {'✅ 可用' if fetcher.mysql_available else '❌ 不可用'}")
        print(f"   xtquant:  {'✅ 可用' if fetcher.xtquant_available else '❌ 不可用'}")
        print(f"   AKShare:  ✅ 可用 (默认)")
        print(f"   Tushare:  {'✅ 可用' if fetcher.data_source_manager and hasattr(fetcher.data_source_manager, 'tushare_available') and fetcher.data_source_manager.tushare_available else '❌ 不可用'}")
        print("="*80)
        
    finally:
        db.close()


def test_stock_data_fetcher_without_db():
    """测试不使用数据库配置（使用环境变量）"""
    
    print("\n" + "="*80)
    print("使用环境变量配置创建 StockDataFetcher")
    print("="*80)
    
    # 不传入 db_session，将从环境变量读取配置
    fetcher = create_stock_data_fetcher()
    
    test_code = "600519"
    print(f"\n测试股票代码: {test_code}")
    
    # 简单测试
    quote = fetcher.get_realtime_quote(test_code)
    if quote:
        print(f"✅ 获取实时行情成功: 价格={quote.get('price')}, 来源={quote.get('source')}")
    else:
        print("❌ 获取实时行情失败")
    
    print("\n数据源状态:")
    print(f"   MySQL:    {'✅ 可用' if fetcher.mysql_available else '❌ 不可用'}")
    print(f"   xtquant:  {'✅ 可用' if fetcher.xtquant_available else '❌ 不可用'}")


if __name__ == "__main__":
    try:
        print("\n" + "#"*80)
        print("测试 1: 从数据库加载配置")
        print("#"*80)
        test_stock_data_fetcher_with_db_config()
        
        print("\n\n" + "#"*80)
        print("测试 2: 从环境变量加载配置")
        print("#"*80)
        test_stock_data_fetcher_without_db()
        
        print("\n" + "#"*80)
        print("测试完成！")
        print("#"*80)
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
