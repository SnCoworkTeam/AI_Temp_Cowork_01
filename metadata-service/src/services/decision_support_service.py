"""
智能决策支持服务
基于知识图谱和数据分析提供决策支持
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository
from ..services.metadata_catalog import MetadataCatalogService
from ..services.entity_recommendation_service import EntityRecommendationService

logger = logging.getLogger(__name__)


class DecisionSupportService:
    """智能决策支持服务"""
    
    def __init__(self, db: Session):
        """
        初始化决策支持服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.kg_repo = KnowledgeGraphRepository(db)
        self.catalog = MetadataCatalogService(db)
        self.recommendation_service = EntityRecommendationService(db)
    
    async def analyze_entity_impact(
        self,
        entity_id: int,
        analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """
        分析实体影响范围
        
        Args:
            entity_id: 实体ID
            analysis_type: 分析类型（full, direct, indirect）
        
        Returns:
            影响分析结果
        """
        try:
            # 查找实体节点
            entity_node = self._find_entity_node(entity_id)
            if not entity_node:
                return {
                    "entity_id": entity_id,
                    "error": "Entity node not found"
                }
            
            # 获取影响范围
            if analysis_type == "direct":
                max_depth = 1
            elif analysis_type == "indirect":
                max_depth = 3
            else:  # full
                max_depth = 3
            
            subgraph = self.kg_repo.get_subgraph(
                node_id=str(entity_node.id),
                max_depth=max_depth
            )
            
            # 分析影响
            impacted_entities = []
            for node in subgraph.get("nodes", []):
                if node.get("id") != str(entity_node.id):
                    entity_id_from_node = self._extract_entity_id_from_node(node)
                    if entity_id_from_node:
                        impacted_entities.append({
                            "entity_id": entity_id_from_node,
                            "node_id": node.get("id"),
                            "label": node.get("label"),
                            "relationship": self._find_relationship(
                                str(entity_node.id), node.get("id"), subgraph.get("edges", [])
                            )
                        })
            
            return {
                "entity_id": entity_id,
                "analysis_type": analysis_type,
                "impacted_entities_count": len(impacted_entities),
                "impacted_entities": impacted_entities,
                "subgraph_stats": {
                    "total_nodes": len(subgraph.get("nodes", [])),
                    "total_edges": len(subgraph.get("edges", []))
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze entity impact: {e}", exc_info=True)
            return {
                "entity_id": entity_id,
                "error": str(e)
            }
    
    async def find_optimal_path(
        self,
        source_entity_id: int,
        target_entity_id: int,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        查找两个实体之间的最优路径
        
        Args:
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
            max_depth: 最大深度
        
        Returns:
            路径分析结果
        """
        try:
            # 查找实体节点
            source_node = self._find_entity_node(source_entity_id)
            target_node = self._find_entity_node(target_entity_id)
            
            if not source_node or not target_node:
                return {
                    "error": "Source or target entity node not found"
                }
            
            # 查找路径
            paths = self.kg_repo.find_paths(
                source_id=str(source_node.id),
                target_id=str(target_node.id),
                max_depth=max_depth
            )
            
            # 选择最短路径
            shortest_path = None
            if paths:
                shortest_path = min(paths, key=len)
            
            return {
                "source_entity_id": source_entity_id,
                "target_entity_id": target_entity_id,
                "paths_found": len(paths),
                "shortest_path_length": len(shortest_path) if shortest_path else 0,
                "shortest_path": shortest_path,
                "all_paths": paths[:10]  # 最多返回10条路径
            }
            
        except Exception as e:
            logger.error(f"Failed to find optimal path: {e}", exc_info=True)
            return {
                "error": str(e)
            }
    
    async def get_entity_insights(
        self,
        entity_id: int
    ) -> Dict[str, Any]:
        """
        获取实体洞察信息
        
        Args:
            entity_id: 实体ID
        
        Returns:
            洞察信息
        """
        try:
            entity = self.catalog.get_business_entity(entity_id)
            if not entity:
                return {
                    "entity_id": entity_id,
                    "error": "Entity not found"
                }
            
            # 获取相关实体推荐
            related_entities = await self.recommendation_service.recommend_related_entities(
                entity_id, limit=5
            )
            
            # 分析影响范围
            impact_analysis = await self.analyze_entity_impact(entity_id, "direct")
            
            # 构建洞察
            insights = {
                "entity_id": entity_id,
                "entity_name": entity.name,
                "entity_type": entity.entity_type,
                "related_entities_count": len(related_entities),
                "top_related_entities": related_entities[:5],
                "direct_impact_count": impact_analysis.get("impacted_entities_count", 0),
                "recommendations": []
            }
            
            # 生成建议
            if len(related_entities) > 0:
                insights["recommendations"].append({
                    "type": "explore_related",
                    "message": f"发现 {len(related_entities)} 个相关实体，建议探索",
                    "entities": related_entities[:3]
                })
            
            if impact_analysis.get("impacted_entities_count", 0) > 10:
                insights["recommendations"].append({
                    "type": "high_impact",
                    "message": "该实体影响范围较大，修改时需谨慎"
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get entity insights: {e}", exc_info=True)
            return {
                "entity_id": entity_id,
                "error": str(e)
            }
    
    def _find_entity_node(self, entity_id: int):
        """查找实体对应的知识图谱节点"""
        all_nodes = self.kg_repo.list_nodes(limit=10000, node_type="concept")
        for node in all_nodes:
            node_props = node.properties or {}
            if str(node_props.get("entity_id")) == str(entity_id):
                return node
        return None
    
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
    
    def _find_relationship(
        self,
        source_id: str,
        target_id: str,
        edges: List[Dict[str, Any]]
    ) -> Optional[str]:
        """查找关系类型"""
        for edge in edges:
            if (edge.get("source_id") == source_id and edge.get("target_id") == target_id) or \
               (edge.get("source_id") == target_id and edge.get("target_id") == source_id):
                return edge.get("relationship_type")
        return None




