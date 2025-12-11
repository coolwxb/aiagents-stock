"""
智能盯盘 - 数据库模块
记录AI决策、交易记录、监控配置等
"""

import sqlite3
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json


class SmartMonitorDB:
    """智能盯盘数据库"""
    
    def __init__(self, db_file: str = None):
        """
        初始化数据库
        
        Args:
            db_file: 数据库文件路径，默认使用统一的sqlite_db目录
        """
        if db_file is None:
            from app.db.db_path import get_db_path, DB_SMART_MONITOR
            db_file = get_db_path(DB_SMART_MONITOR)
        self.db_file = db_file
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 1. 监控任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitor_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                enabled INTEGER DEFAULT 1,
                check_interval INTEGER DEFAULT 300,
                auto_trade INTEGER DEFAULT 0,
                position_size_pct REAL DEFAULT 20,
                stop_loss_pct REAL DEFAULT 5,
                take_profit_pct REAL DEFAULT 10,
                qmt_account_id TEXT,
                notify_email TEXT,
                notify_webhook TEXT,
                has_position INTEGER DEFAULT 0,
                position_cost REAL DEFAULT 0,
                position_quantity INTEGER DEFAULT 0,
                position_date TEXT,
                trading_hours_only INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code)
            )
        ''')
        
        # 添加字段（兼容已有数据库）
        for col, default in [
            ('has_position', 'INTEGER DEFAULT 0'),
            ('position_cost', 'REAL DEFAULT 0'),
            ('position_quantity', 'INTEGER DEFAULT 0'),
            ('position_date', 'TEXT'),
            ('trading_hours_only', 'INTEGER DEFAULT 1')
        ]:
            try:
                cursor.execute(f"ALTER TABLE monitor_tasks ADD COLUMN {col} {default}")
            except sqlite3.OperationalError:
                pass
        
        # 2. AI决策记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                decision_time TEXT NOT NULL,
                trading_session TEXT,
                action TEXT NOT NULL,
                confidence INTEGER,
                reasoning TEXT,
                position_size_pct REAL,
                stop_loss_pct REAL,
                take_profit_pct REAL,
                risk_level TEXT,
                key_price_levels TEXT,
                market_data TEXT,
                account_info TEXT,
                executed INTEGER DEFAULT 0,
                execution_result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3. 交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                trade_type TEXT NOT NULL,
                quantity INTEGER,
                price REAL,
                amount REAL,
                order_id TEXT,
                order_status TEXT,
                ai_decision_id INTEGER,
                trade_time TEXT NOT NULL,
                commission REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                profit_loss REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(ai_decision_id) REFERENCES ai_decisions(id)
            )
        ''')
        
        # 4. 持仓监控表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS position_monitor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                quantity INTEGER,
                cost_price REAL,
                current_price REAL,
                profit_loss REAL,
                profit_loss_pct REAL,
                holding_days INTEGER,
                buy_date TEXT,
                stop_loss_price REAL,
                take_profit_price REAL,
                last_check_time TEXT,
                status TEXT DEFAULT 'holding',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code)
            )
        ''')
        
        # 5. 通知记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT,
                notify_type TEXT NOT NULL,
                notify_target TEXT,
                subject TEXT,
                content TEXT,
                status TEXT DEFAULT 'pending',
                error_msg TEXT,
                sent_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 6. 系统日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_level TEXT,
                module TEXT,
                message TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info(f"数据库初始化完成: {self.db_file}")

    # ========== 监控任务管理 ==========
    
    def add_monitor_task(self, task_data: Dict) -> int:
        """添加监控任务"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO monitor_tasks 
            (task_name, stock_code, stock_name, enabled, check_interval, 
             auto_trade, trading_hours_only, position_size_pct, stop_loss_pct, take_profit_pct,
             qmt_account_id, notify_email, notify_webhook,
             has_position, position_cost, position_quantity, position_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_data.get('task_name'),
            task_data.get('stock_code'),
            task_data.get('stock_name'),
            task_data.get('enabled', 1),
            task_data.get('check_interval', 300),
            task_data.get('auto_trade', 0),
            task_data.get('trading_hours_only', 1),
            task_data.get('position_size_pct', 20),
            task_data.get('stop_loss_pct', 5),
            task_data.get('take_profit_pct', 10),
            task_data.get('qmt_account_id'),
            task_data.get('notify_email'),
            task_data.get('notify_webhook'),
            task_data.get('has_position', 0),
            task_data.get('position_cost', 0),
            task_data.get('position_quantity', 0),
            task_data.get('position_date')
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.logger.info(f"添加监控任务: {task_data.get('stock_code')} - {task_data.get('task_name')}")
        return task_id
    
    def get_monitor_tasks(self, enabled_only: bool = True) -> List[Dict]:
        """获取监控任务列表"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if enabled_only:
            cursor.execute('SELECT * FROM monitor_tasks WHERE enabled = 1 ORDER BY id DESC')
        else:
            cursor.execute('SELECT * FROM monitor_tasks ORDER BY id DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_monitor_task(self, stock_code: str, task_data: Dict):
        """更新监控任务"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        update_fields = []
        values = []
        
        field_map = ['task_name', 'check_interval', 'auto_trade', 'trading_hours_only',
                     'position_size_pct', 'has_position', 'position_cost', 
                     'position_quantity', 'position_date', 'notify_email']
        
        for field in field_map:
            if field in task_data:
                update_fields.append(f'{field} = ?')
                values.append(task_data[field])
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        values.append(stock_code)
        
        sql = f"UPDATE monitor_tasks SET {', '.join(update_fields)} WHERE stock_code = ?"
        cursor.execute(sql, values)
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"更新监控任务: {stock_code}")
    
    def delete_monitor_task(self, task_id: int):
        """删除监控任务"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM monitor_tasks WHERE id = ?', (task_id,))
        
        conn.commit()
        conn.close()
    
    # ========== AI决策记录 ==========
    
    def save_ai_decision(self, decision_data: Dict) -> int:
        """保存AI决策"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_decisions
            (stock_code, stock_name, decision_time, trading_session,
             action, confidence, reasoning, position_size_pct,
             stop_loss_pct, take_profit_pct, risk_level,
             key_price_levels, market_data, account_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            decision_data.get('stock_code'),
            decision_data.get('stock_name'),
            decision_data.get('decision_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            decision_data.get('trading_session'),
            decision_data.get('action'),
            decision_data.get('confidence'),
            decision_data.get('reasoning'),
            decision_data.get('position_size_pct'),
            decision_data.get('stop_loss_pct'),
            decision_data.get('take_profit_pct'),
            decision_data.get('risk_level'),
            json.dumps(decision_data.get('key_price_levels', {})),
            json.dumps(decision_data.get('market_data', {})),
            json.dumps(decision_data.get('account_info', {}))
        ))
        
        decision_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return decision_id
    
    def get_ai_decisions(self, stock_code: str = None, limit: int = 100) -> List[Dict]:
        """获取AI决策历史"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if stock_code:
            cursor.execute('''
                SELECT * FROM ai_decisions 
                WHERE stock_code = ? 
                ORDER BY decision_time DESC 
                LIMIT ?
            ''', (stock_code, limit))
        else:
            cursor.execute('''
                SELECT * FROM ai_decisions 
                ORDER BY decision_time DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        decisions = []
        for row in rows:
            d = dict(row)
            d['key_price_levels'] = json.loads(d['key_price_levels']) if d['key_price_levels'] else {}
            d['market_data'] = json.loads(d['market_data']) if d['market_data'] else {}
            d['account_info'] = json.loads(d['account_info']) if d['account_info'] else {}
            decisions.append(d)
        
        return decisions
    
    def update_decision_execution(self, decision_id: int, executed: bool, result: str):
        """更新决策执行状态"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ai_decisions 
            SET executed = ?, execution_result = ?
            WHERE id = ?
        ''', (1 if executed else 0, result, decision_id))
        
        conn.commit()
        conn.close()
    
    # ========== 交易记录 ==========
    
    def save_trade_record(self, trade_data: Dict) -> int:
        """保存交易记录"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trade_records
            (stock_code, stock_name, trade_type, quantity, price, amount,
             order_id, order_status, ai_decision_id, trade_time,
             commission, tax, profit_loss)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('stock_code'),
            trade_data.get('stock_name'),
            trade_data.get('trade_type'),
            trade_data.get('quantity'),
            trade_data.get('price'),
            trade_data.get('amount'),
            trade_data.get('order_id'),
            trade_data.get('order_status'),
            trade_data.get('ai_decision_id'),
            trade_data.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            trade_data.get('commission', 0),
            trade_data.get('tax', 0),
            trade_data.get('profit_loss', 0)
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_trade_records(self, stock_code: str = None, limit: int = 100) -> List[Dict]:
        """获取交易记录"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if stock_code:
            cursor.execute('''
                SELECT * FROM trade_records 
                WHERE stock_code = ? 
                ORDER BY trade_time DESC 
                LIMIT ?
            ''', (stock_code, limit))
        else:
            cursor.execute('''
                SELECT * FROM trade_records 
                ORDER BY trade_time DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ========== 持仓监控 ==========
    
    def save_position(self, position_data: Dict):
        """保存/更新持仓信息"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM position_monitor WHERE stock_code = ?', 
                      (position_data.get('stock_code'),))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE position_monitor
                SET stock_name = ?, quantity = ?, cost_price = ?,
                    current_price = ?, profit_loss = ?, profit_loss_pct = ?,
                    holding_days = ?, stop_loss_price = ?, take_profit_price = ?,
                    last_check_time = ?, updated_at = CURRENT_TIMESTAMP
                WHERE stock_code = ?
            ''', (
                position_data.get('stock_name'),
                position_data.get('quantity'),
                position_data.get('cost_price'),
                position_data.get('current_price'),
                position_data.get('profit_loss'),
                position_data.get('profit_loss_pct'),
                position_data.get('holding_days'),
                position_data.get('stop_loss_price'),
                position_data.get('take_profit_price'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                position_data.get('stock_code')
            ))
        else:
            cursor.execute('''
                INSERT INTO position_monitor
                (stock_code, stock_name, quantity, cost_price, current_price,
                 profit_loss, profit_loss_pct, holding_days, buy_date,
                 stop_loss_price, take_profit_price, last_check_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position_data.get('stock_code'),
                position_data.get('stock_name'),
                position_data.get('quantity'),
                position_data.get('cost_price'),
                position_data.get('current_price'),
                position_data.get('profit_loss'),
                position_data.get('profit_loss_pct'),
                position_data.get('holding_days'),
                position_data.get('buy_date'),
                position_data.get('stop_loss_price'),
                position_data.get('take_profit_price'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'holding'
            ))
        
        conn.commit()
        conn.close()
    
    def get_positions(self) -> List[Dict]:
        """获取所有持仓"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM position_monitor WHERE status = "holding" ORDER BY id DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def close_position(self, stock_code: str):
        """关闭持仓记录"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE position_monitor 
            SET status = 'closed', updated_at = CURRENT_TIMESTAMP
            WHERE stock_code = ?
        ''', (stock_code,))
        
        conn.commit()
        conn.close()
    
    # ========== 通知记录 ==========
    
    def save_notification(self, notify_data: Dict) -> int:
        """保存通知记录"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications
            (stock_code, notify_type, notify_target, subject, content, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            notify_data.get('stock_code'),
            notify_data.get('notify_type'),
            notify_data.get('notify_target'),
            notify_data.get('subject'),
            notify_data.get('content'),
            notify_data.get('status', 'pending')
        ))
        
        notify_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return notify_id
    
    def update_notification_status(self, notify_id: int, status: str, error_msg: str = None):
        """更新通知状态"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications 
            SET status = ?, error_msg = ?, sent_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, error_msg, notify_id))
        
        conn.commit()
        conn.close()
    
    # ========== 系统日志 ==========
    
    def log_system_event(self, level: str, module: str, message: str, details: str = None):
        """记录系统日志"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_logs (log_level, module, message, details)
            VALUES (?, ?, ?, ?)
        ''', (level, module, message, details))
        
        conn.commit()
        conn.close()


# 全局数据库实例
smart_monitor_db = SmartMonitorDB()
