"""
工作流元数据采集器
从workflow-engine服务采集工作流元数据
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import httpx

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class WorkflowCollector(BaseCollector):
    """工作流元数据采集器"""
    
    def __init__(self, workflow_engine_url: str = "http://workflow-engine:8002", **kwargs):
        """
        初始化工作流采集器
        
        Args:
            workflow_engine_url: Workflow Engine服务URL
            **kwargs: 其他参数传递给BaseCollector
        """
        super().__init__(
            source_service_url=workflow_engine_url,
            **kwargs
        )
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        从Workflow Engine采集工作流元数据
        
        Returns:
            工作流元数据列表
        """
        try:
            client = await self._get_source_client()
            
            # 获取所有工作流列表
            response = await client.get("/api/workflows")
            response.raise_for_status()
            
            workflows_data = response.json()
            workflows = workflows_data.get("workflows", []) if isinstance(workflows_data, dict) else workflows_data
            
            metadata_list = []
            for workflow in workflows:
                try:
                    workflow_id = workflow.get("workflow_id") or workflow.get("id", "")
                    workflow_name = workflow.get("name", workflow.get("workflow_name", ""))
                    
                    # 获取工作流详情（如果可用）
                    detail_metadata = {}
                    try:
                        detail_response = await client.get(f"/api/workflows/{workflow_id}")
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            detail_metadata = detail_data.get("workflow", {})
                    except:
                        pass
                    
                    # 转换工作流信息为元数据格式
                    workflow_metadata = {
                        "workflow_id": workflow_id,
                        "name": workflow_name,
                        "display_name": workflow_name,
                        "description": workflow.get("description", detail_metadata.get("description", "")),
                        "version": workflow.get("version", detail_metadata.get("version", "1.0.0")),
                        "category": workflow.get("category", "workflow"),
                        "workflow_type": workflow.get("workflow_type", "business_process"),
                        "definition": detail_metadata.get("definition", workflow.get("definition", {})),
                        "input_schema": detail_metadata.get("input_schema", {}),
                        "output_schema": detail_metadata.get("output_schema", {}),
                        "execution_count": workflow.get("execution_count", detail_metadata.get("execution_count", 0)),
                        "last_execution_time": workflow.get("last_executed_at", detail_metadata.get("last_executed_at")),
                        "dependencies": {
                            "data_sources": [],
                            "ai_models": []
                        },
                        "tags": workflow.get("tags", []),
                        "metadata": {
                            "created_at": workflow.get("created_at", detail_metadata.get("created_at")),
                            "updated_at": workflow.get("updated_at", detail_metadata.get("updated_at")),
                            **workflow.get("metadata", {})
                        }
                    }
                    metadata_list.append(workflow_metadata)
                except Exception as e:
                    logger.warning(f"Failed to process workflow {workflow.get('name', 'unknown')}: {str(e)}")
                    continue
            
            return metadata_list
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to collect workflows: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Error collecting workflows: {str(e)}", exc_info=True)
            return []
    
    async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步工作流元数据到元数据服务
        
        Args:
            metadata_list: 工作流元数据列表
            
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
                logger.error(f"Failed to sync workflow {metadata.get('name', 'unknown')}: {e.response.status_code} - {e.response.text}")
                errors += 1
            except Exception as e:
                logger.error(f"Error syncing workflow {metadata.get('name', 'unknown')}: {str(e)}")
                errors += 1
        
        return {
            "success": errors == 0,
            "collected": len(metadata_list),
            "synced": synced,
            "errors": errors,
            "message": f"Synced {synced}/{len(metadata_list)} workflows"
        }

