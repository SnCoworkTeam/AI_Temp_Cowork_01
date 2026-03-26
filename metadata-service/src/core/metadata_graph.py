"""
元数据知识图谱
基于PostgreSQL递归查询实现多跳关系查询
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class RelatedService:
    """相关服务"""
    
    def __init__(
        self,
        service_id: str,
        service_name: str,
        service_type: str,
        depth: int,
        relation_type: str
    ):
        self.service_id = service_id
        self.service_name = service_name
        self.service_type = service_type
        self.depth = depth
        self.relation_type = relation_type
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "service_type": self.service_type,
            "depth": self.depth,
            "relation_type": self.relation_type
        }


class MetadataGraph:
    """元数据图谱 - 基于PostgreSQL递归查询"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def find_related_services(
        self,
        intent: str,
        hops: int = 3,
        limit: int = 20
    ) -> List[RelatedService]:
        """
        查找相关服务（基于意图）
        
        Args:
            intent: 意图类型或关键词
            hops: 跳数（关系深度）
            limit: 返回数量限制
            
        Returns:
            相关服务列表
        """
        try:
            # 使用PostgreSQL递归CTE查询
            # 注意：这里假设有一个service_relations表存储服务关系
            # 如果表不存在，需要先创建
            
            query = text("""
            WITH RECURSIVE service_graph AS (
                -- 初始节点：匹配意图的服务
                SELECT 
                    s.id::text as service_id,
                    s.name as service_name,
                    s.type as service_type,
                    0 as depth,
                    'intent_match' as relation_type,
                    ARRAY[s.id::text] as path
                FROM services s
                WHERE s.intent_tags @> ARRAY[:intent::text]
                   OR s.name ILIKE :intent_pattern
                   OR s.description ILIKE :intent_pattern
                
                UNION ALL
                
                -- 递归：查找相关服务
                SELECT 
                    s2.id::text,
                    s2.name,
                    s2.type,
                    sg.depth + 1,
                    sr.relation_type,
                    sg.path || s2.id::text
                FROM service_relations sr
                JOIN service_graph sg ON sr.from_service_id::text = sg.service_id
                JOIN services s2 ON sr.to_service_id::text = s2.id::text
                WHERE sg.depth < :hops
                AND NOT (s2.id::text = ANY(sg.path))  -- 避免循环
            )
            SELECT DISTINCT 
                service_id,
                service_name,
                service_type,
                depth,
                relation_type
            FROM service_graph
            ORDER BY depth, service_name
            LIMIT :limit;
            """)
            
            result = self.db.execute(
                query,
                {
                    "intent": intent,
                    "intent_pattern": f"%{intent}%",
                    "hops": hops,
                    "limit": limit
                }
            )
            
            services = []
            for row in result:
                services.append(RelatedService(
                    service_id=row.service_id,
                    service_name=row.service_name,
                    service_type=row.service_type,
                    depth=row.depth,
                    relation_type=row.relation_type
                ))
            
            logger.info(f"Found {len(services)} related services for intent: {intent}")
            return services
            
        except Exception as e:
            # 如果表不存在或查询失败，返回空列表（降级）
            logger.debug(f"Graph query failed (table may not exist): {e}")
            return []
    
    def find_services_by_tags(
        self,
        tags: List[str],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        根据标签查找服务（简化版本，不依赖图）
        
        Args:
            tags: 标签列表
            limit: 返回数量限制
            
        Returns:
            服务列表
        """
        try:
            # 从业务实体中查找（业务实体有标签）
            from ..models.business_entity import BusinessEntity
            
            query = self.db.query(BusinessEntity)
            
            # 构建标签过滤（PostgreSQL数组包含）
            for tag in tags:
                query = query.filter(BusinessEntity.tags.contains([tag]))
            
            entities = query.limit(limit).all()
            
            services = []
            for entity in entities:
                services.append({
                    "service_id": f"entity_{entity.id}",
                    "service_name": entity.display_name or entity.name,
                    "service_type": "business_entity",
                    "tags": entity.tags or []
                })
            
            return services
            
        except Exception as e:
            logger.error(f"Failed to find services by tags: {e}")
            return []


def get_metadata_graph(db: Session) -> MetadataGraph:
    """获取元数据图谱实例"""
    return MetadataGraph(db)


