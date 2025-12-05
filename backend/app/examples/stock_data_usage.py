#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据获取器使用示例
展示如何在实际应用中使用从数据库加载的配置
"""

from sqlalchemy.orm import Session
from app.data.stock_data import create_stock_data_fetcher
from app.data.data_source_manager import get_data_source_manager
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


def example_1_basic_usage(db: Session):
    """示例 1: 基本使用 - 从数据库加载配置"""
    
    print("\n" + "="*80)
    print("示例 1: 基本使用 - 从数据库加载配置")
    print("="*80)
    
    # 创建数据获取器（自动从数据库加载配置）
    fetcher = create_stock_data_fetcher(db_session=db)
    
    # 获取股票数据
    stock_code = "600519"
    data = fetcher.get_stock_data(stock_code, period="1m")
    
    if data is not None:
        print(f"✅ 成功获取 {stock_code} 的历史数据，共 {len(data)} 条")
    else:
        print(f"❌ 获取 {stock_code} 的历史数据失败")


def example_2_with_data_source_manager(db: Session):
    """示例 2: 使用数据源管理器"""
    
    print("\n" + "="*80)
    print("示例 2: 使用数据源管理器")
    print("="*80)
    
    # 从数据库加载配置
    from app.services.config_service import ConfigService
    config_service = ConfigService(db)
    config = config_service._load_config()
    
    # 创建数据源管理器
    data_source_mgr = get_data_source_manager(config)
    
    # 创建数据获取器
    fetcher = create_stock_data_fetcher(
        db_session=db,
        data_source_manager=data_source_mgr
    )
    
    # 获取实时行情
    stock_code = "000001"
    quote = fetcher.get_realtime_quote(stock_code)
    
    if quote:
        print(f"✅ 成功获取 {stock_code} 实时行情")
        print(f"   价格: {quote.get('price')}")
        print(f"   数据源: {quote.get('source')}")
    else:
        print(f"❌ 获取 {stock_code} 实时行情失败")


def example_3_in_api_endpoint():
    """示例 3: 在 API 端点中使用（推荐方式）"""
    
    print("\n" + "="*80)
    print("示例 3: 在 API 端点中使用")
    print("="*80)
    
    # 模拟 FastAPI 依赖注入
    db = SessionLocal()
    
    try:
        # 在 API 端点中这样使用
        fetcher = create_stock_data_fetcher(db_session=db)
        
        # 处理请求
        stock_code = "600519"
        stock_info = fetcher.get_stock_info(stock_code)
        
        if stock_info:
            print(f"✅ API 返回股票信息:")
            print(f"   代码: {stock_info.get('symbol')}")
            print(f"   名称: {stock_info.get('name')}")
            print(f"   行业: {stock_info.get('industry')}")
        
        return {"success": True, "data": stock_info}
        
    finally:
        db.close()


def example_4_batch_processing(db: Session):
    """示例 4: 批量处理多只股票"""
    
    print("\n" + "="*80)
    print("示例 4: 批量处理多只股票")
    print("="*80)
    
    # 创建数据获取器（只初始化一次）
    fetcher = create_stock_data_fetcher(db_session=db)
    
    # 批量处理
    stock_codes = ["600519", "000001", "000002"]
    results = []
    
    for code in stock_codes:
        quote = fetcher.get_realtime_quote(code)
        if quote:
            results.append({
                "code": code,
                "price": quote.get('price'),
                "change_percent": quote.get('change_percent')
            })
            print(f"✅ {code}: 价格={quote.get('price')}, 涨跌幅={quote.get('change_percent')}%")
        else:
            print(f"❌ {code}: 获取失败")
    
    print(f"\n成功获取 {len(results)}/{len(stock_codes)} 只股票的数据")


def example_5_config_priority():
    """示例 5: 配置优先级演示"""
    
    print("\n" + "="*80)
    print("示例 5: 配置优先级演示")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        print("\n方式 1: 从数据库加载配置（推荐）")
        fetcher1 = create_stock_data_fetcher(db_session=db)
        print(f"   MySQL 状态: {'启用' if fetcher1.mysql_enabled else '禁用'}")
        print(f"   xtquant 状态: {'启用' if fetcher1.xtquant_enabled else '禁用'}")
        
        print("\n方式 2: 从环境变量加载配置（备用）")
        fetcher2 = create_stock_data_fetcher()  # 不传 db_session
        print(f"   MySQL 状态: {'启用' if fetcher2.mysql_enabled else '禁用'}")
        print(f"   xtquant 状态: {'启用' if fetcher2.xtquant_enabled else '禁用'}")
        
        print("\n配置优先级: 数据库配置 > 环境变量")
        
    finally:
        db.close()


if __name__ == "__main__":
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 运行所有示例
        example_1_basic_usage(db)
        example_2_with_data_source_manager(db)
        example_3_in_api_endpoint()
        example_4_batch_processing(db)
        example_5_config_priority()
        
        print("\n" + "="*80)
        print("✅ 所有示例运行完成！")
        print("="*80)
        
    except Exception as e:
        logger.error(f"运行示例时发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
