"""
WebSocket管理器
"""
import json
import logging
from typing import Dict, Callable, Any
from fastapi import WebSocket, WebSocketDisconnect

from .connection_manager import ConnectionManager
from ...models.prompt_models import UserAction

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket管理器 - 处理WebSocket连接和消息"""
    
    def __init__(self):
        self.manager = ConnectionManager()
        self.message_handlers: Dict[str, Callable] = {}
    
    async def handle_websocket(self, websocket: WebSocket, session_id: str):
        """
        处理WebSocket连接
        
        Args:
            websocket: WebSocket连接
            session_id: 会话ID
        """
        connection_id = await self.manager.connect(websocket, session_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._handle_message(data, session_id, connection_id)
        except WebSocketDisconnect:
            self.manager.disconnect(websocket, session_id)
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
            self.manager.disconnect(websocket, session_id)
    
    async def _handle_message(self, data: str, session_id: str, connection_id: str):
        """
        处理WebSocket消息
        
        Args:
            data: 消息数据（JSON字符串）
            session_id: 会话ID
            connection_id: 连接ID
        """
        try:
            message_data = json.loads(data)
            action = UserAction(**message_data)
            
            logger.debug(f"Received action: {action.action} for execution {action.execution_id}")
            
            # 根据action类型调用相应的处理器
            handler = self.message_handlers.get(action.action)
            if handler:
                await handler(action, session_id)
            else:
                logger.warning(f"No handler registered for action: {action.action}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}, data: {data[:100]}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}", exc_info=True)
    
    def register_handler(self, action: str, handler: Callable):
        """
        注册消息处理器
        
        Args:
            action: 操作类型
            handler: 处理函数
        """
        self.message_handlers[action] = handler
        logger.info(f"Registered handler for action: {action}")
    
    async def send_execution_update(self, message: dict):
        """
        发送执行更新消息
        
        Args:
            message: 消息字典（包含session_id）
        """
        session_id = message.get('session_id')
        if not session_id:
            logger.warning("Message missing session_id, cannot send")
            return
        
        await self.manager.broadcast_to_session(message, session_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            "total_connections": self.manager.get_total_connections(),
            "sessions": {
                session_id: self.manager.get_session_connections_count(session_id)
                for session_id in self.manager.session_connections.keys()
            },
            "registered_handlers": list(self.message_handlers.keys())
        }


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()





































