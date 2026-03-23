"""
Workflow Engine客户端
用于触发工作流执行
"""
import logging
import httpx
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class WorkflowClient:
    """Workflow Engine客户端"""
    
    def __init__(self):
        self.base_url = os.getenv("WORKFLOW_ENGINE_URL", "http://workflow-engine:8002")
        self.http_client = httpx.AsyncClient(timeout=60.0)  # 工作流可能需要更长时间
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """
        获取工作流列表
        
        Returns:
            工作流列表
        """
        try:
            response = await self.http_client.get(f"{self.base_url}/api/v1/workflows")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流详情
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流详情
        """
        try:
            response = await self.http_client.get(f"{self.base_url}/api/v1/workflows/{workflow_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            return None
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            执行结果
        """
        try:
            payload = {
                "workflow_id": workflow_id,
                "input": input_data
            }
            
            if context:
                payload["context"] = context
            
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/workflows/{workflow_id}/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Workflow execution failed: HTTP {e.response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建工作流
        
        Args:
            workflow_data: 工作流数据
            
        Returns:
            创建的工作流
        """
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/workflows",
                json=workflow_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            return None


# 全局Workflow客户端实例
workflow_client = WorkflowClient()




