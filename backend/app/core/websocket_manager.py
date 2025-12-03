"""
WebSocket连接管理器
"""
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储所有活跃的WebSocket连接
        # key: task_id, value: list of websockets
        self._connections: Dict[str, List[WebSocket]] = {}
        # 存储客户端订阅的任务
        # key: websocket_id, value: set of task_ids
        self._subscriptions: Dict[int, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str = None):
        """连接WebSocket"""
        await websocket.accept()
        ws_id = id(websocket)
        
        # 初始化订阅集合
        if ws_id not in self._subscriptions:
            self._subscriptions[ws_id] = set()
        
        # 如果指定了task_id，订阅该任务
        if task_id:
            await self.subscribe(websocket, task_id)
        
        logger.info(f"WebSocket连接建立: {ws_id}, task_id: {task_id}")
    
    async def subscribe(self, websocket: WebSocket, task_id: str):
        """订阅任务进度"""
        ws_id = id(websocket)
        
        if task_id not in self._connections:
            self._connections[task_id] = []
        
        if websocket not in self._connections[task_id]:
            self._connections[task_id].append(websocket)
        
        self._subscriptions[ws_id].add(task_id)
        logger.info(f"WebSocket {ws_id} 订阅任务: {task_id}")
    
    async def unsubscribe(self, websocket: WebSocket, task_id: str):
        """取消订阅任务"""
        ws_id = id(websocket)
        
        if task_id in self._connections and websocket in self._connections[task_id]:
            self._connections[task_id].remove(websocket)
            
            # 如果没有订阅者了，清理任务
            if not self._connections[task_id]:
                del self._connections[task_id]
        
        if ws_id in self._subscriptions:
            self._subscriptions[ws_id].discard(task_id)
        
        logger.info(f"WebSocket {ws_id} 取消订阅任务: {task_id}")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        ws_id = id(websocket)
        
        # 取消所有订阅
        if ws_id in self._subscriptions:
            task_ids = list(self._subscriptions[ws_id])
            for task_id in task_ids:
                if task_id in self._connections and websocket in self._connections[task_id]:
                    self._connections[task_id].remove(websocket)
                    if not self._connections[task_id]:
                        del self._connections[task_id]
            
            del self._subscriptions[ws_id]
        
        logger.info(f"WebSocket连接断开: {ws_id}")
    
    async def send_progress(self, task_id: str, data: dict):
        """发送进度更新到所有订阅该任务的客户端"""
        if task_id not in self._connections:
            return
        
        message = json.dumps(data, ensure_ascii=False)
        disconnected = []
        
        for websocket in self._connections[task_id]:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                disconnected.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected:
            self.disconnect(websocket)
    
    def get_active_tasks(self) -> List[str]:
        """获取所有活跃的任务ID"""
        return list(self._connections.keys())
    
    def has_subscribers(self, task_id: str) -> bool:
        """检查任务是否有订阅者"""
        return task_id in self._connections and len(self._connections[task_id]) > 0


# 全局WebSocket管理器实例
_ws_manager = WebSocketConnectionManager()


def get_ws_manager() -> WebSocketConnectionManager:
    """获取全局WebSocket管理器实例"""
    return _ws_manager
