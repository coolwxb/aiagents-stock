"""
WebSocket支持（实时数据推送）
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Set, Callable
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        """广播消息"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # 连接已断开，移除
                self.disconnect(connection)


manager = ConnectionManager()


class LonghubangProgressManager:
    """龙虎榜分析进度管理器"""
    
    def __init__(self):
        # task_id -> websocket 映射
        self.task_connections: Dict[str, WebSocket] = {}
        # task_id -> 进度信息
        self.task_progress: Dict[str, dict] = {}
        # 异步事件循环引用
        self._loop = None
    
    def set_loop(self, loop):
        """设置事件循环"""
        self._loop = loop
    
    async def connect(self, task_id: str, websocket: WebSocket):
        """连接到特定任务"""
        await websocket.accept()
        self.task_connections[task_id] = websocket
        self.task_progress[task_id] = {
            "status": "connected",
            "progress": 0,
            "message": "已连接，等待分析开始...",
            "timestamp": datetime.now().isoformat()
        }
    
    def disconnect(self, task_id: str):
        """断开任务连接"""
        if task_id in self.task_connections:
            del self.task_connections[task_id]
        if task_id in self.task_progress:
            del self.task_progress[task_id]
    
    async def send_progress(self, task_id: str, progress: int, message: str, 
                           stage: str = "", data: dict = None):
        """发送进度更新"""
        if task_id not in self.task_connections:
            return
        
        payload = {
            "type": "progress",
            "task_id": task_id,
            "progress": progress,
            "message": message,
            "stage": stage,
            "timestamp": datetime.now().isoformat()
        }
        if data:
            payload["data"] = data
        
        self.task_progress[task_id] = payload
        
        try:
            websocket = self.task_connections[task_id]
            await websocket.send_json(payload)
        except Exception as e:
            print(f"发送进度失败: {e}")
            self.disconnect(task_id)
    
    async def send_log(self, task_id: str, level: str, message: str):
        """发送日志消息"""
        if task_id not in self.task_connections:
            return
        
        payload = {
            "type": "log",
            "task_id": task_id,
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            websocket = self.task_connections[task_id]
            await websocket.send_json(payload)
        except Exception as e:
            print(f"发送日志失败: {e}")
            self.disconnect(task_id)
    
    async def send_complete(self, task_id: str, success: bool, result: dict = None, 
                           error: str = None):
        """发送完成消息"""
        if task_id not in self.task_connections:
            return
        
        payload = {
            "type": "complete",
            "task_id": task_id,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        if result:
            payload["result"] = result
        if error:
            payload["error"] = error
        
        try:
            websocket = self.task_connections[task_id]
            await websocket.send_json(payload)
        except Exception as e:
            print(f"发送完成消息失败: {e}")
        finally:
            # 完成后断开连接
            self.disconnect(task_id)
    
    def sync_send_progress(self, task_id: str, progress: int, message: str,
                          stage: str = "", data: dict = None):
        """同步发送进度（供非异步代码调用）"""
        if self._loop is None:
            return
        
        try:
            asyncio.run_coroutine_threadsafe(
                self.send_progress(task_id, progress, message, stage, data),
                self._loop
            )
        except Exception as e:
            print(f"同步发送进度失败: {e}")
    
    def sync_send_log(self, task_id: str, level: str, message: str):
        """同步发送日志（供非异步代码调用）"""
        if self._loop is None:
            return
        
        try:
            asyncio.run_coroutine_threadsafe(
                self.send_log(task_id, level, message),
                self._loop
            )
        except Exception as e:
            print(f"同步发送日志失败: {e}")


# 全局龙虎榜进度管理器
longhubang_progress_manager = LonghubangProgressManager()

