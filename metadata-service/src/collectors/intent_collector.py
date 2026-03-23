"""
用户意图和对话元数据采集器
从agent-service采集用户意图、对话和任务执行元数据
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class IntentCollector(BaseCollector):
    """用户意图和对话元数据采集器"""
    
    def __init__(self, agent_service_url: str = "http://agent-service:8010", **kwargs):
        """
        初始化意图采集器
        
        Args:
            agent_service_url: Agent Service服务URL
            **kwargs: 其他参数传递给BaseCollector
        """
        super().__init__(
            source_service_url=agent_service_url,
            **kwargs
        )
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        从Agent Service采集意图和对话元数据
        
        Returns:
            意图元数据列表
        """
        try:
            client = await self._get_source_client()
            
            # 获取意图历史
            response = await client.get("/api/v1/executions/intents")
            if response.status_code == 200:
                intents = response.json()
                
                metadata_list = []
                for intent in intents:
                    metadata_list.append({
                        "intent_type": intent.get("intent_type", ""),
                        "description": f"用户意图类型: {intent.get('intent_type', '')}",
                        "confidence": intent.get("average_confidence", 0.0),
                        "required_tools": intent.get("required_tools", []),
                        "target_service": max(
                            intent.get("target_services", {}).items(),
                            key=lambda x: x[1]
                        )[0] if intent.get("target_services") else None,
                        "execution_strategy": max(
                            intent.get("execution_strategies", {}).items(),
                            key=lambda x: x[1]
                        )[0] if intent.get("execution_strategies") else None,
                        "usage_count": intent.get("usage_count", 0),
                        "success_rate": intent.get("success_rate", 0.0),
                        "tags": ["intent", intent.get("intent_type", "unknown")],
                        "metadata": {
                            "execution_strategies": intent.get("execution_strategies", {}),
                            "target_services": intent.get("target_services", {}),
                            "required_tools": intent.get("required_tools", [])
                        }
                    })
                
                logger.info(f"Collected {len(metadata_list)} intent metadata records")
                return metadata_list
            else:
                logger.warning(f"Failed to get intents from agent-service: {response.status_code}")
                return []
            
        except Exception as e:
            logger.error(f"Error collecting intent metadata: {str(e)}", exc_info=True)
            return []
    
    async def sync(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        同步意图元数据到元数据服务
        
        Args:
            metadata_list: 意图元数据列表
            
        Returns:
            同步结果统计
        """
        # 意图元数据可以作为业务实体存储
        # entity_type = "intent_pattern" 或 "user_intent"
        client = await self._get_metadata_client()
        synced = 0
        errors = 0
        
        for metadata in metadata_list:
            try:
                # 创建业务实体（意图模式）
                entity_data = {
                    "name": metadata.get("intent_type", ""),
                    "display_name": metadata.get("intent_type", ""),
                    "description": metadata.get("description", ""),
                    "entity_type": "concept",  # 或创建新的类型 "intent"
                    "business_definition": metadata.get("description", ""),
                    "tags": metadata.get("tags", []),
                    "metadata": {
                        "intent_type": metadata.get("intent_type"),
                        "confidence": metadata.get("confidence"),
                        "required_tools": metadata.get("required_tools", []),
                        "target_service": metadata.get("target_service"),
                        "execution_strategy": metadata.get("execution_strategy"),
                        "usage_count": metadata.get("usage_count", 0),
                        "success_rate": metadata.get("success_rate", 0.0),
                        **metadata.get("metadata", {})
                    }
                }
                
                response = await client.post(
                    "/api/v1/business-entities",
                    json=entity_data
                )
                
                if response.status_code in [200, 201]:
                    synced += 1
                else:
                    errors += 1
                    logger.warning(f"Failed to sync intent metadata: {response.status_code}")
                    
            except Exception as e:
                errors += 1
                logger.error(f"Error syncing intent metadata: {str(e)}")
        
        return {
            "success": errors == 0,
            "synced": synced,
            "errors": errors,
            "total": len(metadata_list)
        }

