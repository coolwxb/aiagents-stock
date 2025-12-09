"""
GS策略数据库模块
使用独立的SQLite数据库文件存储GS策略相关数据
"""

import sqlite3
from datetime import datetime
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path


class GSStrategyDatabase:
    """GS策略数据库管理类"""
    
    def __init__(self, db_path='gs_strategy.db'):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 股票池表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS gs_stock_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL UNIQUE,
            stock_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        )
        ''')

        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_code ON gs_stock_pool(stock_code)')
        
        # 监控任务表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS gs_monitor_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_pool_id INTEGER,
            stock_code TEXT NOT NULL,
            stock_name TEXT,
            interval INTEGER DEFAULT 300,
            status TEXT DEFAULT 'stopped',
            started_at TEXT,
            execution_count INTEGER DEFAULT 0,
            last_signal TEXT,
            last_signal_time TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            FOREIGN KEY(stock_pool_id) REFERENCES gs_stock_pool(id) ON DELETE CASCADE
        )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_monitor_stock_code ON gs_monitor_tasks(stock_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_monitor_status ON gs_monitor_tasks(status)')
        
        # 交易历史表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS gs_trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monitor_id INTEGER,
            stock_code TEXT NOT NULL,
            stock_name TEXT,
            buy_price REAL,
            buy_quantity INTEGER,
            buy_time TEXT,
            buy_order_id TEXT,
            sell_price REAL,
            sell_quantity INTEGER,
            sell_time TEXT,
            sell_order_id TEXT,
            profit_loss REAL,
            profit_loss_pct REAL,
            status TEXT,
            trade_details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            FOREIGN KEY(monitor_id) REFERENCES gs_monitor_tasks(id) ON DELETE CASCADE
        )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_stock_code ON gs_trade_history(stock_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_status ON gs_trade_history(status)')
        
        conn.commit()
        conn.close()
        
        self.logger.info("[GS策略] 数据库初始化完成")

    
    # ==================== 股票池管理方法 ====================
    
    def add_stock(self, stock_code: str, stock_name: str) -> int:
        """
        添加股票到股票池
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            
        Returns:
            int: 股票ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO gs_stock_pool (stock_code, stock_name)
            VALUES (?, ?)
            ''', (stock_code, stock_name))
            
            stock_id = cursor.lastrowid
            conn.commit()
            
            self.logger.info(f"[GS策略] 添加股票: {stock_code} - {stock_name}")
            return stock_id
            
        except sqlite3.IntegrityError:
            self.logger.warning(f"[GS策略] 股票已存在: {stock_code}")
            raise ValueError(f"股票代码 {stock_code} 已存在于股票池中")
        finally:
            conn.close()
    
    def remove_stock(self, stock_id: int) -> bool:
        """
        从股票池中删除股票（级联删除关联的监控任务和交易历史）
        
        Args:
            stock_id: 股票ID
            
        Returns:
            bool: 是否删除成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM gs_stock_pool WHERE id = ?', (stock_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                self.logger.info(f"[GS策略] 删除股票 (ID: {stock_id})")
                return True
            else:
                raise ValueError(f"股票池中未找到ID为 {stock_id} 的股票")
                
        finally:
            conn.close()

    
    def get_stock_pool(self) -> List[Dict]:
        """
        获取股票池列表
        
        Returns:
            List[Dict]: 股票池列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, stock_code, stock_name, created_at, updated_at
        FROM gs_stock_pool
        ORDER BY created_at DESC
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def search_stock_pool(self, keyword: str) -> List[Dict]:
        """
        搜索股票池
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[Dict]: 匹配的股票列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, stock_code, stock_name, created_at, updated_at
        FROM gs_stock_pool
        WHERE stock_code LIKE ? OR stock_name LIKE ?
        ORDER BY created_at DESC
        ''', (f'%{keyword}%', f'%{keyword}%'))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_stock_by_id(self, stock_id: int) -> Optional[Dict]:
        """
        根据ID获取股票信息
        
        Args:
            stock_id: 股票ID
            
        Returns:
            Optional[Dict]: 股票信息
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM gs_stock_pool WHERE id = ?', (stock_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            return dict(zip(columns, row))
        
        conn.close()
        return None

    
    # ==================== 监控任务管理方法 ====================
    
    def create_monitor(self, stock_pool_id: int, stock_code: str, stock_name: str, interval: int = 300) -> int:
        """
        创建监控任务
        
        Args:
            stock_pool_id: 股票池ID
            stock_code: 股票代码
            stock_name: 股票名称
            interval: 监测间隔（秒）
            
        Returns:
            int: 监控任务ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            cursor.execute('''
            INSERT INTO gs_monitor_tasks 
            (stock_pool_id, stock_code, stock_name, interval, status, started_at)
            VALUES (?, ?, ?, ?, 'running', ?)
            ''', (stock_pool_id, stock_code, stock_name, interval, now))
            
            monitor_id = cursor.lastrowid
            conn.commit()
            
            self.logger.info(f"[GS策略] 创建监控任务: {stock_code} - {stock_name}")
            return monitor_id
            
        finally:
            conn.close()
    
    def update_monitor(self, monitor_id: int, **kwargs) -> bool:
        """
        更新监控任务
        
        Args:
            monitor_id: 监控任务ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 构建更新语句
            update_fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['interval', 'status', 'started_at', 'execution_count', 'last_signal', 'last_signal_time']:
                    update_fields.append(f'{key} = ?')
                    values.append(value)
            
            if not update_fields:
                return False
            
            # 添加updated_at
            update_fields.append('updated_at = ?')
            values.append(datetime.now().isoformat())
            values.append(monitor_id)
            
            query = f"UPDATE gs_monitor_tasks SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            
            updated_count = cursor.rowcount
            conn.commit()
            
            return updated_count > 0
            
        finally:
            conn.close()

    
    def delete_monitor(self, monitor_id: int) -> bool:
        """
        删除监控任务
        
        Args:
            monitor_id: 监控任务ID
            
        Returns:
            bool: 是否删除成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM gs_monitor_tasks WHERE id = ?', (monitor_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                self.logger.info(f"[GS策略] 删除监控任务 (ID: {monitor_id})")
                return True
            else:
                raise ValueError(f"监控任务 {monitor_id} 不存在")
                
        finally:
            conn.close()
    
    def get_monitors(self) -> List[Dict]:
        """
        获取所有监控任务列表
        
        Returns:
            List[Dict]: 监控任务列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM gs_monitor_tasks
        ORDER BY created_at DESC
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_monitor_by_id(self, monitor_id: int) -> Optional[Dict]:
        """
        根据ID获取监控任务
        
        Args:
            monitor_id: 监控任务ID
            
        Returns:
            Optional[Dict]: 监控任务信息
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM gs_monitor_tasks WHERE id = ?', (monitor_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            return dict(zip(columns, row))
        
        conn.close()
        return None
    
    def get_running_monitors(self) -> List[Dict]:
        """
        获取所有运行中的监控任务
        
        Returns:
            List[Dict]: 运行中的监控任务列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM gs_monitor_tasks
        WHERE status = 'running'
        ORDER BY created_at DESC
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]

    
    # ==================== 交易历史管理方法 ====================
    
    def create_trade(self, monitor_id: int, stock_code: str, stock_name: str, 
                     buy_price: float, buy_quantity: int, buy_order_id: str) -> int:
        """
        创建交易记录（买入）
        
        Args:
            monitor_id: 监控任务ID
            stock_code: 股票代码
            stock_name: 股票名称
            buy_price: 买入价格
            buy_quantity: 买入数量
            buy_order_id: 买入订单ID
            
        Returns:
            int: 交易记录ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            cursor.execute('''
            INSERT INTO gs_trade_history 
            (monitor_id, stock_code, stock_name, buy_price, buy_quantity, buy_time, buy_order_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'open')
            ''', (monitor_id, stock_code, stock_name, buy_price, buy_quantity, now, buy_order_id))
            
            trade_id = cursor.lastrowid
            conn.commit()
            
            self.logger.info(f"[GS策略] 创建交易记录: {stock_code} 买入 {buy_quantity}股 @ {buy_price}")
            return trade_id
            
        finally:
            conn.close()
    
    def complete_trade(self, trade_id: int, sell_price: float, sell_quantity: int, sell_order_id: str) -> bool:
        """
        完成交易（卖出）
        
        Args:
            trade_id: 交易记录ID
            sell_price: 卖出价格
            sell_quantity: 卖出数量
            sell_order_id: 卖出订单ID
            
        Returns:
            bool: 是否更新成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取买入信息
            cursor.execute('SELECT buy_price, buy_quantity FROM gs_trade_history WHERE id = ?', (trade_id,))
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"交易记录 {trade_id} 不存在")
            
            buy_price, buy_quantity = row
            
            # 计算盈亏
            profit_loss = (sell_price - buy_price) * buy_quantity
            profit_loss_pct = ((sell_price - buy_price) / buy_price) * 100
            
            now = datetime.now().isoformat()
            cursor.execute('''
            UPDATE gs_trade_history
            SET sell_price = ?, sell_quantity = ?, sell_time = ?, sell_order_id = ?,
                profit_loss = ?, profit_loss_pct = ?, status = 'closed', updated_at = ?
            WHERE id = ?
            ''', (sell_price, sell_quantity, now, sell_order_id, profit_loss, profit_loss_pct, now, trade_id))
            
            conn.commit()
            
            self.logger.info(f"[GS策略] 完成交易 (ID: {trade_id}): 盈亏 {profit_loss:.2f} ({profit_loss_pct:.2f}%)")
            return True
            
        finally:
            conn.close()

    
    def get_trade_history(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """
        获取交易历史记录
        
        Args:
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            
        Returns:
            List[Dict]: 交易历史列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM gs_trade_history WHERE 1=1'
        params = []
        
        if start_date:
            query += ' AND created_at >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND created_at <= ?'
            params.append(f'{end_date} 23:59:59')
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_open_trade_by_monitor(self, monitor_id: int) -> Optional[Dict]:
        """
        获取监控任务的未平仓交易
        
        Args:
            monitor_id: 监控任务ID
            
        Returns:
            Optional[Dict]: 未平仓交易记录
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM gs_trade_history
        WHERE monitor_id = ? AND status = 'open'
        ORDER BY created_at DESC
        LIMIT 1
        ''', (monitor_id,))
        
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            return dict(zip(columns, row))
        
        conn.close()
        return None
    
    def get_statistics(self) -> Dict:
        """
        获取交易统计数据
        
        Returns:
            Dict: 统计数据
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 总交易数
        cursor.execute("SELECT COUNT(*) FROM gs_trade_history WHERE status = 'closed'")
        total_trades = cursor.fetchone()[0]
        
        # 盈利交易数
        cursor.execute("SELECT COUNT(*) FROM gs_trade_history WHERE status = 'closed' AND profit_loss > 0")
        winning_trades = cursor.fetchone()[0]
        
        # 亏损交易数
        cursor.execute("SELECT COUNT(*) FROM gs_trade_history WHERE status = 'closed' AND profit_loss < 0")
        losing_trades = cursor.fetchone()[0]
        
        # 总盈亏
        cursor.execute("SELECT SUM(profit_loss) FROM gs_trade_history WHERE status = 'closed'")
        total_profit_loss = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        # 计算胜率
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_profit_loss': round(total_profit_loss, 2),
            'win_rate': round(win_rate, 2)
        }
    
    def get_db_statistics(self) -> Dict:
        """
        获取数据库统计信息
        
        Returns:
            Dict: 统计信息
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # 股票池数量
        cursor.execute('SELECT COUNT(*) FROM gs_stock_pool')
        stats['total_stocks'] = cursor.fetchone()[0]
        
        # 监控任务数量
        cursor.execute('SELECT COUNT(*) FROM gs_monitor_tasks')
        stats['total_monitors'] = cursor.fetchone()[0]
        
        # 运行中的监控任务数量
        cursor.execute("SELECT COUNT(*) FROM gs_monitor_tasks WHERE status = 'running'")
        stats['running_monitors'] = cursor.fetchone()[0]
        
        # 交易记录数量
        cursor.execute('SELECT COUNT(*) FROM gs_trade_history')
        stats['total_trades'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats


# 创建全局实例
gs_strategy_db = GSStrategyDatabase('gs_strategy.db')


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试GS策略数据库模块")
    print("=" * 60)
    
    db = GSStrategyDatabase('test_gs_strategy.db')
    
    # 测试添加股票
    try:
        stock_id = db.add_stock('600519', '贵州茅台')
        print(f"\n添加股票成功，ID: {stock_id}")
    except ValueError as e:
        print(f"\n添加股票失败: {e}")
    
    # 测试查询股票池
    stocks = db.get_stock_pool()
    print(f"\n股票池数量: {len(stocks)}")
    
    # 获取统计信息
    stats = db.get_db_statistics()
    print(f"\n数据库统计: {stats}")
