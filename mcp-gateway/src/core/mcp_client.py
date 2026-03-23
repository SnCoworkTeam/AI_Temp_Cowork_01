"""
MCP客户端实现
用于连接MCP服务器、发现工具和执行工具
"""
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

try:
    import websockets
    from websockets.exceptions import ConnectionClosed
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None
    ConnectionClosed = Exception
    logger.warning("websockets not available, MCP client will not work")

from ..models.tool_models import ToolDefinition, ToolType, ToolStatus


class MCPConnectionError(Exception):
    """MCP连接错误"""
    pass


class MCPProtocolError(Exception):
    """MCP协议错误"""
    pass


class MCPClient:
    """MCP客户端 - 连接MCP服务器并执行工具"""
    
    def __init__(self, server_url: str, timeout: int = 30, server_name: str = ""):
        """
        初始化MCP客户端
        
        Args:
            server_url: MCP服务器WebSocket URL
            timeout: 连接和请求超时时间（秒）
            server_name: 服务器名称（用于日志和标识）
        """
        self.server_url = server_url
        self.timeout = timeout
        self.server_name = server_name or server_url
        self.websocket = None
        self.connected = False
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3
        self._reconnect_delay = 1.0
    
    async def connect(self) -> bool:
        """
        连接到MCP服务器
        
        Returns:
            是否连接成功
        """
        if not WEBSOCKETS_AVAILABLE or websockets is None:
            logger.error("websockets library not available, cannot connect to MCP server")
            return False
        
        try:
            logger.info(f"Connecting to MCP server: {self.server_url}")
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.server_url),
                timeout=self.timeout
            )
            self.connected = True
            self._reconnect_attempts = 0
            
            # 启动消息接收任务
            asyncio.create_task(self._message_handler())
            
            logger.info(f"Connected to MCP server: {self.server_name}")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to MCP server: {self.server_url}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.server_url}: {e}")
            return False
    
    async def _message_handler(self):
        """处理来自MCP服务器的消息"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    request_id = data.get("id")
                    
                    if request_id and request_id in self._pending_requests:
                        future = self._pending_requests.pop(request_id)
                        if "error" in data:
                            future.set_exception(MCPProtocolError(data["error"].get("message", "Unknown error")))
                        else:
                            future.set_result(data.get("result"))
                    else:
                        logger.warning(f"Received message with unknown request ID: {request_id}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse MCP message: {e}")
                except Exception as e:
                    logger.error(f"Error handling MCP message: {e}")
                    
        except ConnectionClosed:
            logger.warning(f"MCP server connection closed: {self.server_name}")
            self.connected = False
            await self._attempt_reconnect()
        except Exception as e:
            logger.error(f"Message handler error: {e}")
            self.connected = False
    
    async def _attempt_reconnect(self):
        """尝试重新连接"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error(f"Max reconnect attempts reached for {self.server_name}")
            return
        
        self._reconnect_attempts += 1
        delay = self._reconnect_delay * (2 ** (self._reconnect_attempts - 1))
        logger.info(f"Attempting to reconnect to {self.server_name} (attempt {self._reconnect_attempts}/{self._max_reconnect_attempts}) after {delay}s")
        
        await asyncio.sleep(delay)
        await self.connect()
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Any:
        """
        发送JSON-RPC请求到MCP服务器
        
        Args:
            method: 方法名
            params: 参数
            
        Returns:
            响应结果
            
        Raises:
            MCPConnectionError: 如果未连接
            MCPProtocolError: 如果协议错误
        """
        if not self.connected or not self.websocket:
            raise MCPConnectionError(f"Not connected to MCP server: {self.server_name}")
        
        self._request_id += 1
        request_id = self._request_id
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        # 创建Future等待响应
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            # 发送请求
            await self.websocket.send(json.dumps(request))
            
            # 等待响应（带超时）
            result = await asyncio.wait_for(future, timeout=self.timeout)
            return result
            
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise MCPProtocolError(f"Request timeout: {method}")
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            raise MCPProtocolError(f"Request failed: {str(e)}")
    
    async def discover_tools(self) -> List[ToolDefinition]:
        """
        发现MCP服务器上的工具
        
        Returns:
            工具定义列表
        """
        try:
            logger.info(f"Discovering tools from MCP server: {self.server_name}")
            response = await self._send_request("tools/list", {})
            
            tools = []
            if isinstance(response, dict) and "tools" in response:
                tool_list = response["tools"]
            elif isinstance(response, list):
                tool_list = response
            else:
                logger.warning(f"Unexpected response format from tools/list: {response}")
                return []
            
            for tool_data in tool_list:
                try:
                    tool_def = self._parse_tool_definition(tool_data)
                    if tool_def:
                        tools.append(tool_def)
                except Exception as e:
                    logger.warning(f"Failed to parse tool definition: {e}, tool_data: {tool_data}")
            
            logger.info(f"Discovered {len(tools)} tools from {self.server_name}")
            return tools
            
        except Exception as e:
            logger.error(f"Failed to discover tools from {self.server_name}: {e}")
            raise
    
    def _parse_tool_definition(self, tool_data: Dict[str, Any]) -> Optional[ToolDefinition]:
        """
        解析工具定义
        
        Args:
            tool_data: 工具数据字典
            
        Returns:
            ToolDefinition对象
        """
        try:
            # 提取基本信息
            name = tool_data.get("name", "")
            if not name:
                return None
            
            description = tool_data.get("description", "")
            input_schema = tool_data.get("inputSchema", {})
            
            # 解析参数
            parameters = input_schema if isinstance(input_schema, dict) else {}
            required_parameters = parameters.get("required", [])
            
            # 解析返回类型
            returns = None
            if "outputSchema" in tool_data:
                returns = tool_data["outputSchema"]
            
            # 创建工具定义
            tool_def = ToolDefinition(
                name=name,
                description=description,
                version=tool_data.get("version", "1.0.0"),
                tool_type=ToolType.FUNCTION,  # MCP工具默认是函数类型
                status=ToolStatus.ACTIVE,
                parameters=parameters,
                required_parameters=required_parameters,
                returns=returns,
                metadata={
                    "source": f"mcp:{self.server_name}",
                    "mcp_server": self.server_name,
                    "discovered_at": datetime.now().isoformat()
                }
            )
            
            return tool_def
            
        except Exception as e:
            logger.error(f"Error parsing tool definition: {e}")
            return None
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Any:
        """
        执行MCP工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            timeout: 执行超时时间（秒）
            
        Returns:
            执行结果
        """
        try:
            logger.info(f"Executing tool '{tool_name}' on MCP server: {self.server_name}")
            
            # 保存原始超时时间
            original_timeout = self.timeout
            if timeout:
                self.timeout = timeout
            
            try:
                response = await self._send_request(
                    "tools/call",
                    {
                        "name": tool_name,
                        "arguments": parameters
                    }
                )
                
                # 提取结果
                if isinstance(response, dict):
                    result = response.get("content", response.get("result", response))
                else:
                    result = response
                
                logger.info(f"Tool '{tool_name}' executed successfully on {self.server_name}")
                return result
                
            finally:
                # 恢复原始超时时间
                self.timeout = original_timeout
                
        except Exception as e:
            logger.error(f"Failed to execute tool '{tool_name}' on {self.server_name}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        检查MCP服务器健康状态
        
        Returns:
            是否健康
        """
        try:
            # 发送ping请求
            await self._send_request("ping", {})
            return True
        except Exception:
            return False
    
    async def close(self):
        """关闭MCP连接"""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info(f"Closed connection to MCP server: {self.server_name}")
            except Exception as e:
                logger.error(f"Error closing connection to {self.server_name}: {e}")
            finally:
                self.websocket = None
                self.connected = False
        
        # 取消所有待处理的请求
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()


class MCPConnectionPool:
    """MCP连接池 - 管理多个MCP客户端连接（支持WebSocket和HTTP）"""
    
    def __init__(self):
        self._clients: Dict[str, Any] = {}  # 可以是 MCPClient 或 MCPHTTPClient
        self._server_configs: List[Dict[str, Any]] = []
    
    async def add_server(self, server_config: Dict[str, Any]) -> bool:
        """
        添加MCP服务器到连接池
        
        Args:
            server_config: 服务器配置字典，包含：
                - name: 服务器名称
                - url: WebSocket URL 或 HTTP URL
                - transport: 传输类型（"websocket" 或 "http"，默认自动检测）
                - timeout: 超时时间（可选）
                - auto_connect: 是否自动连接（可选）
        
        Returns:
            是否添加成功
        """
        server_name = server_config.get("name", f"mcp_{len(self._clients)}")
        server_url = server_config.get("url", "")
        transport = server_config.get("transport", "auto")  # auto, websocket, http
        
        if not server_url:
            logger.error(f"Invalid server config: missing URL for {server_name}")
            return False
        
        if server_name in self._clients:
            logger.warning(f"Server {server_name} already exists, replacing...")
            await self.remove_server(server_name)
        
        timeout = server_config.get("timeout", 30)
        
        # 自动检测传输类型
        if transport == "auto":
            if server_url.startswith("ws://") or server_url.startswith("wss://"):
                transport = "websocket"
            elif server_url.startswith("http://") or server_url.startswith("https://"):
                transport = "http"
            else:
                # 默认尝试 WebSocket
                transport = "websocket"
        
        # 根据传输类型创建客户端
        if transport == "http":
            from .mcp_http_client import MCPHTTPClient
            client = MCPHTTPClient(server_url, timeout, server_name)
        else:
            client = MCPClient(server_url, timeout, server_name)
        
        self._clients[server_name] = client
        self._server_configs.append(server_config)
        
        # 自动连接
        if server_config.get("auto_connect", True):
            connected = await client.connect()
            if not connected:
                logger.warning(f"Failed to auto-connect to {server_name}")
                return False
        
        return True
    
    async def remove_server(self, server_name: str) -> bool:
        """
        从连接池移除服务器
        
        Args:
            server_name: 服务器名称
        
        Returns:
            是否移除成功
        """
        if server_name in self._clients:
            client = self._clients[server_name]
            await client.close()
            del self._clients[server_name]
            
            # 从配置列表中移除
            self._server_configs = [c for c in self._server_configs if c.get("name") != server_name]
            
            logger.info(f"Removed MCP server: {server_name}")
            return True
        
        return False
    
    def get_client(self, server_name: str) -> Optional[Any]:
        """获取MCP客户端（支持WebSocket和HTTP）"""
        return self._clients.get(server_name)
    
    async def discover_all_tools(self) -> List[ToolDefinition]:
        """
        从所有MCP服务器发现工具
        
        Returns:
            所有工具定义列表
        """
        all_tools = []
        
        for server_name, client in self._clients.items():
            if client.connected:
                try:
                    tools = await client.discover_tools()
                    all_tools.extend(tools)
                except Exception as e:
                    logger.error(f"Failed to discover tools from {server_name}: {e}")
        
        return all_tools
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        检查所有服务器的健康状态
        
        Returns:
            服务器名称到健康状态的映射
        """
        health_status = {}
        
        for server_name, client in self._clients.items():
            try:
                health_status[server_name] = await client.health_check()
            except Exception:
                health_status[server_name] = False
        
        return health_status
    
    async def close_all(self):
        """关闭所有连接"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
        self._server_configs.clear()
        logger.info("Closed all MCP connections")

