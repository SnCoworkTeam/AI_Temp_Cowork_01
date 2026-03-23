"""
工作流Repository
工作流定义、执行历史管理
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from datetime import datetime

from ..models.workflow_models import (
    WorkflowDefinition, WorkflowExecution, WorkflowNode, WorkflowConnection,
    WorkflowStatus, ExecutionStatus
)
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class WorkflowDefinitionRepository(BaseRepository[WorkflowDefinition]):
    """工作流定义Repository"""
    
    def __init__(self, session: Session):
        super().__init__(WorkflowDefinition, session)
    
    def get_by_name(self, name: str) -> Optional[WorkflowDefinition]:
        """
        根据名称获取工作流定义
        
        Args:
            name: 工作流名称
            
        Returns:
            工作流定义实例或None
        """
        try:
            return self.session.query(WorkflowDefinition).filter(
                WorkflowDefinition.name == name
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting workflow by name {name}: {str(e)}")
            raise
    
    def get_active_workflows(self, skip: int = 0, limit: int = 100) -> List[WorkflowDefinition]:
        """
        获取活跃工作流列表
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            活跃工作流列表
        """
        try:
            return self.session.query(WorkflowDefinition).filter(
                WorkflowDefinition.status == WorkflowStatus.ACTIVE
            ).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active workflows: {str(e)}")
            raise
    
    def get_by_creator(self, creator_id: UUID, skip: int = 0, limit: int = 100) -> List[WorkflowDefinition]:
        """
        根据创建者获取工作流列表
        
        Args:
            creator_id: 创建者ID
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            工作流定义列表
        """
        try:
            return self.session.query(WorkflowDefinition).filter(
                WorkflowDefinition.created_by == creator_id
            ).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting workflows by creator {creator_id}: {str(e)}")
            raise


class WorkflowExecutionRepository(BaseRepository[WorkflowExecution]):
    """工作流执行Repository"""
    
    def __init__(self, session: Session):
        super().__init__(WorkflowExecution, session)
    
    def get_by_workflow_id(
        self,
        workflow_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """
        根据工作流ID获取执行历史
        
        Args:
            workflow_id: 工作流定义ID
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            执行历史列表
        """
        try:
            return self.session.query(WorkflowExecution).filter(
                WorkflowExecution.workflow_id == workflow_id
            ).order_by(desc(WorkflowExecution.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting executions by workflow_id {workflow_id}: {str(e)}")
            raise
    
    def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """
        根据用户ID获取执行历史
        
        Args:
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            执行历史列表
        """
        try:
            return self.session.query(WorkflowExecution).filter(
                WorkflowExecution.executed_by == user_id
            ).order_by(desc(WorkflowExecution.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting executions by user_id {user_id}: {str(e)}")
            raise
    
    def get_running_executions(self) -> List[WorkflowExecution]:
        """
        获取正在运行的工作流执行
        
        Returns:
            正在运行的执行列表
        """
        try:
            return self.session.query(WorkflowExecution).filter(
                WorkflowExecution.status == ExecutionStatus.RUNNING
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting running executions: {str(e)}")
            raise
    
    def get_by_status(
        self,
        status: ExecutionStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """
        根据状态获取执行历史
        
        Args:
            status: 执行状态
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            执行历史列表
        """
        try:
            return self.session.query(WorkflowExecution).filter(
                WorkflowExecution.status == status
            ).order_by(desc(WorkflowExecution.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting executions by status {status}: {str(e)}")
            raise
    
    def get_statistics(
        self,
        workflow_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取执行统计信息
        
        Args:
            workflow_id: 工作流ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            统计信息字典
        """
        try:
            query = self.session.query(WorkflowExecution)
            
            if workflow_id:
                query = query.filter(WorkflowExecution.workflow_id == workflow_id)
            
            if start_date:
                query = query.filter(WorkflowExecution.created_at >= start_date)
            
            if end_date:
                query = query.filter(WorkflowExecution.created_at <= end_date)
            
            total = query.count()
            completed = query.filter(WorkflowExecution.status == ExecutionStatus.COMPLETED).count()
            failed = query.filter(WorkflowExecution.status == ExecutionStatus.FAILED).count()
            running = query.filter(WorkflowExecution.status == ExecutionStatus.RUNNING).count()
            
            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "running": running,
                "success_rate": (completed / total * 100) if total > 0 else 0
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting execution statistics: {str(e)}")
            raise


class WorkflowNodeRepository(BaseRepository[WorkflowNode]):
    """工作流节点Repository"""
    
    def __init__(self, session: Session):
        super().__init__(WorkflowNode, session)
    
    def get_by_workflow_id(self, workflow_id: UUID) -> List[WorkflowNode]:
        """
        根据工作流ID获取所有节点
        
        Args:
            workflow_id: 工作流定义ID
            
        Returns:
            节点列表
        """
        try:
            return self.session.query(WorkflowNode).filter(
                WorkflowNode.workflow_id == workflow_id
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting nodes by workflow_id {workflow_id}: {str(e)}")
            raise


class WorkflowConnectionRepository(BaseRepository[WorkflowConnection]):
    """工作流连接Repository"""
    
    def __init__(self, session: Session):
        super().__init__(WorkflowConnection, session)
    
    def get_by_workflow_id(self, workflow_id: UUID) -> List[WorkflowConnection]:
        """
        根据工作流ID获取所有连接
        
        Args:
            workflow_id: 工作流定义ID
            
        Returns:
            连接列表
        """
        try:
            return self.session.query(WorkflowConnection).filter(
                WorkflowConnection.workflow_id == workflow_id
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting connections by workflow_id {workflow_id}: {str(e)}")
            raise









