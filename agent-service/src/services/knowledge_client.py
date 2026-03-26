"""
Knowledge Base客户端
用于知识库搜索和文档管理
"""
import logging
import httpx
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class KnowledgeClient:
    """Knowledge Base客户端"""
    
    def __init__(self):
        self.base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://knowledge-base:8004")
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索知识库
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            params = {
                "q": query,
                "limit": limit
            }
            
            if filters:
                params.update(filters)
            
            response = await self.http_client.get(
                f"{self.base_url}/api/search",
                params=params
            )
            response.raise_for_status()
            result = response.json()
            
            # 处理不同的响应格式
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "results" in result:
                return result["results"]
            else:
                return []
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档详情
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档详情
        """
        try:
            response = await self.http_client.get(
                f"{self.base_url}/api/documents/{document_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.3,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        语义搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            min_score: 最小相似度分数
            filters: 过滤条件
            
        Returns:
            搜索结果
        """
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/search/semantic",
                json={
                    "query": query,
                    "top_k": top_k,
                    "min_score": min_score,
                    "filters": filters or {}
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {"results": [], "total": 0}
    
    async def keyword_search(
        self,
        keywords: List[str],
        match_all: bool = False,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        关键词搜索
        
        Args:
            keywords: 关键词列表
            match_all: 是否匹配所有关键词
            page: 页码
            page_size: 每页大小
            
        Returns:
            搜索结果
        """
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/search/keyword",
                json={
                    "keywords": keywords,
                    "match_all": match_all,
                    "page": page,
                    "page_size": page_size
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return {"results": [], "total": 0}
    
    async def hybrid_search(
        self,
        query: str,
        keywords: List[str] = None,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> Dict[str, Any]:
        """
        混合搜索
        
        Args:
            query: 查询文本
            keywords: 关键词列表
            top_k: 返回结果数量
            semantic_weight: 语义搜索权重
            keyword_weight: 关键词搜索权重
            
        Returns:
            搜索结果
        """
        try:
            params = {
                "query": query,
                "top_k": top_k,
                "semantic_weight": semantic_weight,
                "keyword_weight": keyword_weight
            }
            if keywords:
                params["keywords"] = ",".join(keywords)
            
            response = await self.http_client.get(
                f"{self.base_url}/api/search/hybrid",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return {"results": [], "total": 0}
    
    async def get_knowledge_graph(
        self,
        node_type: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取知识图谱
        
        Args:
            node_type: 节点类型（可选）
            limit: 返回节点数量限制
            
        Returns:
            知识图谱数据
        """
        try:
            params = {"limit": limit}
            if node_type:
                params["node_type"] = node_type
            
            response = await self.http_client.get(
                f"{self.base_url}/api/knowledge-graph",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Get knowledge graph failed: {e}")
            return {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0}
    
    async def get_related_concepts(
        self,
        concept: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        获取相关概念
        
        Args:
            concept: 概念名称
            limit: 返回数量限制
            
        Returns:
            相关概念数据
        """
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/knowledge-graph/nodes",
                json={
                    "operation": "get_related",
                    "concept": concept,
                    "limit": limit
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Get related concepts failed: {e}")
            return {
                "success": False,
                "concept": concept,
                "matching_nodes": [],
                "related_concepts": [],
                "relationships": [],
                "total_related": 0
            }
    
    async def store_execution_record(
        self,
        execution_id: str,
        task: str,
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        存储执行记录到知识库
        
        Args:
            execution_id: 执行ID
            task: 任务描述
            result: 执行结果
            metadata: 元数据
            
        Returns:
            是否成功
        """
        try:
            document_data = {
                "title": f"执行记录: {execution_id}",
                "content": f"任务: {task}\n\n结果: {result}",
                "metadata": metadata or {},
                "tags": ["execution_record", execution_id]
            }
            
            response = await self.http_client.post(
                f"{self.base_url}/api/documents",
                json=document_data
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to store execution record: {e}")
            return False


# 全局Knowledge客户端实例
knowledge_client = KnowledgeClient()




