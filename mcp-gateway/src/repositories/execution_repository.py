"""
工具执行Repository
工具执行记录数据访问层
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

from database.src.models.mcp_models import (
    MCPToolExecution as DBMCPToolExecution,
    ExecutionStatus
)
from database.src.repositories.mcp_repository import (
    MCPToolExecutionRepository as DBMCPToolExecutionRepository
)

logger = logging.getLogger(__name__)


class ExecutionRepository:
    """执行Repository（适配层）"""
    
    def __init__(self, session: Session):
        self.session = session
        self._db_repo = DBMCPToolExecutionRepository(session)
    
    def get_by_id(self, execution_id: str) -> Optional[DBMCPToolExecution]:
        """根据ID获取执行记录"""
        try:
            uuid_id = UUID(execution_id) if isinstance(execution_id, str) else execution_id
            return self._db_repo.get_by_id(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid execution_id format: {execution_id}")
            return None
    
    def create_execution(
        self,
        tool_id: str,
        executed_by: Optional[UUID] = None,
        workflow_execution_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DBMCPToolExecution:
        """创建执行记录"""
        try:
            tool_uuid = UUID(tool_id) if isinstance(tool_id, str) else tool_id
            
            workflow_uuid = None
            if workflow_execution_id:
                workflow_uuid = UUID(workflow_execution_id) if isinstance(workflow_execution_id, str) else workflow_execution_id
            
            execution = DBMCPToolExecution(
                tool_id=tool_uuid,
                executed_by=executed_by,
                workflow_execution_id=workflow_uuid,
                status=ExecutionStatus.PENDING,
                parameters=parameters or {},
                result=None,
                error_message=None,
                execution_time=None,
                start_time=None,
                end_time=None,
                metadata=metadata or {}
            )
            self.session.add(execution)
            self.session.flush()
            return execution
        except SQLAlchemyError as e:
            logger.error(f"Error creating execution: {str(e)}")
            self.session.rollback()
            raise
    
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
        result: Dict[str, Any],
        execution_time: float
    ) -> bool:
        """标记执行完成"""
        try:
            execution = self.get_by_id(execution_id)
            if execution:
                execution.status = ExecutionStatus.COMPLETED
                execution.result = result
                execution.execution_time = execution_time
                execution.end_time = datetime.utcnow()
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
        execution_time: Optional[float] = None
    ) -> bool:
        """标记执行失败"""
        try:
            execution = self.get_by_id(execution_id)
            if execution:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = error_message
                execution.end_time = datetime.utcnow()
                if execution_time:
                    execution.execution_time = execution_time
                elif execution.start_time:
                    delta = datetime.utcnow() - execution.start_time
                    execution.execution_time = delta.total_seconds()
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error failing execution: {str(e)}")
            self.session.rollback()
            return False
    
    def timeout_execution(
        self,
        execution_id: str,
        execution_time: float
    ) -> bool:
        """标记执行超时"""
        try:
            execution = self.get_by_id(execution_id)
            if execution:
                execution.status = ExecutionStatus.TIMEOUT
                execution.error_message = "Execution timeout"
                execution.execution_time = execution_time
                execution.end_time = datetime.utcnow()
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error timing out execution: {str(e)}")
            self.session.rollback()
            return False
    
    def get_by_tool_id(
        self,
        tool_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DBMCPToolExecution]:
        """根据工具ID获取执行记录"""
        try:
            tool_uuid = UUID(tool_id) if isinstance(tool_id, str) else tool_id
            return self._db_repo.get_by_tool_id(tool_uuid, skip=skip, limit=limit)
        except (ValueError, TypeError):
            logger.warning(f"Invalid tool_id format: {tool_id}")
            return []
    
    def get_by_user_id(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DBMCPToolExecution]:
        """根据用户ID获取执行记录"""
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            return self._db_repo.get_by_user_id(user_uuid, skip=skip, limit=limit)
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format: {user_id}")
            return []
    
    def get_recent_executions(
        self,
        limit: int = 100
    ) -> List[DBMCPToolExecution]:
        """获取最近的执行记录"""
        try:
            return self._db_repo.get_all(skip=0, limit=limit)
        except SQLAlchemyError as e:
            logger.error(f"Error getting recent executions: {str(e)}")
            return []
    
    def get_statistics(
        self,
        tool_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取执行统计信息"""
        try:
            tool_uuid = None
            if tool_id:
                tool_uuid = UUID(tool_id) if isinstance(tool_id, str) else tool_id
            
            return self._db_repo.get_statistics(
                tool_id=tool_uuid,
                start_date=start_date,
                end_date=end_date
            )
        except (ValueError, TypeError):
            logger.warning(f"Invalid tool_id format: {tool_id}")
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_duration_seconds": 0.0
            }
    
    def get_call_frequency(
        self,
        tool_id: str,
        time_window_minutes: int = 60
    ) -> int:
        """获取指定时间窗口内的调用频率"""
        try:
            tool_uuid = UUID(tool_id) if isinstance(tool_id, str) else tool_id
            from datetime import timedelta
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            count = self.session.query(DBMCPToolExecution).filter(
                and_(
                    DBMCPToolExecution.tool_id == tool_uuid,
                    DBMCPToolExecution.created_at >= cutoff_time
                )
            ).count()
            
            return count
        except (ValueError, TypeError):
            logger.warning(f"Invalid tool_id format: {tool_id}")
            return 0
        except SQLAlchemyError as e:
            logger.error(f"Error getting call frequency: {str(e)}")
            return 0









