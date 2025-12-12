#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建所有必要的数据库表
"""

from app.database import engine, Base
from app.models.stock import StockAnalysis
from app.models.analysis import AnalysisHistory
from app.models.monitor import MonitorTask
from app.models.portfolio import PortfolioStock
from app.models.user import User
from app.models.config import AppConfig
from app.models.sector import Sector, StockInstrument, SectorStock
from app.models.monitor import MonitorTask  # 确保包含最新字段（strategy等）


def init_database():
    """初始化数据库，创建所有表"""
    print("正在初始化数据库...")
    print(f"数据库引擎: {engine.url}")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("✅ 主数据库初始化完成！")
    print("\n已创建的表:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")
    
    # 初始化GS策略数据库（独立的SQLite数据库）
    print("\n正在初始化GS策略数据库...")
    try:
        from app.db.gs_strategy_db import GSStrategyDatabase
        gs_db = GSStrategyDatabase()
        print("✅ GS策略数据库初始化完成！")
        print("  - gs_stock_pool")
        print("  - gs_monitor_tasks")
        print("  - gs_trade_history")
    except Exception as e:
        print(f"⚠️ GS策略数据库初始化失败: {e}")


if __name__ == "__main__":
    init_database()
