"""
元数据服务客户端
用于与metadata-service通信，管理工具元数据
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from httpx import AsyncClient, Timeout

from ..config import settings
from ..models.tool_metadata import ToolMetadata, ToolMetadataCreate, ToolMetadataUpdate

logger = logging.getLogger(__name__)


class MetadataClient:
    """元数据服务客户端"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        """
        初始化元数据服务客户端
        
        Args:
            base_url: 元数据服务基础URL，如果为None则从配置读取
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or getattr(settings, 'METADATA_SERVICE_URL', 'http://metadata-service:8005')
        self.timeout = Timeout(timeout)
        self._client: Optional[AsyncClient] = None
    
    async def _get_client(self) -> AsyncClient:
        """获取HTTP客户端（懒加载）"""
        if self._client is None:
            self._client = AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
        return self._client
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def create_tool_metadata(
        self,
        tool_metadata: ToolMetadataCreate
    ) -> Optional[Dict[str, Any]]:
        """
        创建工具元数据
        
        Args:
            tool_metadata: 工具元数据
            
        Returns:
            创建结果，如果失败返回None
        """
        try:
            client = await self._get_client()
            
            # 将工具元数据转换为工作流元数据格式（因为metadata-service使用workflow_metadata表）
            payload = {
                "workflow_id": f"tool_{tool_metadata.tool_name}",
                "name": tool_metadata.tool_name,
                "display_name": tool_metadata.tool_name,
                "description": tool_metadata.description,
                "status": "active",
                "category": tool_metadata.category,
                "workflow_type": "tool",
                "input_schema": tool_metadata.input_schema,
                "output_schema": tool_metadata.output_schema,
                "dependencies": {
                    "tools": tool_metadata.dependencies or []
                },
                "tags": tool_metadata.tags or [],
                "metadata": {
                    "usage_statistics": tool_metadata.usage_statistics or {},
                    "performance_metrics": tool_metadata.performance_metrics or {},
                    "quality_metrics": tool_metadata.quality_metrics or {},
                    "version": tool_metadata.version,
                    "author": tool_metadata.author,
                    **{k: v for k, v in (tool_metadata.metadata or {}).items()}
                }
            }
            
            response = await client.post("/api/workflows", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Tool metadata created for {tool_metadata.tool_name}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create tool metadata: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating tool metadata: {str(e)}", exc_info=True)
            return None
    
    async def update_tool_metadata(
        self,
        tool_name: str,
        tool_metadata: ToolMetadataUpdate
    ) -> Optional[Dict[str, Any]]:
        """
        更新工具元数据
        
        Args:
            tool_name: 工具名称
            tool_metadata: 工具元数据更新
            
        Returns:
            更新结果，如果失败返回None
        """
        try:
            client = await self._get_client()
            workflow_id = f"tool_{tool_name}"
            
            # 构建更新payload
            payload = {}
            if tool_metadata.description is not None:
                payload["description"] = tool_metadata.description
            if tool_metadata.category is not None:
                payload["category"] = tool_metadata.category
            if tool_metadata.input_schema is not None:
                payload["input_schema"] = tool_metadata.input_schema
            if tool_metadata.output_schema is not None:
                payload["output_schema"] = tool_metadata.output_schema
            if tool_metadata.dependencies is not None:
                payload["dependencies"] = {"tools": tool_metadata.dependencies}
            if tool_metadata.tags is not None:
                payload["tags"] = tool_metadata.tags
            
            # 更新metadata字段
            metadata_updates = {}
            if tool_metadata.usage_statistics is not None:
                metadata_updates["usage_statistics"] = tool_metadata.usage_statistics
            if tool_metadata.performance_metrics is not None:
                metadata_updates["performance_metrics"] = tool_metadata.performance_metrics
            if tool_metadata.quality_metrics is not None:
                metadata_updates["quality_metrics"] = tool_metadata.quality_metrics
            if tool_metadata.version is not None:
                metadata_updates["version"] = tool_metadata.version
            if tool_metadata.author is not None:
                metadata_updates["author"] = tool_metadata.author
            if tool_metadata.metadata is not None:
                metadata_updates.update(tool_metadata.metadata)
            
            if metadata_updates:
                payload["metadata"] = metadata_updates
            
            response = await client.put(f"/api/workflows/{workflow_id}", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Tool metadata updated for {tool_name}")
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Tool metadata not found for {tool_name}")
            else:
                logger.error(f"Failed to update tool metadata: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error updating tool metadata: {str(e)}", exc_info=True)
            return None
    
    async def get_tool_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具元数据
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具元数据，如果不存在返回None
        """
        try:
            client = await self._get_client()
            workflow_id = f"tool_{tool_name}"
            
            response = await client.get(f"/api/workflows/{workflow_id}")
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Retrieved tool metadata for {tool_name}")
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Tool metadata not found for {tool_name}")
            else:
                logger.error(f"Failed to get tool metadata: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error getting tool metadata: {str(e)}", exc_info=True)
            return None
    
    async def delete_tool_metadata(self, tool_name: str) -> bool:
        """
        删除工具元数据
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否删除成功
        """
        try:
            client = await self._get_client()
            workflow_id = f"tool_{tool_name}"
            
            response = await client.delete(f"/api/workflows/{workflow_id}")
            response.raise_for_status()
            
            logger.info(f"Tool metadata deleted for {tool_name}")
            return True
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Tool metadata not found for {tool_name}")
                return True  # 不存在也算成功
            else:
                logger.error(f"Failed to delete tool metadata: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error deleting tool metadata: {str(e)}", exc_info=True)
            return False
    
    async def update_usage_statistics(
        self,
        tool_name: str,
        statistics: Dict[str, Any]
    ) -> bool:
        """
        更新工具使用统计
        
        Args:
            tool_name: 工具名称
            statistics: 统计数据
            
        Returns:
            是否更新成功
        """
        update = ToolMetadataUpdate(
            usage_statistics=statistics
        )
        result = await self.update_tool_metadata(tool_name, update)
        return result is not None
    
    async def update_performance_metrics(
        self,
        tool_name: str,
        metrics: Dict[str, Any]
    ) -> bool:
        """
        更新工具性能指标
        
        Args:
            tool_name: 工具名称
            metrics: 性能指标
            
        Returns:
            是否更新成功
        """
        update = ToolMetadataUpdate(
            performance_metrics=metrics
        )
        result = await self.update_tool_metadata(tool_name, update)
        return result is not None
    
    async def update_quality_metrics(
        self,
        tool_name: str,
        metrics: Dict[str, Any]
    ) -> bool:
        """
        更新工具质量指标
        
        Args:
            tool_name: 工具名称
            metrics: 质量指标
            
        Returns:
            是否更新成功
        """
        update = ToolMetadataUpdate(
            quality_metrics=metrics
        )
        result = await self.update_tool_metadata(tool_name, update)
        return result is not None


# 全局客户端实例（单例）
_metadata_client: Optional[MetadataClient] = None


def get_metadata_client() -> MetadataClient:
    """获取元数据客户端实例（单例）"""
    global _metadata_client
    if _metadata_client is None:
        _metadata_client = MetadataClient()
    return _metadata_client


async def close_metadata_client():
    """关闭元数据客户端"""
    global _metadata_client
    if _metadata_client:
        await _metadata_client.close()
        _metadata_client = None
