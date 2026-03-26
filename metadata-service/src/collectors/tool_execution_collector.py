"""
工具执行元数据采集器
从mcp-gateway采集工具执行统计和模式元数据
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class ToolExecutionCollector(BaseCollector):
    """工具执行元数据采集器"""
    
    def __init__(self, mcp_gateway_url: str = "http://mcp-gateway:8001", **kwargs):
        """
        初始化工具执行采集器
        
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
        从MCP Gateway采集工具执行元数据
        
        Returns:
            工具执行元数据列表
        """
        try:
            client = await self._get_source_client()
            
            # 获取工具执行统计
            # TODO: 需要mcp-gateway提供执行统计API
            # 可能的API端点：
            # - /api/tools/executions/stats
            # - /api/tools/{tool_id}/executions
            
            metadata_list = []
            
            # 获取所有工具的执行统计
            stats_response = await client.get("/api/tools/stats")
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                tools_stats = stats_data.get("tools", [])
                
                for tool_stats in tools_stats:
                    metadata_list.append({
                        "tool_name": tool_stats.get("tool_name", ""),
                        "tool_id": tool_stats.get("tool_id", ""),
                        "execution_count": tool_stats.get("total_executions", 0),
                        "success_count": tool_stats.get("successful_executions", 0),
                        "failure_count": tool_stats.get("failed_executions", 0),
                        "average_execution_time": tool_stats.get("average_execution_time", 0.0),
                        "success_rate": tool_stats.get("success_rate", 0.0),
                        "last_execution_time": tool_stats.get("last_execution_time"),
                    })
            else:
                # 如果统计API不存在，尝试逐个获取
                response = await client.get("/api/tools")
                if response.status_code == 200:
                    tools_data = response.json()
                    tools = tools_data.get("tools", []) if isinstance(tools_data, dict) else tools_data
                    
                    for tool in tools:
                        tool_name = tool.get("name", "")
                        if tool_name:
                            try:
                                stats_response = await client.get(f"/api/tools/{tool_name}/stats")
                                if stats_response.status_code == 200:
                                    stats = stats_response.json()
                                    metadata_list.append({
                                        "tool_name": tool_name,
                                        "tool_id": stats.get("tool_id", tool.get("id", "")),
                                        "execution_count": stats.get("total_executions", 0),
                                        "success_count": stats.get("successful_executions", 0),
                                        "failure_count": stats.get("failed_executions", 0),
                                        "average_execution_time": stats.get("average_execution_time", 0.0),
                                        "success_rate": stats.get("success_rate", 0.0),
                                        "last_execution_time": stats.get("last_execution_time"),
                                    })
                            except Exception as e:
                                logger.debug(f"Failed to get stats for tool {tool_name}: {e}")
                                pass
            
            return metadata_list
            
        except Exception as e:
            logger.error(f"Error collecting tool execution metadata: {str(e)}", exc_info=True)
            return []
    
    async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步工具执行元数据到元数据服务
        
        Args:
            metadata_list: 工具执行元数据列表
            
        Returns:
            同步结果统计
        """
        # 更新工具的工作流元数据中的使用统计
        client = await self._get_metadata_client()
        synced = 0
        errors = 0
        
        for metadata in metadata_list:
            try:
                tool_name = metadata.get("tool_name")
                workflow_id = f"tool_{tool_name}"
                
                # 获取现有工作流元数据
                response = await client.get(f"/api/workflows/{workflow_id}")
                
                if response.status_code == 200:
                    workflow = response.json()
                    
                    # 更新使用统计
                    update_data = {
                        "execution_count": metadata.get("execution_count", 0),
                        "metadata": {
                            **workflow.get("metadata", {}),
                            "usage_statistics": {
                                "total_calls": metadata.get("execution_count", 0),
                                "successful_calls": metadata.get("success_count", 0),
                                "failed_calls": metadata.get("failure_count", 0),
                                "average_execution_time": metadata.get("average_execution_time", 0.0),
                                "success_rate": metadata.get("success_rate", 0.0),
                                "common_parameters": metadata.get("common_parameters", {}),
                                "error_patterns": metadata.get("error_patterns", []),
                                "last_execution_time": metadata.get("last_execution_time"),
                            }
                        }
                    }
                    
                    update_response = await client.put(
                        f"/api/workflows/{workflow_id}",
                        json=update_data
                    )
                    
                    if update_response.status_code == 200:
                        synced += 1
                    else:
                        errors += 1
                else:
                    # 工具元数据不存在，跳过
                    logger.debug(f"Tool metadata not found for {tool_name}")
                    
            except Exception as e:
                errors += 1
                logger.error(f"Error syncing tool execution metadata: {str(e)}")
        
        return {
            "success": errors == 0,
            "synced": synced,
            "errors": errors,
            "total": len(metadata_list)
        }

