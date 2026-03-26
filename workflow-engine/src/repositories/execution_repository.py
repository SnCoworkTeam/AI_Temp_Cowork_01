"""
执行Repository
工作流执行历史数据访问层
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from datetime import datetime

# 导入数据库模型
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.workflow_models import (
    WorkflowExecution as DBWorkflowExecution,
    ExecutionStatus
)
from database.src.repositories.workflow_repository import (
    WorkflowExecutionRepository as DBWorkflowExecutionRepository
)

logger = logging.getLogger(__name__)


class ExecutionRepository:
    """执行Repository（适配层）"""
    
    def __init__(self, session: Session):
        self.session = session
        self._db_repo = DBWorkflowExecutionRepository(session)
    
    def get_by_id(self, execution_id: str) -> Optional[DBWorkflowExecution]:
        """根据ID获取执行记录"""
        try:
            uuid_id = UUID(execution_id) if isinstance(execution_id, str) else execution_id
            return self._db_repo.get_by_id(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid execution_id format: {execution_id}")
            return None
    
    def create_execution(
        self,
        workflow_id: str,
        executed_by: Optional[UUID] = None,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DBWorkflowExecution:
        """创建执行记录"""
        try:
            workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            
            execution = DBWorkflowExecution(
                workflow_id=workflow_uuid,
                executed_by=executed_by,
                status=ExecutionStatus.PENDING,
                input_data=input_data or {},
                output_data=None,
                progress=0.0,
                current_node_id=None,
                node_results={},
                start_time=None,
                end_time=None,
                execution_time=None,
                metadata=metadata or {}
            )
            self.session.add(execution)
            self.session.flush()
            return execution
        except SQLAlchemyError as e:
            logger.error(f"Error creating execution: {str(e)}")
            self.session.rollback()
            raise
    
    def update_execution(
        self,
        execution_id: str,
        **updates
    ) -> Optional[DBWorkflowExecution]:
        """更新执行记录"""
        try:
            uuid_id = UUID(execution_id) if isinstance(execution_id, str) else execution_id
            execution = self._db_repo.get_by_id(uuid_id)
            
            if execution:
                # 处理特殊字段
                if "status" in updates:
                    status_str = updates["status"]
                    try:
                        execution.status = ExecutionStatus[status_str.upper()]
                    except KeyError:
                        logger.warning(f"Invalid status: {status_str}")
                
                if "progress" in updates:
                    execution.progress = float(updates["progress"])
                
                if "current_node_id" in updates:
                    execution.current_node_id = updates["current_node_id"]
                
                if "node_results" in updates:
                    if execution.node_results is None:
                        execution.node_results = {}
                    execution.node_results.update(updates["node_results"])
                
                if "output_data" in updates:
                    execution.output_data = updates["output_data"]
                
                if "error_message" in updates:
                    execution.error_message = updates["error_message"]
                
                # 更新开始时间（使用started_at字段）
                if "start_time" in updates:
                    execution.start_time = updates["start_time"]
                elif "started_at" in updates:
                    execution.start_time = updates["started_at"]
                
                # 更新结束时间并计算执行时间（使用finished_at字段）
                if "end_time" in updates:
                    execution.end_time = updates["end_time"]
                    if execution.start_time:
                        delta = execution.end_time - execution.start_time
                        execution.execution_time = delta.total_seconds()
                elif "finished_at" in updates:
                    execution.end_time = updates["finished_at"]
                    if execution.start_time:
                        delta = execution.end_time - execution.start_time
                        execution.execution_time = delta.total_seconds()
                
                # 更新其他字段
                for key, value in updates.items():
                    if key not in ["status", "progress", "current_node_id", "node_results",
                                   "output_data", "error_message", "start_time", "end_time"]:
                        if hasattr(execution, key):
                            setattr(execution, key, value)
                
                self.session.flush()
            return execution
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid execution_id format: {str(e)}")
            return None
    
    def start_execution(self, execution_id: str) -> bool:
        """标记执行开始"""
        try:
            execution = self.get_by_id(execution_id)
            if execution:
                execution.status = ExecutionStatus.RUNNING
                execution.start_time = datetime.utcnow()
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error starting execution: {str(e)}")
            self.session.rollback()
            return False
    
    def complete_execution(
        self,
        execution_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        progress: float = 1.0
    ) -> bool:
        """标记执行完成"""
        try:
            execution = self.get_by_id(execution_id)
            if execution:
                execution.status = ExecutionStatus.COMPLETED
                execution.progress = progress
                execution.output_data = output_data
                execution.end_time = datetime.utcnow()
                if execution.start_time:
                    delta = execution.end_time - execution.start_time
                    execution.execution_time = delta.total_seconds()
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error completing execution: {str(e)}")
            self.session.rollback()
            return False
    
    def fail_execution(
        self,
        execution_id: str,
        error_message: str,
        node_results: Optional[Dict[str, Any]] = None
    ) -> bool:
        """标记执行失败"""
        try:
            execution = self.get_by_id(execution_id)
            if execution:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = error_message
                execution.end_time = datetime.utcnow()
                if execution.start_time:
                    delta = execution.end_time - execution.start_time
                    execution.execution_time = delta.total_seconds()
                if node_results:
                    if execution.node_results is None:
                        execution.node_results = {}
                    execution.node_results.update(node_results)
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error failing execution: {str(e)}")
            self.session.rollback()
            return False
    
    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        try:
            execution = self.get_by_id(execution_id)
            if execution:
                execution.status = ExecutionStatus.CANCELLED
                execution.end_time = datetime.utcnow()
                if execution.start_time:
                    delta = execution.end_time - execution.start_time
                    execution.execution_time = delta.total_seconds()
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling execution: {str(e)}")
            self.session.rollback()
            return False
    
    def update_progress(
        self,
        execution_id: str,
        progress: float,
        current_node_id: Optional[str] = None,
        node_result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新执行进度"""
        try:
            execution = self.get_by_id(execution_id)
            if execution:
                execution.progress = max(0.0, min(1.0, progress))
                if current_node_id:
                    execution.current_node_id = current_node_id
                if node_result:
                    if execution.node_results is None:
                        execution.node_results = {}
                    execution.node_results.update(node_result)
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
            self.session.rollback()
            return False
    
    def get_by_workflow_id(
        self,
        workflow_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DBWorkflowExecution]:
        """根据工作流ID获取执行历史"""
        try:
            workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            return self._db_repo.get_by_workflow_id(workflow_uuid, skip=skip, limit=limit)
        except (ValueError, TypeError):
            logger.warning(f"Invalid workflow_id format: {workflow_id}")
            return []
    
    def get_by_user_id(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DBWorkflowExecution]:
        """根据用户ID获取执行历史"""
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            return self._db_repo.get_by_user_id(user_uuid, skip=skip, limit=limit)
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format: {user_id}")
            return []
    
    def get_running_executions(self) -> List[DBWorkflowExecution]:
        """获取正在运行的执行"""
        return self._db_repo.get_running_executions()
    
    def get_statistics(
        self,
        workflow_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取执行统计信息"""
        try:
            workflow_uuid = None
            if workflow_id:
                workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            
            return self._db_repo.get_statistics(
                workflow_id=workflow_uuid,
                start_date=start_date,
                end_date=end_date
            )
        except (ValueError, TypeError):
            logger.warning(f"Invalid workflow_id format: {workflow_id}")
            return {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "running": 0,
                "success_rate": 0
            }

