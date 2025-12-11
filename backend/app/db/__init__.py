"""
数据库操作模块

所有SQLite数据库文件统一存放在项目根目录的 sqlite_db 目录下
"""

from app.db.db_path import (
    get_sqlite_db_dir,
    get_db_path,
    get_all_db_paths,
    DB_STOCK_ANALYSIS,
    DB_STOCK_MONITOR,
    DB_GS_STRATEGY,
    DB_SECTOR_STRATEGY,
    DB_LONGHUBANG,
    DB_MAIN_FORCE_BATCH,
    DB_PORTFOLIO,
    DB_SMART_MONITOR,
)

# 数据库实例导入（延迟导入避免循环依赖）
def get_longhubang_db():
    from app.db.longhubang_db import LonghubangDatabase
    return LonghubangDatabase()

def get_main_force_batch_db():
    from app.db.main_force_batch_db import batch_db
    return batch_db

def get_monitor_db():
    from app.db.monitor_db import monitor_db
    return monitor_db

def get_portfolio_db():
    from app.db.portfolio_db import portfolio_db
    return portfolio_db

def get_sector_db():
    from app.db.sector_db import SectorStrategyDatabase
    return SectorStrategyDatabase()

def get_smart_monitor_db():
    from app.db.smart_monitor_db import smart_monitor_db
    return smart_monitor_db

def get_gs_strategy_db():
    from app.db.gs_strategy_db import gs_strategy_db
    return gs_strategy_db

def get_stock_analysis_db():
    from app.db.stock_db import stock_analysis_db
    return stock_analysis_db


__all__ = [
    # 路径工具
    'get_sqlite_db_dir',
    'get_db_path',
    'get_all_db_paths',
    # 数据库文件名常量
    'DB_STOCK_ANALYSIS',
    'DB_STOCK_MONITOR',
    'DB_GS_STRATEGY',
    'DB_SECTOR_STRATEGY',
    'DB_LONGHUBANG',
    'DB_MAIN_FORCE_BATCH',
    'DB_PORTFOLIO',
    'DB_SMART_MONITOR',
    # 数据库实例获取函数
    'get_longhubang_db',
    'get_main_force_batch_db',
    'get_monitor_db',
    'get_portfolio_db',
    'get_sector_db',
    'get_smart_monitor_db',
    'get_gs_strategy_db',
    'get_stock_analysis_db',
]
