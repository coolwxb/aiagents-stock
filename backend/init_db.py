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


def init_database():
    """初始化数据库，创建所有表"""
    print("正在初始化数据库...")
    print(f"数据库引擎: {engine.url}")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("✅ 数据库初始化完成！")
    print("\n已创建的表:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    init_database()
