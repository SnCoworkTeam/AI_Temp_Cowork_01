"""
知识图谱Repository
知识图谱关系数据访问层
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

# 导入数据库模型
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.knowledge_models import (
    KnowledgeGraphNode as DBKnowledgeGraphNode,
    KnowledgeGraphEdge as DBKnowledgeGraphEdge
)
from database.src.repositories.knowledge_repository import (
    KnowledgeGraphNodeRepository as DBKnowledgeGraphNodeRepository,
    KnowledgeGraphEdgeRepository as DBKnowledgeGraphEdgeRepository
)

logger = logging.getLogger(__name__)


class KnowledgeGraphRepository:
    """知识图谱Repository（适配层）"""
    
    def __init__(self, session: Session):
        self.session = session
        self._node_repo = DBKnowledgeGraphNodeRepository(session)
        self._edge_repo = DBKnowledgeGraphEdgeRepository(session)
    
    # 节点操作
    def get_node_by_id(self, node_id: str) -> Optional[DBKnowledgeGraphNode]:
        """根据ID获取节点"""
        try:
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            return self._node_repo.get_by_id(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid node_id format: {node_id}")
            return None
    
    def get_node_by_label(
        self,
        label: str,
        node_type: Optional[str] = None
    ) -> Optional[DBKnowledgeGraphNode]:
        """根据标签获取节点"""
        try:
            return self._node_repo.get_by_label(label, node_type)
        except Exception as e:
            logger.error(f"Error getting node by label: {str(e)}")
            return None
    
    def create_node(
        self,
        label: str,
        node_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> DBKnowledgeGraphNode:
        """创建节点"""
        try:
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
            return node
        except SQLAlchemyError as e:
            logger.error(f"Error creating node: {str(e)}")
            self.session.rollback()
            raise
    
    def update_node(
        self,
        node_id: str,
        **updates
    ) -> Optional[DBKnowledgeGraphNode]:
        """更新节点"""
        try:
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            return self._node_repo.update(uuid_id, **updates)
        except (ValueError, TypeError):
            logger.warning(f"Invalid node_id format: {node_id}")
            return None
    
    def delete_node(self, node_id: str) -> bool:
        """删除节点（会级联删除相关边）"""
        try:
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            return self._node_repo.delete(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid node_id format: {node_id}")
            return False
    
    def list_nodes(
        self,
        skip: int = 0,
        limit: int = 100,
        node_type: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> List[DBKnowledgeGraphNode]:
        """列出节点"""
        try:
            filters = {}
            if node_type:
                filters["node_type"] = node_type
            if document_id:
                doc_uuid = UUID(document_id) if isinstance(document_id, str) else document_id
                filters["document_id"] = doc_uuid
            
            return self._node_repo.get_all(skip=skip, limit=limit, filters=filters)
        except SQLAlchemyError as e:
            logger.error(f"Error listing nodes: {str(e)}")
            raise
    
    def get_related_nodes(
        self,
        node_id: str,
        max_depth: int = 1
    ) -> List[DBKnowledgeGraphNode]:
        """获取相关节点（通过边连接）"""
        try:
            node = self.get_node_by_id(node_id)
            if not node:
                return []
            
            related_nodes = set()
            
            # 获取直接相关的节点（深度1）
            for edge in node.source_edges:
                if edge.target_node:
                    related_nodes.add(edge.target_node)
            
            for edge in node.target_edges:
                if edge.source_node:
                    related_nodes.add(edge.source_node)
            
            # 如果深度>1，递归获取
            if max_depth > 1:
                for related_node in list(related_nodes):
                    deeper_nodes = self.get_related_nodes(
                        str(related_node.id),
                        max_depth - 1
                    )
                    related_nodes.update(deeper_nodes)
            
            return list(related_nodes)
            
        except Exception as e:
            logger.error(f"Error getting related nodes: {str(e)}")
            return []
    
    # 边操作
    def get_edge_by_id(self, edge_id: str) -> Optional[DBKnowledgeGraphEdge]:
        """根据ID获取边"""
        try:
            uuid_id = UUID(edge_id) if isinstance(edge_id, str) else edge_id
            return self._edge_repo.get_by_id(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid edge_id format: {edge_id}")
            return None
    
    def create_edge(
        self,
        source_node_id: str,
        target_node_id: str,
        label: Optional[str] = None,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None
    ) -> DBKnowledgeGraphEdge:
        """创建边"""
        try:
            source_uuid = UUID(source_node_id) if isinstance(source_node_id, str) else source_node_id
            target_uuid = UUID(target_node_id) if isinstance(target_node_id, str) else target_node_id
            
            edge = DBKnowledgeGraphEdge(
                source_node_id=source_uuid,
                target_node_id=target_uuid,
                label=label,
                weight=weight,
                properties=properties or {}
            )
            self.session.add(edge)
            self.session.flush()
            return edge
        except SQLAlchemyError as e:
            logger.error(f"Error creating edge: {str(e)}")
            self.session.rollback()
            raise
    
    def update_edge(
        self,
        edge_id: str,
        **updates
    ) -> Optional[DBKnowledgeGraphEdge]:
        """更新边"""
        try:
            uuid_id = UUID(edge_id) if isinstance(edge_id, str) else edge_id
            return self._edge_repo.update(uuid_id, **updates)
        except (ValueError, TypeError):
            logger.warning(f"Invalid edge_id format: {edge_id}")
            return None
    
    def delete_edge(self, edge_id: str) -> bool:
        """删除边"""
        try:
            uuid_id = UUID(edge_id) if isinstance(edge_id, str) else edge_id
            return self._edge_repo.delete(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid edge_id format: {edge_id}")
            return False
    
    def get_edges_by_node(
        self,
        node_id: str,
        direction: str = "both"  # "in", "out", "both"
    ) -> List[DBKnowledgeGraphEdge]:
        """获取节点的所有边"""
        try:
            node = self.get_node_by_id(node_id)
            if not node:
                return []
            
            edges = []
            if direction in ["out", "both"]:
                edges.extend(node.source_edges)
            if direction in ["in", "both"]:
                edges.extend(node.target_edges)
            
            return edges
        except Exception as e:
            logger.error(f"Error getting edges by node: {str(e)}")
            return []
    
    def get_edges_between(
        self,
        source_node_id: str,
        target_node_id: str
    ) -> List[DBKnowledgeGraphEdge]:
        """获取两个节点之间的所有边"""
        try:
            source_uuid = UUID(source_node_id) if isinstance(source_node_id, str) else source_node_id
            target_uuid = UUID(target_node_id) if isinstance(target_node_id, str) else target_node_id
            
            return self._edge_repo.get_edges_between(source_uuid, target_uuid)
        except (ValueError, TypeError):
            logger.warning(f"Invalid node_id format")
            return []
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        try:
            nodes = self._node_repo.get_all(skip=0, limit=10000)
            edges = self._edge_repo.get_all(skip=0, limit=10000)
            
            # 统计节点类型
            node_types = {}
            for node in nodes:
                node_type = node.node_type or "unknown"
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            # 统计边标签
            edge_labels = {}
            for edge in edges:
                label = edge.label or "unknown"
                edge_labels[label] = edge_labels.get(label, 0) + 1
            
            return {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": node_types,
                "edge_labels": edge_labels,
                "avg_degree": len(edges) * 2 / len(nodes) if nodes else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting graph stats: {str(e)}")
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "node_types": {},
                "edge_labels": {},
                "avg_degree": 0.0
            }









