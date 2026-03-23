"""
WebSocket连接管理器
"""
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str) -> str:
        """
        连接WebSocket
        
        Args:
            websocket: WebSocket连接
            session_id: 会话ID
            
        Returns:
            连接ID
        """
        await websocket.accept()
        connection_id = str(id(websocket))
        self.active_connections[connection_id] = websocket
        
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} for session {session_id}")
        return connection_id
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """
        断开WebSocket连接
        
        Args:
            websocket: WebSocket连接
            session_id: 会话ID
        """
        connection_id = str(id(websocket))
        self.active_connections.pop(connection_id, None)
        
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(connection_id)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
        
        logger.info(f"WebSocket disconnected: {connection_id} from session {session_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        发送个人消息
        
        Args:
            message: 消息字典
            websocket: WebSocket连接
        """
        try:
            import json
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def broadcast_to_session(self, message: dict, session_id: str):
        """
        向会话广播消息
        
        Args:
            message: 消息字典
            session_id: 会话ID
        """
        if session_id not in self.session_connections:
            logger.warning(f"No connections found for session {session_id}")
            return
        
        disconnected = set()
        for connection_id in self.session_connections[session_id]:
            websocket = self.active_connections.get(connection_id)
            if websocket:
                try:
                    await self.send_personal_message(message, websocket)
                except Exception as e:
                    logger.error(f"Failed to send message to {connection_id}: {e}")
                    disconnected.add(connection_id)
            else:
                disconnected.add(connection_id)
        
        # 清理断开连接的WebSocket
        for connection_id in disconnected:
            self.session_connections[session_id].discard(connection_id)
        
        if not self.session_connections[session_id]:
            del self.session_connections[session_id]
    
    def get_session_connections_count(self, session_id: str) -> int:
        """获取会话的连接数"""
        return len(self.session_connections.get(session_id, set()))
    
    def get_total_connections(self) -> int:
        """获取总连接数"""
        return len(self.active_connections)





































