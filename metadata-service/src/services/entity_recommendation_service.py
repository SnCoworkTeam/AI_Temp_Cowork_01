"""
基于知识图谱的实体推荐服务
提供智能实体推荐功能
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository
from ..services.metadata_catalog import MetadataCatalogService
from ..services.recommendation_cache import RecommendationCache
import os

logger = logging.getLogger(__name__)


class EntityRecommendationService:
    """实体推荐服务"""
    
    def __init__(self, db: Session, use_cache: bool = True):
        """
        初始化实体推荐服务
        
        Args:
            db: 数据库会话
            use_cache: 是否使用缓存
        """
        self.db = db
        self.kg_repo = KnowledgeGraphRepository(db)
        self.catalog = MetadataCatalogService(db)
        self.use_cache = use_cache
        self.cache = None
        if use_cache:
            try:
                redis_host = os.getenv("REDIS_HOST", "redis")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))
                self.cache = RecommendationCache(
                    redis_host=redis_host,
                    redis_port=redis_port,
                    default_ttl=3600  # 1小时
                )
                logger.info("Recommendation cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize recommendation cache: {e}")
                self.use_cache = False
    
    async def recommend_related_entities(
        self,
        entity_id: int,
        max_depth: int = 2,
        limit: int = 10,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        推荐相关实体（基于知识图谱）
        
        Args:
            entity_id: 源实体ID
            max_depth: 最大遍历深度
            limit: 返回数量限制
            relationship_types: 关系类型过滤
        
        Returns:
            推荐实体列表
        """
        # 检查缓存
        if self.use_cache and self.cache:
            cache_key_params = {
                "max_depth": max_depth,
                "limit": limit,
                "relationship_types": ",".join(relationship_types) if relationship_types else None
            }
            cached_result = self.cache.get("related", entity_id, **cache_key_params)
            if cached_result:
                logger.info(f"Cache hit for entity_id: {entity_id}")
                return cached_result.get("recommendations", [])
        
        try:
            # 1. 查找实体对应的知识图谱节点
            entity_node = self._find_entity_node(entity_id)
            if not entity_node:
                logger.warning(f"Entity node not found for entity_id: {entity_id}")
                return []
            
            # 2. 获取子图（相关实体）
            subgraph = self.kg_repo.get_subgraph(
                node_id=str(entity_node.id),
                max_depth=max_depth,
                relationship_types=relationship_types
            )
            
            # 3. 提取相关节点（排除自身）
            related_nodes = [
                node for node in subgraph.get("nodes", [])
                if node.get("id") != str(entity_node.id)
            ]
            
            # 4. 计算推荐分数
            recommendations = []
            for node in related_nodes[:limit]:
                score = self._calculate_recommendation_score(
                    entity_node, node, subgraph.get("edges", [])
                )
                recommendations.append({
                    "entity_id": self._extract_entity_id_from_node(node),
                    "node_id": node.get("id"),
                    "label": node.get("label"),
                    "node_type": node.get("node_type"),
                    "score": score,
                    "relationship": self._find_relationship(
                        str(entity_node.id), node.get("id"), subgraph.get("edges", [])
                    ),
                    "properties": node.get("properties", {})
                })
            
            # 5. 按分数排序
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            final_recommendations = recommendations[:limit]
            
            # 保存到缓存
            if self.use_cache and self.cache:
                cache_key_params = {
                    "max_depth": max_depth,
                    "limit": limit,
                    "relationship_types": ",".join(relationship_types) if relationship_types else None
                }
                self.cache.set(
                    "related",
                    entity_id,
                    {"recommendations": final_recommendations},
                    **cache_key_params
                )
            
            logger.info(f"Recommended {len(final_recommendations)} entities for entity_id: {entity_id}")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend entities: {e}", exc_info=True)
            return []
    
    def _find_entity_node(self, entity_id: int):
        """查找实体对应的知识图谱节点"""
        all_nodes = self.kg_repo.list_nodes(limit=10000, node_type="concept")
        for node in all_nodes:
            node_props = node.properties or {}
            if str(node_props.get("entity_id")) == str(entity_id):
                return node
        return None
    
    def _calculate_recommendation_score(
        self,
        source_node: Any,
        target_node: Dict[str, Any],
        edges: List[Dict[str, Any]]
    ) -> float:
        """
        计算推荐分数
        
        基于：
        - 关系类型权重
        - 路径距离
        - 节点属性相似度
        """
        score = 0.5  # 基础分数
        
        # 查找直接关系
        direct_edge = self._find_direct_edge(
            str(source_node.id), target_node.get("id"), edges
        )
        
        if direct_edge:
            # 直接关系加分
            score += 0.3
            
            # 关系类型权重
            rel_type = direct_edge.get("relationship_type", "")
            if rel_type == "parent_of" or rel_type == "child_of":
                score += 0.2  # 层次关系权重高
            elif rel_type == "related_to":
                score += 0.1
        
        # 节点类型匹配加分
        if source_node.node_type == target_node.get("node_type"):
            score += 0.1
        
        return min(score, 1.0)
    
    def _find_direct_edge(
        self,
        source_id: str,
        target_id: str,
        edges: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """查找直接边"""
        for edge in edges:
            if (edge.get("source_id") == source_id and edge.get("target_id") == target_id) or \
               (edge.get("source_id") == target_id and edge.get("target_id") == source_id):
                return edge
        return None
    
    def _find_relationship(
        self,
        source_id: str,
        target_id: str,
        edges: List[Dict[str, Any]]
    ) -> Optional[str]:
        """查找关系类型"""
        edge = self._find_direct_edge(source_id, target_id, edges)
        return edge.get("relationship_type") if edge else None
    
    def _extract_entity_id_from_node(self, node: Dict[str, Any]) -> Optional[int]:
        """从节点提取实体ID"""
        props = node.get("properties", {})
        entity_id = props.get("entity_id")
        if entity_id:
            try:
                return int(entity_id)
            except (ValueError, TypeError):
                return None
        return None
    
    async def recommend_by_similarity(
        self,
        entity_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        基于相似度推荐实体
        
        Args:
            entity_id: 源实体ID
            limit: 返回数量限制
        
        Returns:
            推荐实体列表
        """
        # 检查缓存
        if self.use_cache and self.cache:
            cached_result = self.cache.get("similar", entity_id, limit=limit)
            if cached_result:
                logger.info(f"Cache hit for similar entities: {entity_id}")
                return cached_result.get("recommendations", [])
        
        try:
            # 获取源实体信息
            entity = self.catalog.get_business_entity(entity_id)
            if not entity:
                return []
            
            # 获取所有实体
            all_entities = self.catalog.list_business_entities(limit=10000)
            
            # 计算相似度
            similarities = []
            for other_entity in all_entities:
                if other_entity.id == entity_id:
                    continue
                
                similarity = self._calculate_entity_similarity(entity, other_entity)
                if similarity > 0.5:  # 相似度阈值
                    similarities.append({
                        "entity_id": other_entity.id,
                        "name": other_entity.name,
                        "display_name": other_entity.display_name,
                        "similarity": similarity,
                        "entity_type": other_entity.entity_type
                    })
            
            # 按相似度排序
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            final_similarities = similarities[:limit]
            
            # 保存到缓存
            if self.use_cache and self.cache:
                self.cache.set(
                    "similar",
                    entity_id,
                    {"recommendations": final_similarities},
                    limit=limit
                )
            
            return final_similarities
            
        except Exception as e:
            logger.error(f"Failed to recommend by similarity: {e}", exc_info=True)
            return []
    
    def _calculate_entity_similarity(
        self,
        entity1: Any,
        entity2: Any
    ) -> float:
        """计算实体相似度"""
        score = 0.0
        
        # 类型匹配
        if entity1.entity_type == entity2.entity_type:
            score += 0.3
        
        # 名称相似度（简单实现）
        name1 = (entity1.name or "").lower()
        name2 = (entity2.name or "").lower()
        if name1 and name2:
            if name1 in name2 or name2 in name1:
                score += 0.3
            # 简单的字符重叠度
            common_chars = set(name1) & set(name2)
            if common_chars:
                score += 0.2 * (len(common_chars) / max(len(name1), len(name2)))
        
        # 描述相似度（如果有）
        desc1 = (entity1.description or "").lower()
        desc2 = (entity2.description or "").lower()
        if desc1 and desc2:
            common_words = set(desc1.split()) & set(desc2.split())
            if common_words:
                score += 0.2 * (len(common_words) / max(len(desc1.split()), len(desc2.split())))
        
        return min(score, 1.0)

