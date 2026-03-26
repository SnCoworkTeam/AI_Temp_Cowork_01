"""
EA知识图谱服务
存储EA实体和关系，支持图遍历和关系查询
根据风险分析报告建议：图谱+向量混合存储
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

# 导入数据库模型
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.enterprise_architecture_models import (
    BusinessProcess, ApplicationSystem, DataEntity,
    ArchitectureRelationship
)

# 尝试导入Neo4j客户端
try:
    from database.src.core.neo4j_client import Neo4jClient
    NEO4J_AVAILABLE = True
except ImportError as e:
    NEO4J_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Neo4j客户端未找到，将使用关系数据库: {e}")

if 'logger' not in locals():
    logger = logging.getLogger(__name__)


class EAKnowledgeGraph:
    """EA知识图谱服务"""
    
    def __init__(self, db: Session, graph_client=None, neo4j_client: Optional[Neo4jClient] = None):
        """
        初始化EA知识图谱服务
        
        Args:
            db: 数据库会话
            graph_client: 图数据库客户端（兼容接口）
            neo4j_client: Neo4j客户端（如果提供）
        """
        self.db = db
        
        # 初始化Neo4j客户端
        if neo4j_client:
            self.neo4j_client = neo4j_client
            self.use_neo4j = True
        elif NEO4J_AVAILABLE:
            try:
                self.neo4j_client = Neo4jClient()
                # 不在这里连接，延迟到使用时连接
                self.use_neo4j = True
                logger.info("已集成Neo4j客户端（延迟连接）")
            except Exception as e:
                logger.warning(f"Neo4j客户端初始化失败: {e}，将使用关系数据库")
                self.neo4j_client = None
                self.use_neo4j = False
        else:
            self.neo4j_client = None
            self.use_neo4j = False
        
        # 兼容旧的graph_client接口
        self.graph_client = graph_client or self.neo4j_client
        
        logger.info("EA知识图谱服务初始化完成")
    
    async def create_entity(
        self,
        entity_type: str,
        entity_id: str,
        properties: Dict[str, Any]
    ) -> bool:
        """
        创建EA实体节点（在图数据库中）
        
        Args:
            entity_type: 实体类型（"BusinessProcess" | "ApplicationSystem" | "DataEntity"）
            entity_id: 实体ID
            properties: 实体属性字典
            
        Returns:
            bool: 是否成功
        """
        if self.use_neo4j and self.neo4j_client:
            # 使用Neo4j
            try:
                # 确保连接
                if not self.neo4j_client.driver:
                    await self.neo4j_client.connect()
                
                # 创建节点
                node_properties = {
                    "id": entity_id,
                    **properties
                }
                await self.neo4j_client.create_node(
                    labels=[entity_type],
                    properties=node_properties
                )
                logger.debug(f"在Neo4j中创建实体: {entity_type}:{entity_id}")
                return True
            except Exception as e:
                logger.error(f"在Neo4j中创建实体失败: {e}")
                return False
        elif self.graph_client:
            # 使用兼容的图数据库客户端
            try:
                self.graph_client.create_node(
                    node_id=entity_id,
                    node_type=entity_type,
                    properties=properties
                )
                logger.debug(f"在图数据库中创建实体: {entity_type}:{entity_id}")
                return True
            except Exception as e:
                logger.error(f"在图数据库中创建实体失败: {e}")
                return False
        else:
            # 如果没有图数据库，实体信息已经在关系数据库中
            logger.debug(f"实体已在关系数据库中: {entity_type}:{entity_id}")
            return True
    
    async def create_relationship(
        self,
        from_entity_id: str,
        to_entity_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        创建EA关系边（在图数据库中）
        
        Args:
            from_entity_id: 源实体ID
            to_entity_id: 目标实体ID
            relation_type: 关系类型（"uses" | "calls" | "contains" | "flows_to"等）
            properties: 关系属性字典
            
        Returns:
            bool: 是否成功
        """
        if self.use_neo4j and self.neo4j_client:
            # 使用Neo4j
            try:
                # 确保连接
                if not self.neo4j_client.driver:
                    await self.neo4j_client.connect()
                
                # 创建关系
                rel_properties = properties or {}
                query = """
                MATCH (a {id: $from_id}), (b {id: $to_id})
                CREATE (a)-[r:%s]->(b)
                SET r += $properties
                RETURN id(r) AS rel_id
                """ % relation_type.upper()
                
                params = {
                    "from_id": from_entity_id,
                    "to_id": to_entity_id,
                    "properties": rel_properties
                }
                
                result = await self.neo4j_client.execute_write(query, params)
                if result:
                    logger.debug(f"在Neo4j中创建关系: {from_entity_id} -[{relation_type}]-> {to_entity_id}")
                    return True
                return False
            except Exception as e:
                logger.error(f"在Neo4j中创建关系失败: {e}")
                return False
        elif self.graph_client:
            # 使用兼容的图数据库客户端
            try:
                self.graph_client.create_relationship(
                    from_id=from_entity_id,
                    to_id=to_entity_id,
                    relation_type=relation_type,
                    properties=properties or {}
                )
                logger.debug(f"在图数据库中创建关系: {from_entity_id} -[{relation_type}]-> {to_entity_id}")
                return True
            except Exception as e:
                logger.error(f"在图数据库中创建关系失败: {e}")
                return False
        else:
            # 如果没有图数据库，从关系数据库加载关系
            try:
                # 从ArchitectureRelationship表加载关系
                relationship = self.db.query(ArchitectureRelationship).filter(
                    ArchitectureRelationship.from_entity_id == from_entity_id,
                    ArchitectureRelationship.to_entity_id == to_entity_id,
                    ArchitectureRelationship.relationship_type == relation_type
                ).first()
                
                if relationship:
                    logger.debug(f"关系已在关系数据库中: {from_entity_id} -[{relation_type}]-> {to_entity_id}")
                    return True
                else:
                    logger.warning(f"关系不存在于关系数据库中: {from_entity_id} -[{relation_type}]-> {to_entity_id}")
                    return False
            except Exception as e:
                logger.error(f"从关系数据库加载关系失败: {e}")
                return False
    
    async def query_related_entities(
        self,
        entity_id: str,
        relation_types: Optional[List[str]] = None,
        max_depth: int = 2,
        direction: str = "both"  # "outgoing" | "incoming" | "both"
    ) -> List[Dict[str, Any]]:
        """
        查询相关实体（图遍历）
        
        Args:
            entity_id: 实体ID
            relation_types: 关系类型列表，如果为None则查询所有关系
            max_depth: 最大遍历深度
            direction: 遍历方向
            
        Returns:
            List[Dict]: 相关实体列表，每个包含entity_id, entity_type, relation_type, depth
        """
        if self.use_neo4j and self.neo4j_client:
            # 使用Neo4j进行图遍历
            try:
                # 确保连接
                if not self.neo4j_client.driver:
                    await self.neo4j_client.connect()
                
                # 构建Cypher查询
                if direction == "outgoing":
                    rel_pattern = "-[r*1..%d]->" % max_depth
                elif direction == "incoming":
                    rel_pattern = "<-[r*1..%d]-" % max_depth
                else:  # both
                    rel_pattern = "-[r*1..%d]-" % max_depth
                
                # 关系类型过滤
                rel_filter = ""
                if relation_types:
                    rel_types_str = "|".join([rt.upper() for rt in relation_types])
                    rel_filter = f":{rel_types_str}"
                
                query = f"""
                MATCH (start {{id: $entity_id}}){rel_pattern}(related)
                WHERE ALL(rel IN r WHERE type(rel) IN $relation_types OR $relation_types IS NULL)
                RETURN DISTINCT related.id AS entity_id, 
                       labels(related)[0] AS entity_type,
                       type(r[0]) AS relation_type,
                       length(r) AS depth
                LIMIT 100
                """
                
                params = {
                    "entity_id": entity_id,
                    "relation_types": relation_types or None
                }
                
                results = await self.neo4j_client.execute_query(query, params)
                
                # 转换为统一格式
                related_entities = []
                for record in results:
                    related_entities.append({
                        "entity_id": record.get("entity_id"),
                        "entity_type": record.get("entity_type"),
                        "relation_type": record.get("relation_type"),
                        "depth": record.get("depth", 1)
                    })
                
                return related_entities
            except Exception as e:
                logger.error(f"Neo4j图遍历失败: {e}")
                return []
        elif self.graph_client:
            # 使用兼容的图数据库客户端进行图遍历
            try:
                results = self.graph_client.traverse(
                    start_node=entity_id,
                    relation_types=relation_types,
                    max_depth=max_depth,
                    direction=direction
                )
                return results
            except Exception as e:
                logger.error(f"图遍历失败: {e}")
                return []
        else:
            # 从关系数据库查询关系（简化实现，只查询1度关系）
            try:
                related_entities = []
                
                # 查询出边关系
                if direction in ["outgoing", "both"]:
                    relationships = self.db.query(ArchitectureRelationship).filter(
                        ArchitectureRelationship.from_entity_id == entity_id
                    ).all()
                    
                    for rel in relationships:
                        if relation_types is None or rel.relationship_type in relation_types:
                            related_entities.append({
                                "entity_id": rel.to_entity_id,
                                "entity_type": rel.to_entity_type,
                                "relation_type": rel.relationship_type,
                                "depth": 1
                            })
                
                # 查询入边关系
                if direction in ["incoming", "both"]:
                    relationships = self.db.query(ArchitectureRelationship).filter(
                        ArchitectureRelationship.to_entity_id == entity_id
                    ).all()
                    
                    for rel in relationships:
                        if relation_types is None or rel.relationship_type in relation_types:
                            related_entities.append({
                                "entity_id": rel.from_entity_id,
                                "entity_type": rel.from_entity_type,
                                "relation_type": rel.relationship_type,
                                "depth": 1
                            })
                
                return related_entities
            except Exception as e:
                logger.error(f"从关系数据库查询关系失败: {e}")
                return []
    
    async def find_path(
        self,
        from_entity_id: str,
        to_entity_id: str,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查找两个实体之间的路径
        
        Args:
            from_entity_id: 起始实体ID
            to_entity_id: 目标实体ID
            max_depth: 最大路径长度
            
        Returns:
            List[Dict]: 路径列表，每个路径包含nodes和edges
        """
        if self.use_neo4j and self.neo4j_client:
            # 使用Neo4j查找路径
            try:
                # 确保连接
                if not self.neo4j_client.driver:
                    await self.neo4j_client.connect()
                
                # 使用Cypher查找最短路径
                query = """
                MATCH path = shortestPath((start {id: $from_id})-[*1..%d]-(end {id: $to_id}))
                RETURN [node in nodes(path) | node.id] AS nodes,
                       [rel in relationships(path) | type(rel)] AS edges,
                       length(path) AS path_length
                LIMIT 5
                """ % max_depth
                
                params = {
                    "from_id": from_entity_id,
                    "to_id": to_entity_id
                }
                
                results = await self.neo4j_client.execute_query(query, params)
                
                # 转换为统一格式
                paths = []
                for record in results:
                    paths.append({
                        "nodes": record.get("nodes", []),
                        "edges": record.get("edges", []),
                        "path_length": record.get("path_length", 0)
                    })
                
                return paths
            except Exception as e:
                logger.error(f"Neo4j查找路径失败: {e}")
                return []
        elif self.graph_client:
            # 使用兼容的图数据库客户端查找路径
            try:
                paths = self.graph_client.find_paths(
                    from_node=from_entity_id,
                    to_node=to_entity_id,
                    max_depth=max_depth
                )
                return paths
            except Exception as e:
                logger.error(f"查找路径失败: {e}")
                return []
        else:
            # 从关系数据库查找路径（简化实现，使用BFS）
            try:
                from collections import deque
                
                # BFS查找路径
                queue = deque([(from_entity_id, [from_entity_id])])
                visited = {from_entity_id}
                
                while queue:
                    current_id, path = queue.popleft()
                    
                    if len(path) > max_depth:
                        continue
                    
                    if current_id == to_entity_id:
                        # 找到路径
                        return [{"nodes": path, "edges": []}]  # 简化实现，不返回边信息
                    
                    # 查找下一跳
                    relationships = self.db.query(ArchitectureRelationship).filter(
                        ArchitectureRelationship.from_entity_id == current_id
                    ).all()
                    
                    for rel in relationships:
                        next_id = rel.to_entity_id
                        if next_id not in visited:
                            visited.add(next_id)
                            queue.append((next_id, path + [next_id]))
                
                return []  # 未找到路径
            except Exception as e:
                logger.error(f"从关系数据库查找路径失败: {e}")
                return []
    
    def get_entity_relationships(
        self,
        entity_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取实体的所有关系（按关系类型分组）
        
        Args:
            entity_id: 实体ID
            
        Returns:
            Dict: {relation_type: [related_entities]}
        """
        try:
            relationships = {}
            
            # 查询出边
            outgoing = self.db.query(ArchitectureRelationship).filter(
                ArchitectureRelationship.from_entity_id == entity_id
            ).all()
            
            for rel in outgoing:
                rel_type = rel.relationship_type
                if rel_type not in relationships:
                    relationships[rel_type] = []
                relationships[rel_type].append({
                    "entity_id": rel.to_entity_id,
                    "entity_type": rel.to_entity_type,
                    "direction": "outgoing"
                })
            
            # 查询入边
            incoming = self.db.query(ArchitectureRelationship).filter(
                ArchitectureRelationship.to_entity_id == entity_id
            ).all()
            
            for rel in incoming:
                rel_type = rel.relationship_type
                if rel_type not in relationships:
                    relationships[rel_type] = []
                relationships[rel_type].append({
                    "entity_id": rel.from_entity_id,
                    "entity_type": rel.from_entity_type,
                    "direction": "incoming"
                })
            
            return relationships
        except Exception as e:
            logger.error(f"获取实体关系失败: {e}")
            return {}

