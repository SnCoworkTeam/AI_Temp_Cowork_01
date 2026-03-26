"""
SAP OData MCP服务客户端
专门用于连接SAP OData MCP服务器（不同于MCP Gateway）
"""
import logging
import httpx
import os
import json
from typing import Dict, Any, Optional, List
from urllib.parse import quote

logger = logging.getLogger(__name__)


class SAPODataMCPClient:
    """SAP OData MCP服务客户端"""
    
    def __init__(self, server_url: Optional[str] = None):
        """
        初始化SAP OData MCP客户端
        
        Args:
            server_url: SAP OData MCP服务器URL（默认从环境变量读取）
        """
        self.server_url = server_url or os.getenv(
            "SAP_ODATA_MCP_SERVER_URL", 
            "http://localhost:3000/mcp"
        )
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.session_id: Optional[str] = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """
        初始化MCP会话
        
        Returns:
            是否初始化成功
        """
        try:
            # 发送initialize请求
            response = await self.http_client.post(
                f"{self.server_url}",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "sap-odata-agent",
                            "version": "1.0.0"
                        }
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    # 从响应头或结果中获取session ID
                    self.session_id = response.headers.get("mcp-session-id") or response.headers.get("Mcp-Session-Id")
                    if not self.session_id and "result" in result:
                        # 尝试从结果中获取
                        result_data = result.get("result", {})
                        self.session_id = result_data.get("sessionId")
                    
                    # 发送initialized通知
                    await self.http_client.post(
                        f"{self.server_url}",
                        json={
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "initialized",
                            "params": {}
                        },
                        headers={
                            "Content-Type": "application/json",
                            "mcp-session-id": self.session_id or ""
                        }
                    )
                    
                    self.initialized = True
                    logger.info(f"SAP OData MCP client initialized with session: {self.session_id}")
                    return True
            
            logger.error(f"Failed to initialize SAP OData MCP client: {response.status_code} - {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"Error initializing SAP OData MCP client: {e}", exc_info=True)
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用工具列表
        
        Returns:
            工具列表
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            response = await self.http_client.post(
                f"{self.server_url}",
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/list",
                    "params": {}
                },
                headers={
                    "Content-Type": "application/json",
                    "mcp-session-id": self.session_id or ""
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    tools = result["result"].get("tools", [])
                    return tools
            
            logger.warning(f"Failed to list tools: {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"Error listing tools: {e}", exc_info=True)
            return []
    
    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            执行结果
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            response = await self.http_client.post(
                f"{self.server_url}",
                json={
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": parameters
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "mcp-session-id": self.session_id or ""
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    return result["result"]
                elif "error" in result:
                    logger.error(f"Tool execution error: {result['error']}")
                    return {
                        "success": False,
                        "error": result["error"]
                    }
            
            logger.error(f"Tool execution failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}"
            }
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_services(
        self,
        keyword: str = "",
        category: str = "all"
    ) -> Dict[str, Any]:
        """
        搜索SAP服务
        
        Args:
            keyword: 搜索关键词
            category: 服务类别
            
        Returns:
            服务列表
        """
        return await self.call_tool(
            "search-sap-services",
            {
                "keyword": keyword,
                "category": category
            }
        )
    
    async def discover_entities(
        self,
        service_id: str
    ) -> Dict[str, Any]:
        """
        发现服务实体
        
        Args:
            service_id: 服务ID
            
        Returns:
            实体列表
        """
        return await self.call_tool(
            "discover-service-entities",
            {
                "serviceId": service_id
            }
        )
    
    async def get_entity_schema(
        self,
        service_id: str,
        entity_name: str
    ) -> Dict[str, Any]:
        """
        获取实体schema
        
        Args:
            service_id: 服务ID
            entity_name: 实体名称
            
        Returns:
            实体schema
        """
        return await self.call_tool(
            "get-entity-schema",
            {
                "serviceId": service_id,
                "entityName": entity_name
            }
        )
    
    async def execute_entity_operation(
        self,
        service_id: str,
        entity_name: str,
        operation: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行实体操作
        
        Args:
            service_id: 服务ID
            entity_name: 实体名称
            operation: 操作类型（read/create/update/delete）
            parameters: 操作参数
            
        Returns:
            执行结果
        """
        return await self.call_tool(
            "execute-entity-operation",
            {
                "serviceId": service_id,
                "entityName": entity_name,
                "operation": operation,
                "parameters": parameters
            }
        )
    
    async def close(self):
        """关闭客户端"""
        await self.http_client.aclose()

