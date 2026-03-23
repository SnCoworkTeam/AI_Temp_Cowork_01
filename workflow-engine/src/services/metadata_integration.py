"""
元数据集成服务
用于与metadata-service通信，管理工作流元数据
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from httpx import AsyncClient, Timeout

from ..config import settings
from ..models.workflow_metadata import (
    WorkflowMetadata,
    WorkflowMetadataCreate,
    WorkflowMetadataUpdate
)

logger = logging.getLogger(__name__)


class MetadataIntegration:
    """元数据集成服务"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        """
        初始化元数据集成服务
        
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
    
    async def create_workflow_metadata(
        self,
        workflow_metadata: WorkflowMetadataCreate
    ) -> Optional[Dict[str, Any]]:
        """
        创建工作流元数据
        
        Args:
            workflow_metadata: 工作流元数据
            
        Returns:
            创建结果，如果失败返回None
        """
        try:
            client = await self._get_client()
            
            # 构建payload，映射到metadata-service的workflow_metadata格式
            payload = {
                "workflow_id": workflow_metadata.workflow_id,
                "name": workflow_metadata.name,
                "display_name": workflow_metadata.name,
                "description": workflow_metadata.description,
                "version": workflow_metadata.version,
                "category": workflow_metadata.category or workflow_metadata.business_process,
                "workflow_type": "business_process",
                "input_schema": {},  # 可以从工作流定义中提取
                "output_schema": {},  # 可以从工作流定义中提取
                "dependencies": {
                    "data_sources": workflow_metadata.data_sources or [],
                    "ai_models": workflow_metadata.ai_models_used or []
                },
                "data_sources": workflow_metadata.data_sources or [],
                "data_sinks": [],
                "tags": workflow_metadata.tags or [],
                "metadata": {
                    "business_process": workflow_metadata.business_process,
                    "kpis": workflow_metadata.kpis or [],
                    "sla_requirements": workflow_metadata.sla_requirements or {},
                    "execution_statistics": workflow_metadata.execution_statistics or {},
                    "success_rate": workflow_metadata.success_rate,
                    "average_execution_time": workflow_metadata.average_execution_time,
                    **{k: v for k, v in (workflow_metadata.metadata or {}).items()}
                }
            }
            
            response = await client.post("/api/workflows", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Workflow metadata created for {workflow_metadata.workflow_id}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create workflow metadata: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating workflow metadata: {str(e)}", exc_info=True)
            return None
    
    async def update_workflow_metadata(
        self,
        workflow_id: str,
        workflow_metadata: WorkflowMetadataUpdate
    ) -> Optional[Dict[str, Any]]:
        """
        更新工作流元数据
        
        Args:
            workflow_id: 工作流ID
            workflow_metadata: 工作流元数据更新
            
        Returns:
            更新结果，如果失败返回None
        """
        try:
            client = await self._get_client()
            
            # 构建更新payload
            payload = {}
            if workflow_metadata.name is not None:
                payload["display_name"] = workflow_metadata.name
                payload["name"] = workflow_metadata.name
            if workflow_metadata.description is not None:
                payload["description"] = workflow_metadata.description
            if workflow_metadata.version is not None:
                payload["version"] = workflow_metadata.version
            if workflow_metadata.category is not None:
                payload["category"] = workflow_metadata.category
            if workflow_metadata.data_sources is not None:
                payload["data_sources"] = workflow_metadata.data_sources
                if "dependencies" not in payload:
                    payload["dependencies"] = {}
                payload["dependencies"]["data_sources"] = workflow_metadata.data_sources
            if workflow_metadata.tags is not None:
                payload["tags"] = workflow_metadata.tags
            
            # 更新metadata字段
            metadata_updates = {}
            if workflow_metadata.business_process is not None:
                metadata_updates["business_process"] = workflow_metadata.business_process
            if workflow_metadata.kpis is not None:
                metadata_updates["kpis"] = workflow_metadata.kpis
            if workflow_metadata.sla_requirements is not None:
                metadata_updates["sla_requirements"] = workflow_metadata.sla_requirements
            if workflow_metadata.execution_statistics is not None:
                metadata_updates["execution_statistics"] = workflow_metadata.execution_statistics
            if workflow_metadata.success_rate is not None:
                metadata_updates["success_rate"] = workflow_metadata.success_rate
            if workflow_metadata.average_execution_time is not None:
                metadata_updates["average_execution_time"] = workflow_metadata.average_execution_time
            if workflow_metadata.ai_models_used is not None:
                if "dependencies" not in payload:
                    payload["dependencies"] = {}
                payload["dependencies"]["ai_models"] = workflow_metadata.ai_models_used
                metadata_updates["ai_models_used"] = workflow_metadata.ai_models_used
            if workflow_metadata.metadata is not None:
                metadata_updates.update(workflow_metadata.metadata)
            
            if metadata_updates:
                payload["metadata"] = metadata_updates
            
            response = await client.put(f"/api/workflows/{workflow_id}", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Workflow metadata updated for {workflow_id}")
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Workflow metadata not found for {workflow_id}")
            else:
                logger.error(f"Failed to update workflow metadata: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error updating workflow metadata: {str(e)}", exc_info=True)
            return None
    
    async def get_workflow_metadata(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流元数据
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流元数据，如果不存在返回None
        """
        try:
            client = await self._get_client()
            
            response = await client.get(f"/api/workflows/{workflow_id}")
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Retrieved workflow metadata for {workflow_id}")
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Workflow metadata not found for {workflow_id}")
            else:
                logger.error(f"Failed to get workflow metadata: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error getting workflow metadata: {str(e)}", exc_info=True)
            return None
    
    async def delete_workflow_metadata(self, workflow_id: str) -> bool:
        """
        删除工作流元数据
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            是否删除成功
        """
        try:
            client = await self._get_client()
            
            response = await client.delete(f"/api/workflows/{workflow_id}")
            response.raise_for_status()
            
            logger.info(f"Workflow metadata deleted for {workflow_id}")
            return True
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Workflow metadata not found for {workflow_id}")
                return True  # 不存在也算成功
            else:
                logger.error(f"Failed to delete workflow metadata: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error deleting workflow metadata: {str(e)}", exc_info=True)
            return False
    
    async def update_execution_statistics(
        self,
        workflow_id: str,
        statistics: Dict[str, Any]
    ) -> bool:
        """
        更新工作流执行统计
        
        Args:
            workflow_id: 工作流ID
            statistics: 统计数据
            
        Returns:
            是否更新成功
        """
        update = WorkflowMetadataUpdate(
            execution_statistics=statistics
        )
        result = await self.update_workflow_metadata(workflow_id, update)
        return result is not None
    
    async def update_success_rate(
        self,
        workflow_id: str,
        success_rate: float
    ) -> bool:
        """
        更新工作流成功率
        
        Args:
            workflow_id: 工作流ID
            success_rate: 成功率（0.0-1.0）
            
        Returns:
            是否更新成功
        """
        update = WorkflowMetadataUpdate(
            success_rate=success_rate
        )
        result = await self.update_workflow_metadata(workflow_id, update)
        return result is not None
    
    async def update_average_execution_time(
        self,
        workflow_id: str,
        average_execution_time: float
    ) -> bool:
        """
        更新工作流平均执行时间
        
        Args:
            workflow_id: 工作流ID
            average_execution_time: 平均执行时间（秒）
            
        Returns:
            是否更新成功
        """
        update = WorkflowMetadataUpdate(
            average_execution_time=average_execution_time
        )
        result = await self.update_workflow_metadata(workflow_id, update)
        return result is not None


# 全局服务实例（单例）
_metadata_integration: Optional[MetadataIntegration] = None


def get_metadata_integration() -> MetadataIntegration:
    """获取元数据集成服务实例（单例）"""
    global _metadata_integration
    if _metadata_integration is None:
        _metadata_integration = MetadataIntegration()
    return _metadata_integration


async def close_metadata_integration():
    """关闭元数据集成服务"""
    global _metadata_integration
    if _metadata_integration:
        await _metadata_integration.close()
        _metadata_integration = None

