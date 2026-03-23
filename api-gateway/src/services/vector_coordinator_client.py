"""
向量协调服务客户端
用于调用vector-coordinator-service的API
"""
import httpx
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class VectorCoordinatorClient:
    """向量协调服务客户端"""
    
    def __init__(self):
        self.vector_coordinator_url = os.getenv(
            "VECTOR_COORDINATOR_URL",
            "http://vector-coordinator-service:8020"
        )
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
    
    async def find_similar_vectors(
        self,
        query: str,
        modalities: Optional[List[str]] = None,
        limit: int = 10,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        查找相似向量
        
        Args:
            query: 查询文本
            modalities: 模态列表（可选）
            limit: 返回数量限制
            threshold: 相似度阈值（可选）
        
        Returns:
            相似向量列表
        """
        try:
            request_body = {
                "query": query,
                "limit": limit
            }
            if modalities:
                request_body["modalities"] = modalities
            if threshold is not None:
                request_body["threshold"] = threshold
            
            response = await self.http_client.post(
                f"{self.vector_coordinator_url}/api/vectors/similar",
                json=request_body
            )
            response.raise_for_status()
            result = response.json()
            return result.get("results", [])
        except Exception as e:
            logger.warning(f"Failed to find similar vectors: {e}")
            return []
    
    async def register_vector(
        self,
        entity_uri: str,
        modality: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        注册向量到向量协调服务
        
        Args:
            entity_uri: 实体URI
            modality: 模态
            vector: 向量
            metadata: 元数据
        
        Returns:
            是否注册成功
        """
        try:
            request_body = {
                "entity_uri": entity_uri,
                "modality": modality,
                "vector": vector
            }
            if metadata:
                request_body["metadata"] = metadata
            
            response = await self.http_client.post(
                f"{self.vector_coordinator_url}/api/vectors/register",
                json=request_body
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Failed to register vector: {e}")
            return False
    
    async def fuse_vectors(
        self,
        vectors: Dict[str, List[float]],
        weights: Optional[Dict[str, float]] = None
    ) -> Optional[List[float]]:
        """
        融合多个模态的向量
        
        Args:
            vectors: 向量字典
            weights: 权重字典（可选）
        
        Returns:
            融合后的向量
        """
        try:
            request_body = {"vectors": vectors}
            if weights:
                request_body["weights"] = weights
            
            response = await self.http_client.post(
                f"{self.vector_coordinator_url}/api/vectors/fuse",
                json=request_body
            )
            response.raise_for_status()
            result = response.json()
            return result.get("fused_vector")
        except Exception as e:
            logger.warning(f"Failed to fuse vectors: {e}")
            return None
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()







