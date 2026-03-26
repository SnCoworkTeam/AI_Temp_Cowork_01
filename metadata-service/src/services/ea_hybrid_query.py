"""
EA混合查询引擎
结合图谱和向量，提供更精准的EA查询
根据风险分析报告建议：图谱+向量混合存储
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .ea_vectorization_service import EAVectorizationService
from .ea_knowledge_graph import EAKnowledgeGraph

logger = logging.getLogger(__name__)


class EAHybridQuery:
    """EA混合查询引擎"""
    
    def __init__(
        self,
        db: Session,
        graph: EAKnowledgeGraph,
        vector: EAVectorizationService
    ):
        """
        初始化EA混合查询引擎
        
        Args:
            db: 数据库会话
            graph: EA知识图谱服务
            vector: EA向量化服务
        """
        self.db = db
        self.graph = graph
        self.vector = vector
        logger.info("EA混合查询引擎初始化完成")
    
    async def query(
        self,
        user_input: str,
        query_type: str = "hybrid",  # "semantic" | "relation" | "hybrid"
        entity_type: Optional[str] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        混合查询EA数据
        
        Args:
            user_input: 用户输入
            query_type: 查询类型
                - "semantic": 纯向量语义搜索
                - "relation": 纯图谱关系查询
                - "hybrid": 先向量后图谱，或先图谱后向量
            entity_type: 可选的实体类型过滤
            top_k: 返回结果数量
            
        Returns:
            Dict: 查询结果，包含vector_results和graph_results
        """
        if query_type == "semantic":
            # 纯向量语义搜索
            vector_results = self.vector.semantic_search(
                query=user_input,
                entity_type=entity_type,
                top_k=top_k
            )
            return {
                "query_type": "semantic",
                "vector_results": vector_results,
                "graph_results": []
            }
        
        elif query_type == "relation":
            # 纯图谱关系查询
            # 先从用户输入中提取实体ID（简化实现）
            # 实际应该使用NER或LLM提取实体
            entity_id = self._extract_entity_id(user_input)
            
            if entity_id:
                graph_results = await self.graph.query_related_entities(
                    entity_id=entity_id,
                    max_depth=2
                )
                return {
                    "query_type": "relation",
                    "vector_results": [],
                    "graph_results": graph_results
                }
            else:
                return {
                    "query_type": "relation",
                    "vector_results": [],
                    "graph_results": []
                }
        
        else:  # hybrid
            # 混合查询：先向量后图谱
            # 1. 先用向量找到相关实体
            vector_results = self.vector.semantic_search(
                query=user_input,
                entity_type=entity_type,
                top_k=5  # 先取前5个
            )
            
            # 2. 再用图谱查询这些实体的关系
            graph_results = []
            all_related_entities = {}
            
            for result in vector_results:
                entity_id = result.get("entity_id")
                if entity_id:
                    # 查询该实体的相关实体
                    related = await self.graph.query_related_entities(
                        entity_id=entity_id,
                        max_depth=1
                    )
                    
                    # 去重并合并
                    for rel_entity in related:
                        rel_id = rel_entity.get("entity_id")
                        if rel_id and rel_id not in all_related_entities:
                            all_related_entities[rel_id] = rel_entity
                    
                    graph_results.extend(related)
            
            # 3. 对图谱结果进行向量过滤（可选）
            # 如果图谱结果太多，可以用向量相似度进一步过滤
            if len(graph_results) > top_k:
                # 简化实现：只返回前top_k个
                graph_results = graph_results[:top_k]
            
            return {
                "query_type": "hybrid",
                "vector_results": vector_results,
                "graph_results": list(all_related_entities.values()),
                "total_results": len(vector_results) + len(all_related_entities)
            }
    
    async def query_with_context(
        self,
        user_input: str,
        context_entity_id: Optional[str] = None,
        query_type: str = "hybrid",
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        带上下文的混合查询
        
        Args:
            user_input: 用户输入
            context_entity_id: 上下文实体ID（如果用户正在查看某个实体）
            query_type: 查询类型
            top_k: 返回结果数量
            
        Returns:
            Dict: 查询结果
        """
        if context_entity_id:
            # 如果有上下文实体，先查询相关实体
            related_entities = await self.graph.query_related_entities(
                entity_id=context_entity_id,
                max_depth=2
            )
            
            # 然后在这些相关实体中进行向量搜索
            # 简化实现：直接返回相关实体
            return {
                "query_type": "context_aware",
                "context_entity_id": context_entity_id,
                "vector_results": [],
                "graph_results": related_entities[:top_k]
            }
        else:
            # 没有上下文，使用普通混合查询
            return await self.query(user_input, query_type, top_k=top_k)
    
    async def find_impact_analysis(
        self,
        entity_id: str,
        change_type: str = "modify"  # "create" | "modify" | "delete"
    ) -> Dict[str, Any]:
        """
        影响分析：查找某个实体的变更会影响哪些其他实体
        
        Args:
            entity_id: 实体ID
            change_type: 变更类型
            
        Returns:
            Dict: 影响分析结果，包含affected_entities和impact_paths
        """
        # 1. 查询所有相关实体（多度关系）
        affected_entities = []
        
            # 直接相关（1度）
            direct_related = await self.graph.query_related_entities(
                entity_id=entity_id,
                max_depth=1
            )
            affected_entities.extend(direct_related)
            
            # 间接相关（2度）
            indirect_related = []
            for rel_entity in direct_related:
                rel_id = rel_entity.get("entity_id")
                if rel_id:
                    second_degree = await self.graph.query_related_entities(
                        entity_id=rel_id,
                        max_depth=1
                    )
                    indirect_related.extend(second_degree)
        
        # 去重
        seen_ids = {entity_id}
        unique_affected = []
        for entity in affected_entities + indirect_related:
            eid = entity.get("entity_id")
            if eid and eid not in seen_ids:
                seen_ids.add(eid)
                unique_affected.append(entity)
        
        # 2. 查找影响路径
        impact_paths = []
        for affected in unique_affected[:10]:  # 限制数量
            paths = await self.graph.find_path(
                from_entity_id=entity_id,
                to_entity_id=affected.get("entity_id"),
                max_depth=3
            )
            if paths:
                impact_paths.extend(paths)
        
        return {
            "source_entity_id": entity_id,
            "change_type": change_type,
            "affected_entities": unique_affected,
            "impact_paths": impact_paths[:5],  # 限制路径数量
            "total_affected": len(unique_affected)
        }
    
    def _extract_entity_id(self, user_input: str) -> Optional[str]:
        """
        从用户输入中提取实体ID（简化实现）
        
        实际应该使用NER或LLM提取实体
        
        Args:
            user_input: 用户输入
            
        Returns:
            Optional[str]: 实体ID，如果无法提取则返回None
        """
        # 简化实现：查找常见的实体ID模式
        import re
        
        # 查找类似"process:xxx"、"system:xxx"的模式
        patterns = [
            r"(?:process|流程)[:：](\w+)",
            r"(?:system|系统)[:：](\w+)",
            r"(?:entity|实体)[:：](\w+)",
            r"id[:：](\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

