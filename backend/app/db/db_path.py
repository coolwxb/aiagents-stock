"""
数据库路径统一配置模块
所有SQLite数据库文件统一存放在项目根目录的 sqlite_db 目录下
"""

import os
from pathlib import Path


def get_sqlite_db_dir() -> str:
    """
    获取SQLite数据库目录的绝对路径
    
    Returns:
        str: sqlite_db目录的绝对路径
    """
    # 从当前文件向上找到项目根目录（包含sqlite_db的目录）
    current_dir = Path(__file__).resolve().parent
    
    # backend/app/db -> backend/app -> backend -> 项目根目录
    project_root = current_dir.parent.parent.parent
    
    sqlite_db_dir = project_root / "sqlite_db"
    
    # 确保目录存在
    sqlite_db_dir.mkdir(parents=True, exist_ok=True)
    
    return str(sqlite_db_dir)


def get_db_path(db_name: str) -> str:
    """
    获取指定数据库文件的完整路径
    
    Args:
        db_name: 数据库文件名（如 'gs_strategy.db'）
        
    Returns:
        str: 数据库文件的完整路径
    """
    return os.path.join(get_sqlite_db_dir(), db_name)


# 预定义的数据库文件名常量
DB_STOCK_ANALYSIS = "stock_analysis.db"
DB_STOCK_MONITOR = "stock_monitor.db"
DB_GS_STRATEGY = "gs_strategy.db"
DB_SECTOR_STRATEGY = "sector_strategy.db"
DB_LONGHUBANG = "longhubang.db"
DB_MAIN_FORCE_BATCH = "main_force_batch.db"
DB_PORTFOLIO = "portfolio_stocks.db"
DB_SMART_MONITOR = "smart_monitor.db"


def get_all_db_paths() -> dict:
    """
    获取所有数据库文件路径
    
    Returns:
        dict: 数据库名称到路径的映射
    """
    return {
        'stock_analysis': get_db_path(DB_STOCK_ANALYSIS),
        'stock_monitor': get_db_path(DB_STOCK_MONITOR),
        'gs_strategy': get_db_path(DB_GS_STRATEGY),
        'sector_strategy': get_db_path(DB_SECTOR_STRATEGY),
        'longhubang': get_db_path(DB_LONGHUBANG),
        'main_force_batch': get_db_path(DB_MAIN_FORCE_BATCH),
        'portfolio': get_db_path(DB_PORTFOLIO),
        'smart_monitor': get_db_path(DB_SMART_MONITOR),
    }
