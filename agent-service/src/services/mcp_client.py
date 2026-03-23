"""
MCP Gateway客户端
用于调用工具和执行API
"""
import logging
import httpx
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Gateway客户端"""
    
    def __init__(self):
        self.base_url = os.getenv("MCP_GATEWAY_URL", "http://mcp-gateway:8001")
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用工具列表
        
        Returns:
            工具列表
        """
        try:
            response = await self.http_client.get(f"{self.base_url}/api/tools")
            response.raise_for_status()
            result = response.json()
            
            # 处理不同的响应格式
            if isinstance(result, dict):
                # 如果是字典，可能是 {"tools": [...]} 或 {"items": [...]} 或 ToolListResponse格式
                if "tools" in result:
                    # ToolListResponse格式: {"tools": [...], "total": ..., "page": ..., "page_size": ...}
                    tools = result["tools"]
                    # 确保返回的是字典列表
                    if tools:
                        # 如果是Pydantic模型对象，转换为字典
                        if hasattr(tools[0], 'model_dump'):
                            return [tool.model_dump() for tool in tools]
                        # 如果已经是字典，直接返回
                        elif isinstance(tools[0], dict):
                            return tools
                    return tools if tools else []
                elif "items" in result:
                    return result["items"]
                else:
                    # 如果字典中没有tools或items，返回空列表
                    logger.warning(f"Unexpected response format from /api/tools: {list(result.keys())}")
                    return []
            elif isinstance(result, list):
                # 如果直接是列表，直接返回
                return result
            else:
                logger.warning(f"Unexpected response type from /api/tools: {type(result)}")
                return []
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list tools: HTTP {e.response.status_code} - {e.response.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工具详情
        
        Args:
            tool_id: 工具ID
            
        Returns:
            工具详情
        """
        try:
            response = await self.http_client.get(f"{self.base_url}/api/tools/{tool_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get tool {tool_id}: {e}")
            return None
    
    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            tool_id: 工具ID
            parameters: 工具参数
            context: 上下文信息
            
        Returns:
            执行结果
        """
        try:
            # 构建符合ToolExecutionRequest格式的请求体
            payload = {
                "parameters": parameters
            }
            
            if context:
                payload["context"] = context
            
            response = await self.http_client.post(
                f"{self.base_url}/api/tools/{tool_id}/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Tool execution failed: HTTP {e.response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索工具
        
        Args:
            query: 搜索查询
            
        Returns:
            匹配的工具列表
        """
        try:
            response = await self.http_client.get(
                f"{self.base_url}/api/tools/search",
                params={"q": query}
            )
            response.raise_for_status()
            result = response.json()
            # 处理不同的返回格式
            if isinstance(result, dict) and "tools" in result:
                return result.get("tools", [])
            elif isinstance(result, list):
                return result
            else:
                logger.warning(f"Unexpected tool search response format: {result}")
                return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Tool search endpoint not found (404), tools may not be registered yet")
            else:
                logger.error(f"Tool search failed: HTTP {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Tool search failed: {e}")
            return []


# 全局MCP客户端实例
mcp_client = MCPClient()




