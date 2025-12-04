#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 get_technical_indicators 方法
验证 bug 修复: 'StockDataFetcher' object has no attribute 'get_technical_indicators'
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.data.stock_data import create_stock_data_fetcher
from app.database import SessionLocal
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_get_technical_indicators():
    """测试获取技术指标方法"""
    
    print("\n" + "="*80)
    print("测试 StockDataFetcher.get_technical_indicators() 方法")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        # 创建数据获取器
        fetcher = create_stock_data_fetcher(db_session=db)
        
        # 测试股票
        test_code = "600519"  # 贵州茅台
        
        print(f"\n🔍 测试股票: {test_code}")
        print("-"*80)
        
        # 测试 get_technical_indicators 方法
        print("\n📊 调用 get_technical_indicators()...")
        indicators = fetcher.get_technical_indicators(test_code)
        
        if indicators:
            print(f"\n✅ 成功获取技术指标！")
            print("-"*80)
            
            # 显示基本信息
            print(f"股票代码: {indicators.get('symbol')}")
            print(f"当前价格: {indicators.get('current_price'):.2f}")
            print(f"趋势: {indicators.get('trend')}")
            
            # 显示均线指标
            print(f"\n📈 均线指标:")
            print(f"   MA5:  {indicators.get('ma5'):.2f}")
            print(f"   MA10: {indicators.get('ma10'):.2f}")
            print(f"   MA20: {indicators.get('ma20'):.2f}")
            print(f"   MA60: {indicators.get('ma60'):.2f}")
            
            # 显示 MACD
            print(f"\n📊 MACD 指标:")
            print(f"   DIF: {indicators.get('macd_dif'):.4f}")
            print(f"   DEA: {indicators.get('macd_dea'):.4f}")
            print(f"   MACD: {indicators.get('macd'):.4f}")
            
            # 显示 RSI
            print(f"\n📉 RSI 指标:")
            print(f"   RSI: {indicators.get('rsi'):.2f}")
            
            # 显示 KDJ
            print(f"\n📊 KDJ 指标:")
            print(f"   K: {indicators.get('kdj_k'):.2f}")
            print(f"   D: {indicators.get('kdj_d'):.2f}")
            print(f"   J: {indicators.get('kdj_j'):.2f}")
            
            # 显示布林带
            print(f"\n📈 布林带指标:")
            print(f"   上轨: {indicators.get('boll_upper'):.2f}")
            print(f"   中轨: {indicators.get('boll_mid'):.2f}")
            print(f"   下轨: {indicators.get('boll_lower'):.2f}")
            print(f"   位置: {indicators.get('boll_position')}")
            
            # 显示成交量
            print(f"\n📊 成交量指标:")
            print(f"   成交量: {indicators.get('volume'):.0f}")
            print(f"   量比: {indicators.get('volume_ratio'):.2f}")
            
            print("\n" + "="*80)
            print("✅ 测试通过！bug 已修复")
            print("="*80)
            
        else:
            print("\n❌ 获取技术指标失败")
            
    except AttributeError as e:
        print(f"\n❌ AttributeError: {e}")
        print("⚠️  bug 未修复：StockDataFetcher 缺少 get_technical_indicators 方法")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    test_get_technical_indicators()
