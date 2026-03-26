"""
MCP HTTP客户端实现（支持 Streamable HTTP/SSE 传输）
用于连接使用 HTTP SSE 传输的 MCP 服务器（如 SAP MCP Server）
"""
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None
    logger.warning("httpx not available, HTTP MCP client will not work")

from ..models.tool_models import ToolDefinition, ToolType, ToolStatus


class MCPHTTPConnectionError(Exception):
    """MCP HTTP连接错误"""
    pass


class MCPHTTPProtocolError(Exception):
    """MCP HTTP协议错误"""
    pass


class MCPHTTPClient:
    """MCP HTTP客户端 - 连接使用 HTTP SSE 传输的 MCP 服务器"""
    
    def __init__(self, server_url: str, timeout: int = 30, server_name: str = ""):
        """
        初始化MCP HTTP客户端
        
        Args:
            server_url: MCP服务器HTTP URL（例如：http://sap-mcp-server:3000/mcp）
            timeout: 连接和请求超时时间（秒）
            server_name: 服务器名称（用于日志和标识）
        """
        self.server_url = server_url.rstrip('/')
        if not self.server_url.endswith('/mcp'):
            self.server_url = f"{self.server_url}/mcp"
        
        self.timeout = timeout
        self.server_name = server_name or server_url
        self.http_client = None
        self.connected = False
        self._request_id = 0
        self._session_id: Optional[str] = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3
        self._reconnect_delay = 1.0
    
    async def connect(self) -> bool:
        """
        连接到MCP服务器（初始化会话）
        
        Returns:
            是否连接成功
        """
        if not HTTPX_AVAILABLE or httpx is None:
            logger.error("httpx library not available, cannot connect to MCP HTTP server")
            return False
        
        try:
            # 创建 httpx 客户端，设置更长的超时时间
            timeout_config = httpx.Timeout(
                connect=10.0,  # 连接超时 10 秒
                read=self.timeout,  # 读取超时使用配置的值
                write=10.0,  # 写入超时 10 秒
                pool=5.0  # 连接池超时 5 秒
            )
            self.http_client = httpx.AsyncClient(timeout=timeout_config)
            
            # 初始化会话 - 发送 initialize 请求创建session
            logger.info(f"Connecting to MCP HTTP server: {self.server_url}")
            
            # 发送 initialize 请求
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-gateway",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self.http_client.post(
                self.server_url,
                json=initialize_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            if response.status_code == 200:
                try:
                    # 检查是否是 SSE 格式响应
                    response_text = response.text
                    if response_text.startswith("event:") or "event: message" in response_text:
                        # 解析 SSE 格式：event: message\ndata: {...}
                        lines = response_text.split('\n')
                        json_data = None
                        for line in lines:
                            if line.startswith('data: '):
                                json_data = line[6:]  # 移除 "data: " 前缀
                                break
                        if json_data:
                            result = json.loads(json_data)
                        else:
                            logger.error(f"Failed to find data in SSE response: {response_text[:200]}")
                            return False
                    else:
                        # 普通 JSON 响应
                        result = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}, response text: {response.text[:200]}")
                    return False
                
                # 从响应头中获取session ID（如果有）
                session_id = response.headers.get("Mcp-Session-Id") or response.headers.get("mcp-session-id")
                if session_id:
                    self._session_id = session_id
                    logger.info(f"Got session ID from response: {session_id}")
                
                # 尝试从响应中获取会话ID（如果有）
                try:
                    server_info = result.get("result", {})
                    logger.info(f"Connected to MCP HTTP server: {self.server_name}, info: {server_info.get('serverInfo', {}).get('name', 'unknown')}")
                except:
                    logger.info(f"Connected to MCP HTTP server: {self.server_name}")
                
                self.connected = True
                self._reconnect_attempts = 0
                return True
            else:
                logger.error(f"Failed to connect to MCP HTTP server: {response.status_code}, {response.text[:500]}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP HTTP server {self.server_url}: {e}")
            return False
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Any:
        """
        发送JSON-RPC请求到MCP服务器（通过HTTP POST）
        
        Args:
            method: 方法名
            params: 参数
            
        Returns:
            响应结果
            
        Raises:
            MCPHTTPConnectionError: 如果未连接
            MCPHTTPProtocolError: 如果协议错误
        """
        # 如果未连接，尝试自动重连
        if not self.connected or not self.http_client:
            logger.warning(f"Not connected to MCP HTTP server {self.server_name}, attempting to reconnect...")
            connected = await self.connect()
            if not connected:
                raise MCPHTTPConnectionError(f"Not connected to MCP HTTP server: {self.server_name}")
        
        self._request_id += 1
        request_id = self._request_id
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            
            # 如果有session ID，添加到请求头
            if self._session_id:
                headers["mcp-session-id"] = self._session_id
            
            # 发送POST请求到 /mcp 端点
            response = await self.http_client.post(
                self.server_url,
                json=request,
                headers=headers
            )
            
            if response.status_code == 401 or response.status_code == 403:
                # 认证错误，可能需要重新连接
                logger.warning(f"Authentication error ({response.status_code}), marking as disconnected")
                self.connected = False
                raise MCPHTTPConnectionError(f"Authentication failed: {response.status_code}")
            elif response.status_code != 200:
                raise MCPHTTPProtocolError(f"HTTP error {response.status_code}: {response.text}")
            
            # 解析响应（支持 SSE 格式）
            response_text = response.text
            if response_text.startswith("event:") or "event: message" in response_text:
                # 解析 SSE 格式：event: message\ndata: {...}
                lines = response_text.split('\n')
                json_data = None
                for line in lines:
                    if line.startswith('data: '):
                        json_data = line[6:]  # 移除 "data: " 前缀
                        break
                if json_data:
                    result = json.loads(json_data)
                else:
                    raise MCPHTTPProtocolError(f"Failed to find data in SSE response: {response_text[:200]}")
            else:
                # 普通 JSON 响应
                result = response.json()
            
            # 检查是否有错误
            if "error" in result:
                error = result["error"]
                raise MCPHTTPProtocolError(f"MCP error: {error.get('message', 'Unknown error')}")
            
            # 返回结果
            return result.get("result")
            
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout to {self.server_url}: {e}")
            raise MCPHTTPProtocolError(f"Request timeout: {method}")
        except httpx.ConnectError as e:
            logger.error(f"Connection error to {self.server_url}: {e}")
            # 标记为未连接，下次请求时会自动重连
            self.connected = False
            raise MCPHTTPConnectionError(f"Connection failed: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Request error to {self.server_url}: {e}")
            # 标记为未连接，下次请求时会自动重连
            self.connected = False
            raise MCPHTTPConnectionError(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise MCPHTTPProtocolError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            raise MCPHTTPProtocolError(f"Request failed: {str(e)}")
    
    async def discover_tools(self) -> List[ToolDefinition]:
        """
        发现MCP服务器上的工具
        
        Returns:
            工具定义列表
        """
        try:
            logger.info(f"Discovering tools from MCP HTTP server: {self.server_name}")
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
                    "source": f"mcp-http:{self.server_name}",
                    "mcp_server": self.server_name,
                    "transport": "http",
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
            logger.info(f"Executing tool '{tool_name}' on MCP HTTP server: {self.server_name}")
            
            # 保存原始超时时间
            original_timeout = self.timeout
            if timeout:
                self.timeout = timeout
                if self.http_client:
                    self.http_client.timeout = httpx.Timeout(timeout)
            
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
                    # MCP 工具调用响应格式：{ "content": [...] }
                    if "content" in response:
                        content = response["content"]
                        if isinstance(content, list) and len(content) > 0:
                            # 提取第一个内容项
                            first_content = content[0]
                            if isinstance(first_content, dict) and "text" in first_content:
                                result = first_content["text"]
                            else:
                                result = first_content
                        else:
                            result = content
                    else:
                        result = response.get("result", response)
                else:
                    result = response
                
                logger.info(f"Tool '{tool_name}' executed successfully on {self.server_name}")
                return result
                
            finally:
                # 恢复原始超时时间
                self.timeout = original_timeout
                if self.http_client:
                    self.http_client.timeout = httpx.Timeout(original_timeout)
                
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
            # 尝试获取服务器信息
            if self.http_client:
                health_url = self.server_url.replace('/mcp', '/health')
                response = await self.http_client.get(health_url, timeout=5.0)
                return response.status_code == 200
            return False
        except Exception:
            return False
    
    async def close(self):
        """关闭MCP连接"""
        if self.http_client:
            try:
                # 如果支持会话删除，发送 DELETE 请求
                if self._session_id:
                    try:
                        await self.http_client.delete(self.server_url)
                    except:
                        pass
                
                await self.http_client.aclose()
                logger.info(f"Closed connection to MCP HTTP server: {self.server_name}")
            except Exception as e:
                logger.error(f"Error closing connection to {self.server_name}: {e}")
            finally:
                self.http_client = None
                self.connected = False






