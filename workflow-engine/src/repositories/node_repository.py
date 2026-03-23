"""
节点Repository
工作流节点配置数据访问层
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

# 导入数据库模型
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.workflow_models import (
    WorkflowNode as DBWorkflowNode,
    WorkflowConnection as DBWorkflowConnection,
    NodeType
)
from database.src.repositories.workflow_repository import (
    WorkflowNodeRepository as DBWorkflowNodeRepository,
    WorkflowConnectionRepository as DBWorkflowConnectionRepository
)

logger = logging.getLogger(__name__)


class NodeRepository:
    """节点Repository（适配层）"""
    
    def __init__(self, session: Session):
        self.session = session
        self._node_repo = DBWorkflowNodeRepository(session)
        self._connection_repo = DBWorkflowConnectionRepository(session)
    
    def get_by_workflow_id(self, workflow_id: str) -> List[DBWorkflowNode]:
        """根据工作流ID获取所有节点"""
        try:
            workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            return self._node_repo.get_by_workflow_id(workflow_uuid)
        except (ValueError, TypeError):
            logger.warning(f"Invalid workflow_id format: {workflow_id}")
            return []
    
    def get_by_node_id(
        self,
        workflow_id: str,
        node_id: str
    ) -> Optional[DBWorkflowNode]:
        """根据节点ID获取节点"""
        try:
            nodes = self.get_by_workflow_id(workflow_id)
            for node in nodes:
                if node.node_id == node_id:
                    return node
            return None
        except Exception as e:
            logger.error(f"Error getting node by node_id: {str(e)}")
            return None
    
    def create_node(
        self,
        workflow_id: str,
        node_id: str,
        name: str,
        node_type: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, float]] = None,
        style: Optional[Dict[str, Any]] = None
    ) -> DBWorkflowNode:
        """创建节点"""
        try:
            workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            
            # 转换节点类型
            db_node_type = None
            try:
                db_node_type = NodeType[node_type.upper()]
            except KeyError:
                # 如果枚举中没有，尝试使用字符串值
                db_node_type = node_type
            
            node = DBWorkflowNode(
                workflow_id=workflow_uuid,
                node_id=node_id,
                name=name,
                node_type=db_node_type,
                description=description,
                config=config or {},
                position=position,
                style=style
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
    ) -> Optional[DBWorkflowNode]:
        """更新节点"""
        try:
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            return self._node_repo.update(uuid_id, **updates)
        except (ValueError, TypeError):
            logger.warning(f"Invalid node_id format: {node_id}")
            return None
    
    def delete_node(self, node_id: str) -> bool:
        """删除节点"""
        try:
            uuid_id = UUID(node_id) if isinstance(node_id, str) else node_id
            return self._node_repo.delete(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid node_id format: {node_id}")
            return False
    
    def delete_workflow_nodes(self, workflow_id: str) -> int:
        """删除工作流的所有节点"""
        try:
            workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            nodes = self._node_repo.get_by_workflow_id(workflow_uuid)
            count = len(nodes)
            for node in nodes:
                self.session.delete(node)
            self.session.flush()
            return count
        except (ValueError, TypeError):
            logger.warning(f"Invalid workflow_id format: {workflow_id}")
            return 0
    
    def get_connections_by_workflow_id(
        self,
        workflow_id: str
    ) -> List[DBWorkflowConnection]:
        """根据工作流ID获取所有连接"""
        try:
            workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            return self._connection_repo.get_by_workflow_id(workflow_uuid)
        except (ValueError, TypeError):
            logger.warning(f"Invalid workflow_id format: {workflow_id}")
            return []
    
    def create_connection(
        self,
        workflow_id: str,
        source_node_id: str,
        target_node_id: str,
        condition: Optional[str] = None,
        label: Optional[str] = None,
        style: Optional[Dict[str, Any]] = None
    ) -> DBWorkflowConnection:
        """创建连接"""
        try:
            workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            
            # 获取节点ID（需要先找到节点）
            source_node = self.get_by_node_id(workflow_id, source_node_id)
            target_node = self.get_by_node_id(workflow_id, target_node_id)
            
            if not source_node or not target_node:
                raise ValueError(f"Source or target node not found: {source_node_id} -> {target_node_id}")
            
            connection = DBWorkflowConnection(
                workflow_id=workflow_uuid,
                source_node_id=source_node.id,
                target_node_id=target_node.id,
                condition=condition,
                label=label,
                style=style
            )
            self.session.add(connection)
            self.session.flush()
            return connection
        except SQLAlchemyError as e:
            logger.error(f"Error creating connection: {str(e)}")
            self.session.rollback()
            raise
    
    def delete_connection(self, connection_id: str) -> bool:
        """删除连接"""
        try:
            uuid_id = UUID(connection_id) if isinstance(connection_id, str) else connection_id
            return self._connection_repo.delete(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid connection_id format: {connection_id}")
            return False
    
    def delete_workflow_connections(self, workflow_id: str) -> int:
        """删除工作流的所有连接"""
        try:
            workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            connections = self._connection_repo.get_by_workflow_id(workflow_uuid)
            count = len(connections)
            for connection in connections:
                self.session.delete(connection)
            self.session.flush()
            return count
        except (ValueError, TypeError):
            logger.warning(f"Invalid workflow_id format: {workflow_id}")
            return 0









