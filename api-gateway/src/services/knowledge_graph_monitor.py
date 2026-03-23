"""
知识图谱监控服务
提供跨服务的知识图谱统计信息和健康检查
"""
import httpx
import os
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class KnowledgeGraphMonitor:
    """知识图谱监控服务"""
    
    def __init__(self):
        self.knowledge_base_url = os.getenv(
            "KNOWLEDGE_BASE_URL",
            "http://knowledge-base:8004"
        )
        self.metadata_service_url = os.getenv(
            "METADATA_SERVICE_URL",
            "http://metadata-service:8005"
        )
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
    
    async def get_unified_stats(self) -> Dict[str, Any]:
        """
        获取统一统计信息
        
        Returns:
            包含knowledge-base、metadata-service和实体映射统计信息的字典
        """
        stats = {
            "knowledge_base": {},
            "metadata_service": {},
            "entity_mappings": {},
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy"
        }
        
        # 获取knowledge-base统计
        try:
            kb_response = await self.http_client.get(
                f"{self.knowledge_base_url}/api/ontology/concepts",
                params={"limit": 1}
            )
            if kb_response.status_code == 200:
                kb_data = kb_response.json()
                # 尝试获取总数
                total_concepts = 0
                if isinstance(kb_data, dict):
                    total_concepts = kb_data.get("total", kb_data.get("count", 0))
                elif isinstance(kb_data, list):
                    total_concepts = len(kb_data)
                
                stats["knowledge_base"] = {
                    "total_concepts": total_concepts,
                    "status": "healthy",
                    "url": self.knowledge_base_url
                }
            else:
                stats["knowledge_base"] = {
                    "status": "error",
                    "error": f"HTTP {kb_response.status_code}",
                    "url": self.knowledge_base_url
                }
                stats["overall_status"] = "degraded"
        except Exception as e:
            logger.error(f"Failed to get knowledge-base stats: {e}")
            stats["knowledge_base"] = {
                "status": "error",
                "error": str(e),
                "url": self.knowledge_base_url
            }
            stats["overall_status"] = "degraded"
        
        # 获取metadata-service统计
        try:
            ms_response = await self.http_client.get(
                f"{self.metadata_service_url}/api/business-entities",
                params={"limit": 1}
            )
            if ms_response.status_code == 200:
                ms_data = ms_response.json()
                total_entities = 0
                if isinstance(ms_data, dict):
                    total_entities = ms_data.get("total", ms_data.get("count", len(ms_data.get("items", []))))
                elif isinstance(ms_data, list):
                    total_entities = len(ms_data)
                
                stats["metadata_service"] = {
                    "total_entities": total_entities,
                    "status": "healthy",
                    "url": self.metadata_service_url
                }
            else:
                stats["metadata_service"] = {
                    "status": "error",
                    "error": f"HTTP {ms_response.status_code}",
                    "url": self.metadata_service_url
                }
                stats["overall_status"] = "degraded"
        except Exception as e:
            logger.error(f"Failed to get metadata-service stats: {e}")
            stats["metadata_service"] = {
                "status": "error",
                "error": str(e),
                "url": self.metadata_service_url
            }
            stats["overall_status"] = "degraded"
        
        # 获取实体映射统计
        try:
            mapping_response = await self.http_client.get(
                f"{self.metadata_service_url}/api/entity-mapping/mappings",
                params={"limit": 1}
            )
            if mapping_response.status_code == 200:
                mapping_data = mapping_response.json()
                total_mappings = 0
                if isinstance(mapping_data, dict):
                    total_mappings = mapping_data.get("count", 0)
                    if total_mappings == 0 and "mappings" in mapping_data:
                        total_mappings = len(mapping_data.get("mappings", []))
                
                # 获取不同状态的映射数量
                confirmed_count = 0
                pending_count = 0
                rejected_count = 0
                
                try:
                    confirmed_response = await self.http_client.get(
                        f"{self.metadata_service_url}/api/entity-mapping/mappings",
                        params={"status": "confirmed", "limit": 1}
                    )
                    if confirmed_response.status_code == 200:
                        confirmed_data = confirmed_response.json()
                        if isinstance(confirmed_data, dict):
                            confirmed_count = confirmed_data.get("count", 0)
                    
                    pending_response = await self.http_client.get(
                        f"{self.metadata_service_url}/api/entity-mapping/mappings",
                        params={"status": "pending", "limit": 1}
                    )
                    if pending_response.status_code == 200:
                        pending_data = pending_response.json()
                        if isinstance(pending_data, dict):
                            pending_count = pending_data.get("count", 0)
                    
                    rejected_response = await self.http_client.get(
                        f"{self.metadata_service_url}/api/entity-mapping/mappings",
                        params={"status": "rejected", "limit": 1}
                    )
                    if rejected_response.status_code == 200:
                        rejected_data = rejected_response.json()
                        if isinstance(rejected_data, dict):
                            rejected_count = rejected_data.get("count", 0)
                except Exception as e:
                    logger.warning(f"Failed to get mapping status counts: {e}")
                
                stats["entity_mappings"] = {
                    "total_mappings": total_mappings,
                    "confirmed": confirmed_count,
                    "pending": pending_count,
                    "rejected": rejected_count,
                    "status": "healthy"
                }
            else:
                stats["entity_mappings"] = {
                    "status": "error",
                    "error": f"HTTP {mapping_response.status_code}"
                }
                stats["overall_status"] = "degraded"
        except Exception as e:
            logger.error(f"Failed to get entity mapping stats: {e}")
            stats["entity_mappings"] = {
                "status": "error",
                "error": str(e)
            }
            stats["overall_status"] = "degraded"
        
        return stats
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()








