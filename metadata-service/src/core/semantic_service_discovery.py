"""
语义服务发现
基于向量相似度匹配服务
"""
import logging
import httpx
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ServiceMatch:
    """服务匹配结果"""
    
    def __init__(
        self,
        service_id: str,
        service_name: str,
        service_type: str,
        similarity_score: float,
        metadata: Dict[str, Any]
    ):
        self.service_id = service_id
        self.service_name = service_name
        self.service_type = service_type
        self.similarity_score = similarity_score
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "service_type": self.service_type,
            "similarity_score": self.similarity_score,
            "metadata": self.metadata
        }


class SemanticServiceDiscovery:
    """语义服务发现 - 利用knowledge-base的向量搜索能力"""
    
    def __init__(self):
        self.knowledge_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://knowledge-base:8004")
        self.timeout = 10.0
        self._http_client = None
    
    async def _get_http_client(self):
        """获取HTTP客户端（延迟初始化）"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client
    
    async def find_semantic_services(
        self,
        user_input: str,
        limit: int = 5,
        min_score: float = 0.3
    ) -> List[ServiceMatch]:
        """
        基于语义相似度查找服务
        
        Args:
            user_input: 用户输入
            limit: 返回结果数量限制
            min_score: 最小相似度分数
            
        Returns:
            服务匹配结果列表
        """
        try:
            # 调用knowledge-base的语义搜索API
            # 假设服务元数据已向量化并存储在knowledge-base的"service_metadata"集合中
            client = await self._get_http_client()
            
            # 构建搜索请求
            search_request = {
                "query": user_input,
                "top_k": limit,
                "min_score": min_score,
                "filters": {
                    "collection": "service_metadata"  # 服务元数据集合
                }
            }
            
            response = await client.post(
                f"{self.knowledge_base_url}/api/search/semantic",
                json=search_request
            )
            
            if response.status_code == 200:
                result = response.json()
                results = result.get("results", [])
                
                # 转换为ServiceMatch对象
                matches = []
                for item in results:
                    metadata = item.get("metadata", {})
                    matches.append(ServiceMatch(
                        service_id=metadata.get("service_id", ""),
                        service_name=metadata.get("service_name", ""),
                        service_type=metadata.get("service_type", "unknown"),
                        similarity_score=item.get("score", 0.0),
                        metadata=metadata
                    ))
                
                logger.info(
                    f"Found {len(matches)} semantic service matches for: {user_input[:50]}"
                )
                return matches
            else:
                logger.warning(
                    f"Semantic service discovery failed: {response.status_code} - {response.text}"
                )
                return []
                
        except Exception as e:
            logger.error(f"Error in semantic service discovery: {e}", exc_info=True)
            return []  # 降级：返回空列表
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# 全局实例
semantic_service_discovery = SemanticServiceDiscovery()


