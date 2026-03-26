"""
知识图谱Repository
知识图谱关系数据访问层（迁移自knowledge-base）
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

# 导入database模块的模型和Repository
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.knowledge_models import (
    KnowledgeGraphNode as DBKnowledgeGraphNode,
    KnowledgeGraphEdge as DBKnowledgeGraphEdge
)
from sqlalchemy import or_, and_
from database.src.repositories.knowledge_repository import (
    KnowledgeGraphNodeRepository as DBKnowledgeGraphNodeRepository,
    KnowledgeGraphEdgeRepository as DBKnowledgeGraphEdgeRepository
)

logger = logging.getLogger(__name__)


class KnowledgeGraphRepository:
    """
    知识图谱Repository
    
    迁移自knowledge-base，用于metadata-service中的知识图谱管理
    直接使用database模块的Repository，简化实现
    """
    
    def __init__(self, session: Session):
        """
        初始化知识图谱Repository
        
        Args:
            session: SQLAlchemy数据库会话
        """
        self.session = session
        self._node_repo = DBKnowledgeGraphNodeRepository(session)
        self._edge_repo = DBKnowledgeGraphEdgeRepository(session)
    
    # ========== 节点操作 ==========
    
    def get_node_by_id(self, node_id: str) -> Optional[DBKnowledgeGraphNode]:
        """
        根据ID获取节点
        
        Args:
            node_id: 节点ID（UUID字符串或UUID对象）
        
        Returns:
            节点对象，如果不存在返回None
        """
        try:
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            return self._node_repo.get_by_id(uuid_id)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid node_id format: {node_id}, error: {e}")
            return None
    
    def get_node_by_label(
        self,
        label: str,
        node_type: Optional[str] = None
    ) -> Optional[DBKnowledgeGraphNode]:
        """
        根据标签获取节点
        
        Args:
            label: 节点标签
            node_type: 节点类型（可选）
        
        Returns:
            节点对象，如果不存在返回None
        """
        try:
            # 直接查询数据库，使用label字段（模型没有concept字段）
            query = self.session.query(DBKnowledgeGraphNode).filter(
                DBKnowledgeGraphNode.label == label
            )
            if node_type:
                query = query.filter(DBKnowledgeGraphNode.node_type == node_type)
            return query.first()
        except Exception as e:
            logger.error(f"Error getting node by label: {e}", exc_info=True)
            return None
    
    def create_node(
        self,
        label: str,
        node_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> Optional[DBKnowledgeGraphNode]:
        """
        创建节点（如果已存在则返回现有节点）
        
        Args:
            label: 节点标签
            node_type: 节点类型（可选）
            properties: 节点属性（可选）
            document_id: 关联文档ID（可选）
        
        Returns:
            创建的节点对象或现有节点
        """
        try:
            # 先检查节点是否已存在
            existing_node = self.get_node_by_label(label, node_type)
            if existing_node:
                logger.debug(f"Node already exists: {label} (type: {node_type}), returning existing node")
                # 如果提供了新属性，更新现有节点
                if properties:
                    if existing_node.properties:
                        existing_node.properties.update(properties)
                    else:
                        existing_node.properties = properties
                    self.session.flush()
                return existing_node
            
            # 节点不存在，创建新节点
            doc_uuid = None
            if document_id:
                doc_uuid = UUID(document_id) if isinstance(document_id, str) else document_id
            
            node = DBKnowledgeGraphNode(
                label=label,
                node_type=node_type,
                properties=properties or {},
                document_id=doc_uuid
            )
            self.session.add(node)
            self.session.flush()
            logger.debug(f"Created node: {label} (type: {node_type})")
            return node
        except SQLAlchemyError as e:
            logger.error(f"Error creating node: {e}", exc_info=True)
            self.session.rollback()
            # 如果是因为唯一约束冲突，尝试获取现有节点
            if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                logger.info(f"Node {label} already exists, attempting to retrieve it")
                existing_node = self.get_node_by_label(label, node_type)
                if existing_node:
                    return existing_node
            raise
    
    def update_node(
        self,
        node_id: str,
        **updates
    ) -> Optional[DBKnowledgeGraphNode]:
        """
        更新节点
        
        Args:
            node_id: 节点ID
            **updates: 要更新的字段
        
        Returns:
            更新后的节点对象，如果不存在返回None
        """
        try:
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            return self._node_repo.update(uuid_id, **updates)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid node_id format: {node_id}, error: {e}")
            return None
    
    def delete_node(self, node_id: str) -> bool:
        """
        删除节点
        
        Args:
            node_id: 节点ID
        
        Returns:
            是否删除成功
        """
        try:
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            return self._node_repo.delete(uuid_id)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid node_id format: {node_id}, error: {e}")
            return False
    
    def list_nodes(
        self,
        skip: int = 0,
        limit: int = 100,
        node_type: Optional[str] = None,
        label_pattern: Optional[str] = None
    ) -> List[DBKnowledgeGraphNode]:
        """
        列出节点
        
        Args:
            skip: 跳过数量
            limit: 返回数量限制
            node_type: 节点类型过滤（可选）
            label_pattern: 标签模式过滤（可选）
        
        Returns:
            节点列表
        """
        try:
            # 构建查询
            query = self.session.query(DBKnowledgeGraphNode)
            
            # 应用过滤条件
            if node_type:
                query = query.filter(DBKnowledgeGraphNode.node_type == node_type)
            if label_pattern:
                query = query.filter(DBKnowledgeGraphNode.label.ilike(f"%{label_pattern}%"))
            
            # 应用分页
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error listing nodes: {e}", exc_info=True)
            return []
    
    # ========== 边操作 ==========
    
    def create_edge(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Optional[DBKnowledgeGraphEdge]:
        """
        创建边
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            relationship_type: 关系类型
            properties: 边属性（可选）
        
        Returns:
            创建的边对象
        """
        try:
            # 验证输入参数
            if not source_id or not target_id:
                logger.warning(f"Cannot create edge: source_id or target_id is None or empty. source_id={source_id}, target_id={target_id}")
                return None
            
            # 验证节点是否存在
            source_node = self.get_node_by_id(source_id)
            target_node = self.get_node_by_id(target_id)
            
            if not source_node:
                logger.warning(f"Cannot create edge: source node not found. source_id={source_id}")
                return None
            
            if not target_node:
                logger.warning(f"Cannot create edge: target node not found. target_id={target_id}")
                return None
            
            source_uuid = UUID(source_id) if isinstance(source_id, str) else source_id
            target_uuid = UUID(target_id) if isinstance(target_id, str) else target_id
            
            # 再次验证UUID不为None
            if source_uuid is None or target_uuid is None:
                logger.error(f"Cannot create edge: UUID conversion failed. source_id={source_id}, target_id={target_id}, source_uuid={source_uuid}, target_uuid={target_uuid}")
                return None
            
            # 使用正确的字段名：relationship_type和edge_metadata（映射到数据库的metadata列）
            edge = DBKnowledgeGraphEdge(
                source_node_id=source_uuid,
                target_node_id=target_uuid,
                relationship_type=relationship_type,
                edge_metadata=properties or {}  # 使用edge_metadata属性，映射到数据库的metadata列
            )
            self.session.add(edge)
            self.session.flush()
            logger.info(f"Created edge: {source_id} -> {target_id} ({relationship_type})")
            return edge
        except (ValueError, TypeError, SQLAlchemyError) as e:
            logger.error(f"Error creating edge: {e}", exc_info=True)
            self.session.rollback()
            return None
    
    def get_edge_by_id(self, edge_id: str) -> Optional[DBKnowledgeGraphEdge]:
        """
        根据ID获取边
        
        Args:
            edge_id: 边ID
        
        Returns:
            边对象，如果不存在返回None
        """
        try:
            uuid_id = UUID(edge_id) if isinstance(edge_id, str) else edge_id
            return self._edge_repo.get_by_id(uuid_id)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid edge_id format: {edge_id}, error: {e}")
            return None
    
    def get_edges_by_node(
        self,
        node_id: str,
        direction: str = "both"  # "in", "out", "both"
    ) -> List[DBKnowledgeGraphEdge]:
        """
        获取节点的边
        
        Args:
            node_id: 节点ID
            direction: 方向（"in", "out", "both"）
        
        Returns:
            边列表
        """
        try:
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            query = self.session.query(DBKnowledgeGraphEdge)
            
            if direction == "in":
                query = query.filter(DBKnowledgeGraphEdge.target_node_id == uuid_id)
            elif direction == "out":
                query = query.filter(DBKnowledgeGraphEdge.source_node_id == uuid_id)
            else:  # both
                query = query.filter(
                    or_(
                        DBKnowledgeGraphEdge.source_node_id == uuid_id,
                        DBKnowledgeGraphEdge.target_node_id == uuid_id
                    )
                )
            
            return query.all()
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid node_id format: {node_id}, error: {e}")
            return []
    
    def delete_edge(self, edge_id: str) -> bool:
        """
        删除边
        
        Args:
            edge_id: 边ID
        
        Returns:
            是否删除成功
        """
        try:
            uuid_id = UUID(edge_id) if isinstance(edge_id, str) else edge_id
            return self._edge_repo.delete(uuid_id)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid edge_id format: {edge_id}, error: {e}")
            return False
    
    def list_edges(
        self,
        skip: int = 0,
        limit: int = 100,
        relationship_type: Optional[str] = None
    ) -> List[DBKnowledgeGraphEdge]:
        """
        列出边
        
        Args:
            skip: 跳过数量
            limit: 返回数量限制
            relationship_type: 关系类型过滤（可选）
        
        Returns:
            边列表
        """
        try:
            # 构建查询
            query = self.session.query(DBKnowledgeGraphEdge)
            
            # 应用过滤条件
            if relationship_type:
                query = query.filter(DBKnowledgeGraphEdge.relationship_type == relationship_type)
            
            # 应用分页
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error listing edges: {e}", exc_info=True)
            return []
    
    # ========== 查询操作 ==========
    
    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None
    ) -> List[List[str]]:
        """
        查找路径
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            max_depth: 最大深度
            relationship_types: 关系类型过滤（可选）
        
        Returns:
            路径列表（每个路径是节点ID列表）
        """
        try:
            source_uuid = UUID(source_id) if isinstance(source_id, str) else source_id
            target_uuid = UUID(target_id) if isinstance(target_id, str) else target_id
            
            # 使用广度优先搜索查找路径
            paths = []
            queue = [(source_uuid, [source_uuid])]
            visited = {source_uuid}
            
            while queue and len(paths) < 100:  # 限制路径数量
                current_id, path = queue.pop(0)
                
                if len(path) > max_depth:
                    continue
                
                if current_id == target_uuid:
                    paths.append([str(nid) for nid in path])
                    continue
                
                # 获取出边
                edges = self.get_edges_by_node(str(current_id), direction="out")
                for edge in edges:
                    if relationship_types and edge.relationship_type not in relationship_types:
                        continue
                    
                    next_id = edge.target_id
                    if next_id not in visited or next_id == target_uuid:
                        visited.add(next_id)
                        queue.append((next_id, path + [next_id]))
            
            return paths
        except Exception as e:
            logger.error(f"Error finding paths: {e}", exc_info=True)
            return []
    
    def get_neighbors(
        self,
        node_id: str,
        relationship_types: Optional[List[str]] = None,
        direction: str = "both"
    ) -> List[DBKnowledgeGraphNode]:
        """
        获取邻居节点
        
        Args:
            node_id: 节点ID
            relationship_types: 关系类型过滤（可选）
            direction: 方向（"in", "out", "both"）
        
        Returns:
            邻居节点列表
        """
        try:
            edges = self.get_edges_by_node(node_id, direction)
            neighbor_ids = set()
            
            for edge in edges:
                if relationship_types and edge.relationship_type not in relationship_types:
                    continue
                
                if direction == "in" or direction == "both":
                    neighbor_ids.add(edge.source_id)
                if direction == "out" or direction == "both":
                    neighbor_ids.add(edge.target_id)
            
            # 移除自身
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            neighbor_ids.discard(uuid_id)
            
            # 获取节点对象
            neighbors = []
            for nid in neighbor_ids:
                node = self.get_node_by_id(str(nid))
                if node:
                    neighbors.append(node)
            
            return neighbors
        except Exception as e:
            logger.error(f"Error getting neighbors: {e}", exc_info=True)
            return []
    
    def get_subgraph(
        self,
        node_id: str,
        max_depth: int = 2,
        relationship_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        获取子图
        
        Args:
            node_id: 中心节点ID
            max_depth: 最大深度
            relationship_types: 关系类型过滤（可选）
        
        Returns:
            子图数据（包含节点和边）
        """
        try:
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            nodes = {}
            edges = []
            visited = set()
            
            def traverse(current_id, depth):
                if depth > max_depth or current_id in visited:
                    return
                
                visited.add(current_id)
                node = self.get_node_by_id(str(current_id))
                if node:
                    nodes[str(current_id)] = {
                        "id": str(node.id),
                        "label": node.label,
                        "node_type": node.node_type,
                        "properties": node.properties
                    }
                    
                    if depth < max_depth:
                        neighbors = self.get_neighbors(
                            str(current_id),
                            relationship_types=relationship_types,
                            direction="both"
                        )
                        for neighbor in neighbors:
                            neighbor_edges = self.get_edges_by_node(
                                str(current_id),
                                direction="both"
                            )
                            for edge in neighbor_edges:
                                if (edge.source_id == current_id and edge.target_id == neighbor.id) or \
                                   (edge.target_id == current_id and edge.source_id == neighbor.id):
                                    edges.append({
                                        "id": str(edge.id),
                                        "source_id": str(edge.source_id),
                                        "target_id": str(edge.target_id),
                                        "relationship_type": edge.relationship_type,
                                        "properties": edge.properties
                                    })
                                    traverse(neighbor.id, depth + 1)
            
            traverse(uuid_id, 0)
            
            return {
                "nodes": list(nodes.values()),
                "edges": edges
            }
        except Exception as e:
            logger.error(f"Error getting subgraph: {e}", exc_info=True)
            return {"nodes": [], "edges": []}



