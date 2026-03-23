"""
WebSocket代理模块
处理WebSocket连接的代理转发
"""
import logging
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
import websockets
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WebSocketProxy:
    """WebSocket代理"""
    
    def __init__(self):
        self.service_urls = {
            "agent-service": "ws://agent-service:8010",
            "workflow-engine": "ws://workflow-engine:8002"
        }
    
    async def proxy_websocket(
        self, 
        websocket: WebSocket, 
        target_service: str,
        target_path: str
    ):
        """
        代理WebSocket连接
        
        Args:
            websocket: 客户端WebSocket连接
            target_service: 目标服务名称
            target_path: 目标路径
        """
        target_url = self.service_urls.get(target_service)
        if not target_url:
            await websocket.close(code=1003, reason=f"Service {target_service} not found")
            return
        
        # 构建目标WebSocket URL
        full_url = f"{target_url}{target_path}"
        
        logger.info(f"Proxying WebSocket to: {full_url}")
        
        try:
            # 接受客户端连接
            await websocket.accept()
            
            # 连接到目标服务
            async with websockets.connect(full_url) as target_ws:
                logger.info(f"Connected to target WebSocket: {full_url}")
                
                # 双向转发消息
                async def forward_to_client():
                    """从目标服务转发到客户端"""
                    try:
                        while True:
                            message = await target_ws.recv()
                            if isinstance(message, str):
                                await websocket.send_text(message)
                            else:
                                await websocket.send_bytes(message)
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("Target WebSocket closed")
                    except Exception as e:
                        logger.error(f"Error forwarding to client: {e}")
                
                async def forward_to_server():
                    """从客户端转发到目标服务"""
                    try:
                        while True:
                            data = await websocket.receive()
                            if "text" in data:
                                await target_ws.send(data["text"])
                            elif "bytes" in data:
                                await target_ws.send(data["bytes"])
                    except WebSocketDisconnect:
                        logger.info("Client disconnected")
                    except Exception as e:
                        logger.error(f"Error forwarding to server: {e}")
                
                # 运行双向转发
                try:
                    await asyncio.gather(
                        forward_to_client(),
                        forward_to_server(),
                        return_exceptions=True
                    )
                except Exception as e:
                    logger.error(f"Error in WebSocket proxy: {e}")
                    
        except websockets.exceptions.InvalidURI:
            logger.error(f"Invalid WebSocket URI: {full_url}")
            await websocket.close(code=1002, reason="Invalid target URI")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Target WebSocket connection closed")
            await websocket.close(code=1006, reason="Target connection closed")
        except Exception as e:
            logger.error(f"WebSocket proxy error: {e}", exc_info=True)
            try:
                await websocket.close(code=1011, reason="Internal server error")
            except:
                pass


# 全局WebSocket代理实例
websocket_proxy = WebSocketProxy()
