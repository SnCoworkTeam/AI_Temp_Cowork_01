"""
知识图谱搜索服务
在统一搜索中集成知识图谱查询
"""
import logging
import httpx
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class KnowledgeGraphSearchService:
    """知识图谱搜索服务"""
    
    def __init__(self):
        """
        初始化知识图谱搜索服务
        """
        self.metadata_service_url = os.getenv(
            "METADATA_SERVICE_URL",
            "http://metadata-service:8005"
        )
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def search_by_entity(
        self,
        entity_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        根据实体名称搜索相关节点
        
        Args:
            entity_name: 实体名称
            limit: 返回数量限制
        
        Returns:
            相关节点列表
        """
        try:
            # 1. 查找匹配的节点
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/knowledge-graph/nodes",
                params={
                    "label_pattern": entity_name,
                    "limit": limit
                }
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            nodes = data.get("nodes", [])
            
            # 2. 对每个节点获取邻居和子图
            enriched_results = []
            for node in nodes[:limit]:
                node_id = node.get("id")
                
                # 获取节点详情（包括邻居）
                detail_response = await self.http_client.get(
                    f"{self.metadata_service_url}/api/knowledge-graph/nodes/{node_id}"
                )
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    enriched_results.append({
                        "type": "knowledge_graph_node",
                        "id": node_id,
                        "label": node.get("label"),
                        "node_type": node.get("node_type"),
                        "properties": node.get("properties", {}),
                        "neighbors": detail_data.get("neighbors", []),
                        "neighbor_count": detail_data.get("neighbor_count", 0),
                        "score": 1.0,  # 知识图谱节点默认高分
                        "source": "knowledge-graph"
                    })
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"Failed to search knowledge graph: {e}", exc_info=True)
            return []
    
    async def find_related_entities(
        self,
        entity_id: str,
        max_depth: int = 2,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查找相关实体（通过知识图谱）
        
        Args:
            entity_id: 实体节点ID
            max_depth: 最大深度
            limit: 返回数量限制
        
        Returns:
            相关实体列表
        """
        try:
            # 获取子图
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/knowledge-graph/subgraph/{entity_id}",
                params={
                    "max_depth": max_depth
                }
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            subgraph = data.get("subgraph", {})
            nodes = subgraph.get("nodes", [])
            edges = subgraph.get("edges", [])
            
            # 转换为统一格式
            results = []
            for node in nodes:
                if node.get("id") != entity_id:  # 排除自身
                    results.append({
                        "type": "related_entity",
                        "id": node.get("id"),
                        "label": node.get("label"),
                        "node_type": node.get("node_type"),
                        "properties": node.get("properties", {}),
                        "relationship": self._find_relationship(entity_id, node.get("id"), edges),
                        "score": 0.8,  # 相关实体分数
                        "source": "knowledge-graph"
                    })
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find related entities: {e}", exc_info=True)
            return []
    
    def _find_relationship(
        self,
        source_id: str,
        target_id: str,
        edges: List[Dict[str, Any]]
    ) -> Optional[str]:
        """查找两个节点之间的关系类型"""
        for edge in edges:
            if (edge.get("source_id") == source_id and edge.get("target_id") == target_id) or \
               (edge.get("source_id") == target_id and edge.get("target_id") == source_id):
                return edge.get("relationship_type")
        return None
    
    async def search_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 3
    ) -> List[List[str]]:
        """
        查找两个节点之间的路径
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            max_depth: 最大深度
        
        Returns:
            路径列表
        """
        try:
            response = await self.http_client.post(
                f"{self.metadata_service_url}/api/knowledge-graph/paths",
                json={
                    "source_id": source_id,
                    "target_id": target_id,
                    "max_depth": max_depth
                }
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            return data.get("paths", [])
            
        except Exception as e:
            logger.error(f"Failed to search paths: {e}", exc_info=True)
            return []
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()







