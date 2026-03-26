"""
MCP工具元数据采集器
从mcp-gateway服务采集工具元数据
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import httpx

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class MCPToolCollector(BaseCollector):
    """MCP工具元数据采集器"""
    
    def __init__(self, mcp_gateway_url: str = "http://mcp-gateway:8001", **kwargs):
        """
        初始化MCP工具采集器
        
        Args:
            mcp_gateway_url: MCP Gateway服务URL
            **kwargs: 其他参数传递给BaseCollector
        """
        super().__init__(
            source_service_url=mcp_gateway_url,
            **kwargs
        )
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        从MCP Gateway采集工具元数据
        
        Returns:
            工具元数据列表
        """
        try:
            client = await self._get_source_client()
            
            # 获取所有工具列表
            response = await client.get("/api/tools")
            response.raise_for_status()
            
            tools_data = response.json()
            tools = tools_data.get("tools", []) if isinstance(tools_data, dict) else tools_data
            
            metadata_list = []
            for tool in tools:
                try:
                    # 转换工具信息为元数据格式
                    tool_metadata = {
                        "workflow_id": f"tool_{tool.get('name', '')}",
                        "name": tool.get("name", ""),
                        "display_name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "version": tool.get("version", "1.0.0"),
                        "category": "tool",
                        "workflow_type": "tool",
                        "input_schema": tool.get("parameters", {}),
                        "output_schema": tool.get("returns", {}),
                        "dependencies": {
                            "tools": []
                        },
                        "tags": tool.get("metadata", {}).get("tags", []),
                        "metadata": {
                            "tool_type": tool.get("tool_type", ""),
                            "status": tool.get("status", ""),
                            "registered_at": tool.get("registered_at"),
                            **tool.get("metadata", {})
                        }
                    }
                    metadata_list.append(tool_metadata)
                except Exception as e:
                    logger.warning(f"Failed to process tool {tool.get('name', 'unknown')}: {str(e)}")
                    continue
            
            return metadata_list
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to collect tools from MCP Gateway: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Error collecting tools: {str(e)}", exc_info=True)
            return []
    
    async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步工具元数据到元数据服务
        
        Args:
            metadata_list: 工具元数据列表
            
        Returns:
            同步结果统计
        """
        client = await self._get_metadata_client()
        synced = 0
        errors = 0
        
        for metadata in metadata_list:
            try:
                workflow_id = metadata.get("workflow_id")
                
                # 检查是否已存在
                check_response = await client.get(f"/api/workflows/{workflow_id}")
                if check_response.status_code == 200:
                    # 更新现有记录
                    response = await client.put(f"/api/workflows/{workflow_id}", json=metadata)
                else:
                    # 创建新记录
                    response = await client.post("/api/workflows", json=metadata)
                
                response.raise_for_status()
                synced += 1
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to sync tool {metadata.get('name', 'unknown')}: {e.response.status_code} - {e.response.text}")
                errors += 1
            except Exception as e:
                logger.error(f"Error syncing tool {metadata.get('name', 'unknown')}: {str(e)}")
                errors += 1
        
        return {
            "success": errors == 0,
            "collected": len(metadata_list),
            "synced": synced,
            "errors": errors,
            "message": f"Synced {synced}/{len(metadata_list)} tools"
        }

