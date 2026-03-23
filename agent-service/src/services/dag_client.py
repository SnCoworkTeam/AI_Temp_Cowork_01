"""
DAG Orchestrator客户端
用于任务分解和DAG执行
"""
import logging
import httpx
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class DAGClient:
    """DAG Orchestrator客户端"""
    
    def __init__(self):
        self.base_url = os.getenv("DAG_ORCHESTRATOR_URL", "http://dag-orchestrator:8009")
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
    
    async def decompose_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        分解任务为子任务
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            任务分解结果
        """
        try:
            payload = {
                "user_input": task  # DAG orchestrator API期望user_input字段
            }
            
            if context:
                payload["context"] = context
            
            # 检查API路径：可能是/api/v1/tasks/decompose或/api/v1/dag/decompose
            try:
                response = await self.http_client.post(
                    f"{self.base_url}/api/v1/tasks/decompose",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError:
                # 尝试备用路径
                response = await self.http_client.post(
                    f"{self.base_url}/api/v1/dag/decompose",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")
            return None
    
    async def execute_dag(
        self,
        dag_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行DAG
        
        Args:
            dag_id: DAG ID
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            执行结果
        """
        try:
            payload = {
                "dag_id": dag_id,
                "input": input_data
            }
            
            if context:
                payload["context"] = context
            
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/dag/{dag_id}/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"DAG execution failed: HTTP {e.response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"DAG execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 全局DAG客户端实例
dag_client = DAGClient()




