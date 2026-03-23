"""
AI模型元数据采集器
从各种来源采集AI模型元数据
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from .base_collector import BaseCollector
from .workflow_collector import WorkflowCollector

logger = logging.getLogger(__name__)


class ModelCollector(BaseCollector):
    """AI模型元数据采集器"""
    
    def __init__(
        self,
        model_registry_url: Optional[str] = None,
        **kwargs
    ):
        """
        初始化模型采集器
        
        Args:
            model_registry_url: 模型注册表服务URL（可选）
            **kwargs: 其他参数传递给BaseCollector
        """
        # 如果没有提供源服务URL，使用默认值
        source_url = model_registry_url or "http://localhost:8000"
        super().__init__(
            source_service_url=source_url,
            **kwargs
        )
        self.model_registry_url = model_registry_url
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        采集AI模型元数据
        
        可以从多个来源采集：
        1. 模型注册表服务
        2. 工作流中使用的模型
        3. 配置文件中的模型定义
        
        Returns:
            模型元数据列表
        """
        metadata_list = []
        
        # 方法1: 从工作流中提取使用的模型
        try:
            workflow_collector = WorkflowCollector(
                workflow_engine_url="http://workflow-engine:8002",
                metadata_service_url=self.metadata_service_url
            )
            workflows = await workflow_collector.collect()
            
            # 从工作流元数据中提取AI模型
            for workflow in workflows:
                metadata = workflow.get("metadata", {})
                ai_models = metadata.get("ai_models_used", [])
                
                for model_name in ai_models:
                    model_metadata = {
                        "name": model_name,
                        "display_name": model_name,
                        "description": f"AI model used in workflow {workflow.get('name', '')}",
                        "model_type": "llm",  # 默认类型
                        "status": "active",
                        "deployment_endpoint": "",
                        "tags": ["workflow", workflow.get("name", "")],
                        "metadata": {
                            "source": "workflow",
                            "workflow_id": workflow.get("workflow_id"),
                            "workflow_name": workflow.get("name")
                        }
                    }
                    metadata_list.append(model_metadata)
        except Exception as e:
            logger.warning(f"Failed to collect models from workflows: {str(e)}")
        
        # 方法2: 从模型注册表服务采集（如果可用）
        if self.model_registry_url:
            try:
                client = await self._get_source_client()
                response = await client.get("/api/models")
                response.raise_for_status()
                
                models_data = response.json()
                models = models_data.get("models", []) if isinstance(models_data, dict) else models_data
                
                for model in models:
                    try:
                        model_metadata = {
                            "name": model.get("name", ""),
                            "display_name": model.get("display_name", model.get("name", "")),
                            "description": model.get("description", ""),
                            "model_type": model.get("model_type", "llm"),
                            "model_version": model.get("version", "1.0.0"),
                            "framework": model.get("framework", ""),
                            "model_path": model.get("model_path", ""),
                            "training_dataset": model.get("training_dataset", ""),
                            "accuracy": model.get("accuracy"),
                            "precision": model.get("precision"),
                            "recall": model.get("recall"),
                            "f1_score": model.get("f1_score"),
                            "deployment_endpoint": model.get("deployment_endpoint", ""),
                            "status": model.get("status", "active"),
                            "tags": model.get("tags", []),
                            "metadata": model.get("metadata", {})
                        }
                        metadata_list.append(model_metadata)
                    except Exception as e:
                        logger.warning(f"Failed to process model {model.get('name', 'unknown')}: {str(e)}")
                        continue
            except Exception as e:
                logger.warning(f"Failed to collect models from registry: {str(e)}")
        
        return metadata_list
    
    async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步模型元数据到元数据服务
        
        Args:
            metadata_list: 模型元数据列表
            
        Returns:
            同步结果统计
        """
        client = await self._get_metadata_client()
        synced = 0
        errors = 0
        
        for metadata in metadata_list:
            try:
                model_name = metadata.get("name")
                
                # 通过搜索查找现有模型
                search_response = await client.get(
                    "/api/ai-models",
                    params={"search": model_name}
                )
                search_response.raise_for_status()
                existing_models = search_response.json()
                
                if existing_models and len(existing_models) > 0:
                    # 更新现有记录
                    model_id = existing_models[0]["id"]
                    response = await client.put(f"/api/ai-models/{model_id}", json=metadata)
                else:
                    # 创建新记录
                    response = await client.post("/api/ai-models", json=metadata)
                
                response.raise_for_status()
                synced += 1
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to sync model {metadata.get('name', 'unknown')}: {e.response.status_code} - {e.response.text}")
                errors += 1
            except Exception as e:
                logger.error(f"Error syncing model {metadata.get('name', 'unknown')}: {str(e)}")
                errors += 1
        
        return {
            "success": errors == 0,
            "collected": len(metadata_list),
            "synced": synced,
            "errors": errors,
            "message": f"Synced {synced}/{len(metadata_list)} models"
        }

