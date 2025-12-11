"""
持仓股票数据库管理模块

提供持仓股票和分析历史的数据库操作接口
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os


class PortfolioDB:
    """持仓股票数据库管理类"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，默认使用统一的sqlite_db目录
        """
        if db_path is None:
            from app.db.db_path import get_db_path, DB_PORTFOLIO
            db_path = get_db_path(DB_PORTFOLIO)
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 创建持仓股票表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    cost_price REAL,
                    quantity INTEGER,
                    note TEXT,
                    auto_monitor BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建持仓分析历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_stock_id INTEGER NOT NULL,
                    analysis_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    rating TEXT,
                    confidence REAL,
                    current_price REAL,
                    target_price REAL,
                    entry_min REAL,
                    entry_max REAL,
                    take_profit REAL,
                    stop_loss REAL,
                    summary TEXT,
                    FOREIGN KEY (portfolio_stock_id) REFERENCES portfolio_stocks(id) ON DELETE CASCADE
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_portfolio_analysis_stock_id 
                ON portfolio_analysis_history(portfolio_stock_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_portfolio_analysis_time 
                ON portfolio_analysis_history(analysis_time DESC)
            ''')
            
            conn.commit()
            
        except Exception as e:
            print(f"[ERROR] 数据库初始化失败: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ==================== 持仓股票CRUD操作 ====================
    
    def add_stock(self, code: str, name: str, cost_price: Optional[float] = None,
                  quantity: Optional[int] = None, note: str = "", 
                  auto_monitor: bool = True) -> int:
        """添加持仓股票"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO portfolio_stocks 
                (code, name, cost_price, quantity, note, auto_monitor, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (code, name, cost_price, quantity, note, auto_monitor, 
                  datetime.now(), datetime.now()))
            
            conn.commit()
            stock_id = cursor.lastrowid
            return stock_id
            
        except sqlite3.IntegrityError as e:
            raise ValueError(f"股票代码 {code} 已存在") from e
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def update_stock(self, stock_id: int, **kwargs) -> bool:
        """更新持仓股票信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['code', 'name', 'cost_price', 'quantity', 'note', 'auto_monitor']
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            return False
        
        update_fields['updated_at'] = datetime.now()
        
        set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
        values = list(update_fields.values()) + [stock_id]
        
        try:
            cursor.execute(f'''
                UPDATE portfolio_stocks 
                SET {set_clause}
                WHERE id = ?
            ''', values)
            
            conn.commit()
            return cursor.rowcount > 0
                
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def delete_stock(self, stock_id: int) -> bool:
        """删除持仓股票（级联删除其所有分析历史）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM portfolio_stocks WHERE id = ?', (stock_id,))
            conn.commit()
            return cursor.rowcount > 0
                
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_stock(self, stock_id: int) -> Optional[Dict]:
        """获取单只持仓股票信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM portfolio_stocks WHERE id = ?', (stock_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        finally:
            conn.close()
    
    def get_stock_by_code(self, code: str) -> Optional[Dict]:
        """根据股票代码获取持仓股票信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM portfolio_stocks WHERE code = ?', (code,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        finally:
            conn.close()
    
    def get_all_stocks(self, auto_monitor_only: bool = False) -> List[Dict]:
        """获取所有持仓股票列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if auto_monitor_only:
                cursor.execute('''
                    SELECT * FROM portfolio_stocks 
                    WHERE auto_monitor = 1
                    ORDER BY created_at DESC
                ''')
            else:
                cursor.execute('SELECT * FROM portfolio_stocks ORDER BY created_at DESC')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def search_stocks(self, keyword: str) -> List[Dict]:
        """搜索持仓股票（按代码或名称）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            keyword_pattern = f"%{keyword}%"
            cursor.execute('''
                SELECT * FROM portfolio_stocks 
                WHERE code LIKE ? OR name LIKE ?
                ORDER BY created_at DESC
            ''', (keyword_pattern, keyword_pattern))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_stock_count(self) -> int:
        """获取持仓股票总数"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT COUNT(*) as count FROM portfolio_stocks')
            result = cursor.fetchone()
            return result['count']
            
        finally:
            conn.close()

    # ==================== 分析历史记录操作 ====================
    
    def save_analysis(self, stock_id: int, rating: str, confidence: float,
                     current_price: float, target_price: Optional[float] = None,
                     entry_min: Optional[float] = None, entry_max: Optional[float] = None,
                     take_profit: Optional[float] = None, stop_loss: Optional[float] = None,
                     summary: str = "") -> int:
        """保存分析历史记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO portfolio_analysis_history 
                (portfolio_stock_id, analysis_time, rating, confidence, current_price,
                 target_price, entry_min, entry_max, take_profit, stop_loss, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (stock_id, datetime.now(), rating, confidence, current_price,
                  target_price, entry_min, entry_max, take_profit, stop_loss, summary))
            
            conn.commit()
            return cursor.lastrowid
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_analysis_history(self, stock_id: int, limit: int = 10) -> List[Dict]:
        """获取股票的分析历史记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM portfolio_analysis_history 
                WHERE portfolio_stock_id = ?
                ORDER BY analysis_time DESC
                LIMIT ?
            ''', (stock_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_latest_analysis_history(self, stock_id: int, limit: int = 10) -> List[Dict]:
        """获取股票的最新分析历史记录（别名方法）"""
        return self.get_analysis_history(stock_id, limit)
    
    def get_latest_analysis(self, stock_id: int) -> Optional[Dict]:
        """获取股票的最新一次分析记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM portfolio_analysis_history 
                WHERE portfolio_stock_id = ?
                ORDER BY analysis_time DESC
                LIMIT 1
            ''', (stock_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        finally:
            conn.close()
    
    def get_rating_changes(self, stock_id: int, days: int = 30) -> List[Tuple[str, str, str]]:
        """获取股票在指定天数内的评级变化"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT analysis_time, rating 
                FROM portfolio_analysis_history 
                WHERE portfolio_stock_id = ?
                AND analysis_time >= datetime('now', '-' || ? || ' days')
                ORDER BY analysis_time ASC
            ''', (stock_id, days))
            
            rows = cursor.fetchall()
            
            changes = []
            for i in range(1, len(rows)):
                prev_rating = rows[i-1]['rating']
                curr_rating = rows[i]['rating']
                if prev_rating != curr_rating:
                    changes.append((
                        rows[i]['analysis_time'],
                        prev_rating,
                        curr_rating
                    ))
            
            return changes
            
        finally:
            conn.close()
    
    def delete_old_analysis(self, days: int = 90) -> int:
        """删除超过指定天数的分析历史记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM portfolio_analysis_history 
                WHERE analysis_time < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            conn.commit()
            return cursor.rowcount
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_all_latest_analysis(self) -> List[Dict]:
        """获取所有持仓股票的最新分析记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    s.*,
                    h.rating, h.confidence, h.current_price, h.target_price,
                    h.entry_min, h.entry_max, h.take_profit, h.stop_loss,
                    h.analysis_time
                FROM portfolio_stocks s
                LEFT JOIN (
                    SELECT h1.*
                    FROM portfolio_analysis_history h1
                    INNER JOIN (
                        SELECT portfolio_stock_id, MAX(analysis_time) as max_time
                        FROM portfolio_analysis_history
                        GROUP BY portfolio_stock_id
                    ) h2
                    ON h1.portfolio_stock_id = h2.portfolio_stock_id 
                    AND h1.analysis_time = h2.max_time
                ) h ON s.id = h.portfolio_stock_id
                ORDER BY s.created_at DESC
            ''')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()


# 创建全局数据库实例
portfolio_db = PortfolioDB()
