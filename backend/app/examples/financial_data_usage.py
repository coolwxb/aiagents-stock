#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据获取使用示例
展示如何使用 xtquant、AKShare、Tushare 获取财务数据
"""

from app.data.stock_data import create_stock_data_fetcher
from app.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_financial_data():
    """示例 1: 基本财务数据获取"""
    
    print("\n" + "="*80)
    print("示例 1: 基本财务数据获取")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        # 创建数据获取器
        fetcher = create_stock_data_fetcher(db_session=db)
        
        # 测试股票
        test_code = "600519"  # 贵州茅台
        
        print(f"\n获取 {test_code} 的财务数据...")
        financial_data = fetcher.get_financial_data(test_code)
        
        if financial_data:
            print(f"✅ 成功获取财务数据 (数据源: {financial_data.get('source')})")
            print(f"\n包含的财务报表:")
            
            # 利润表
            if 'income_statement' in financial_data:
                income = financial_data['income_statement']
                print(f"  - 利润表: {len(income)} 期报告")
                if income:
                    latest = income[0] if isinstance(income, list) else income
                    print(f"    最新报告期字段: {list(latest.keys())[:5]}...")
            
            # 资产负债表
            if 'balance_sheet' in financial_data:
                balance = financial_data['balance_sheet']
                print(f"  - 资产负债表: {len(balance)} 期报告")
            
            # 现金流量表
            if 'cash_flow' in financial_data:
                cashflow = financial_data['cash_flow']
                print(f"  - 现金流量表: {len(cashflow)} 期报告")
            
            # 每股指标
            if 'pershare_index' in financial_data:
                pershare = financial_data['pershare_index']
                print(f"  - 每股指标: {len(pershare)} 期报告")
        else:
            print("❌ 获取财务数据失败")
            
    finally:
        db.close()


def example_download_financial_data():
    """示例 2: 下载财务数据到本地（xtquant）"""
    
    print("\n" + "="*80)
    print("示例 2: 下载财务数据到本地")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        fetcher = create_stock_data_fetcher(db_session=db)
        
        if not fetcher.xtquant_available:
            print("⚠️ xtquant 不可用，跳过此示例")
            return
        
        test_code = "600519"
        
        print(f"\n下载 {test_code} 的财务数据到本地...")
        
        # 指定要下载的表
        tables = ['Balance', 'Income', 'CashFlow', 'PershareIndex']
        
        success = fetcher.download_financial_data_xtquant(
            test_code, 
            table_list=tables
        )
        
        if success:
            print("✅ 财务数据下载成功！")
            print("   后续查询将更快速...")
            
            # 再次查询验证
            print("\n验证本地数据...")
            financial_data = fetcher.get_financial_data(test_code)
            if financial_data:
                print(f"✅ 可以正常读取本地财务数据")
        else:
            print("❌ 下载失败")
            
    finally:
        db.close()


def example_analyze_financial_data():
    """示例 3: 分析财务数据"""
    
    print("\n" + "="*80)
    print("示例 3: 分析财务数据")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        fetcher = create_stock_data_fetcher(db_session=db)
        
        test_code = "600519"
        
        print(f"\n分析 {test_code} 的财务状况...")
        financial_data = fetcher.get_financial_data(test_code)
        
        if not financial_data:
            print("❌ 无法获取财务数据")
            return
        
        # 分析利润表数据
        if 'income_statement' in financial_data:
            income_list = financial_data['income_statement']
            
            if income_list and len(income_list) > 0:
                print("\n📊 利润表分析:")
                
                # 显示最近3期数据
                for i, period in enumerate(income_list[:3]):
                    print(f"\n  第 {i+1} 期:")
                    
                    # 根据数据源显示不同字段
                    if financial_data.get('source') == 'xtquant':
                        # xtquant 字段
                        if 'm_timetag' in period:
                            print(f"    报告期: {period.get('m_timetag', 'N/A')}")
                        if 'm_anntime' in period:
                            print(f"    公告日期: {period.get('m_anntime', 'N/A')}")
                    else:
                        # AKShare/Tushare 字段
                        if '报告期' in period:
                            print(f"    报告期: {period.get('报告期', 'N/A')}")
                    
                    # 显示部分财务指标（如果存在）
                    revenue_keys = ['营业总收入', 'total_revenue', '营业收入']
                    profit_keys = ['净利润', 'net_profit', '归属于母公司所有者的净利润']
                    
                    for key in revenue_keys:
                        if key in period:
                            print(f"    营业收入: {period[key]}")
                            break
                    
                    for key in profit_keys:
                        if key in period:
                            print(f"    净利润: {period[key]}")
                            break
        
        # 分析每股指标（如果是 xtquant 数据）
        if 'pershare_index' in financial_data:
            pershare_list = financial_data['pershare_index']
            
            if pershare_list and len(pershare_list) > 0:
                print("\n📈 每股指标分析:")
                latest = pershare_list[0]
                
                # 显示常见每股指标
                indicators = {
                    'EPS': ['eps', 'BasicEPS'],
                    'BPS': ['bps', 'BPS'],
                    'ROE': ['roe', 'ROE']
                }
                
                for name, keys in indicators.items():
                    for key in keys:
                        if key in latest:
                            print(f"  {name}: {latest[key]}")
                            break
        
        print("\n✅ 财务分析完成")
        
    finally:
        db.close()


def example_batch_financial_data():
    """示例 4: 批量获取多只股票的财务数据"""
    
    print("\n" + "="*80)
    print("示例 4: 批量获取财务数据")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        fetcher = create_stock_data_fetcher(db_session=db)
        
        # 多只股票
        stock_codes = ["600519", "000858", "600036"]  # 茅台、五粮液、招商银行
        
        print("\n批量获取财务数据...\n")
        
        for code in stock_codes:
            financial_data = fetcher.get_financial_data(code)
            
            if financial_data:
                source = financial_data.get('source', 'unknown')
                
                # 统计包含的表
                tables = []
                if 'balance_sheet' in financial_data:
                    tables.append('资产负债表')
                if 'income_statement' in financial_data:
                    tables.append('利润表')
                if 'cash_flow' in financial_data:
                    tables.append('现金流量表')
                
                print(f"✅ {code}: {source} - 包含 {', '.join(tables)}")
            else:
                print(f"❌ {code}: 获取失败")
        
        print("\n批量处理完成！")
        
    finally:
        db.close()


if __name__ == "__main__":
    try:
        print("\n" + "#"*80)
        print("财务数据获取使用示例")
        print("#"*80)
        
        example_basic_financial_data()
        example_download_financial_data()
        example_analyze_financial_data()
        example_batch_financial_data()
        
        print("\n" + "#"*80)
        print("✅ 所有示例运行完成！")
        print("#"*80)
        
    except Exception as e:
        logger.error(f"运行示例时发生错误: {e}")
        import traceback
        traceback.print_exc()
