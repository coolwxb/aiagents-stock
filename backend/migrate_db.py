"""
手动执行数据库迁移 - 添加监控任务字段
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

def upgrade():
    """添加新字段到monitor_tasks表"""
    print("开始执行数据库迁移...")
    
    with engine.connect() as conn:
        # 检查表是否存在（SQLite语法）
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='monitor_tasks';
        """))
        
        if not result.fetchone():
            print("monitor_tasks表不存在，跳过迁移")
            return
        
        # SQLite不支持IF NOT EXISTS，需要先检查列是否存在
        # 获取现有列
        result = conn.execute(text("PRAGMA table_info(monitor_tasks);"))
        existing_columns = {row[1] for row in result.fetchall()}
        
        print(f"现有字段: {existing_columns}")
        
        try:
            # 进场区间
            if 'entry_min' not in existing_columns:
                conn.execute(text("ALTER TABLE monitor_tasks ADD COLUMN entry_min REAL;"))
                print("  ✓ 添加 entry_min")
            
            if 'entry_max' not in existing_columns:
                conn.execute(text("ALTER TABLE monitor_tasks ADD COLUMN entry_max REAL;"))
                print("  ✓ 添加 entry_max")
            
            # 止盈止损
            if 'take_profit' not in existing_columns:
                conn.execute(text("ALTER TABLE monitor_tasks ADD COLUMN take_profit REAL;"))
                print("  ✓ 添加 take_profit")
            
            if 'stop_loss' not in existing_columns:
                conn.execute(text("ALTER TABLE monitor_tasks ADD COLUMN stop_loss REAL;"))
                print("  ✓ 添加 stop_loss")
            
            # 通知设置
            if 'notification_enabled' not in existing_columns:
                conn.execute(text("ALTER TABLE monitor_tasks ADD COLUMN notification_enabled BOOLEAN DEFAULT 0;"))
                print("  ✓ 添加 notification_enabled")
            
            # 量化配置
            if 'quant_config' not in existing_columns:
                conn.execute(text("ALTER TABLE monitor_tasks ADD COLUMN quant_config TEXT;"))
                print("  ✓ 添加 quant_config")

            # 策略字段
            if 'strategy' not in existing_columns:
                conn.execute(text("ALTER TABLE monitor_tasks ADD COLUMN strategy TEXT DEFAULT 'GS';"))
                print("  ✓ 添加 strategy (默认 GS)")
            
            conn.commit()
            print("\n✅ 数据库迁移成功完成！")
            print("已添加字段：")
            print("  - entry_min (进场最低价)")
            print("  - entry_max (进场最高价)")
            print("  - take_profit (止盈价位)")
            print("  - stop_loss (止损价位)")
            print("  - notification_enabled (通知开关)")
            print("  - quant_config (量化配置JSON)")
            print("  - strategy (监控策略，默认GS)")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 迁移失败: {e}")
            raise

if __name__ == "__main__":
    upgrade()
