"""
MCP工具Repository
MCP工具配置和调用记录管理
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from datetime import datetime

from ..models.mcp_models import MCPTool, MCPToolExecution
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MCPToolRepository(BaseRepository[MCPTool]):
    """MCP工具Repository"""
    
    def __init__(self, session: Session):
        super().__init__(MCPTool, session)
    
    def get_by_name(self, name: str) -> Optional[MCPTool]:
        """
        根据工具名称获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例或None
        """
        try:
            return self.session.query(MCPTool).filter(MCPTool.name == name).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting MCP tool by name {name}: {str(e)}")
            raise
    
    def get_active_tools(self) -> List[MCPTool]:
        """
        获取活跃工具列表
        
        Returns:
            活跃工具列表
        """
        try:
            return self.session.query(MCPTool).filter(MCPTool.is_active == True).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active MCP tools: {str(e)}")
            raise
    
    def get_by_category(self, category: str) -> List[MCPTool]:
        """
        根据分类获取工具列表
        
        Args:
            category: 工具分类
            
        Returns:
            工具列表
        """
        try:
            return self.session.query(MCPTool).filter(
                MCPTool.category == category,
                MCPTool.is_active == True
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting MCP tools by category {category}: {str(e)}")
            raise


class MCPToolExecutionRepository(BaseRepository[MCPToolExecution]):
    """MCP工具执行Repository"""
    
    def __init__(self, session: Session):
        super().__init__(MCPToolExecution, session)
    
    def get_by_tool_id(
        self,
        tool_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MCPToolExecution]:
        """
        根据工具ID获取执行记录
        
        Args:
            tool_id: 工具ID
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            执行记录列表
        """
        try:
            return self.session.query(MCPToolExecution).filter(
                MCPToolExecution.tool_id == tool_id
            ).order_by(desc(MCPToolExecution.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting executions by tool_id {tool_id}: {str(e)}")
            raise
    
    def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MCPToolExecution]:
        """
        根据用户ID获取执行记录
        
        Args:
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            执行记录列表
        """
        try:
            return self.session.query(MCPToolExecution).filter(
                MCPToolExecution.executed_by == user_id
            ).order_by(desc(MCPToolExecution.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting executions by user_id {user_id}: {str(e)}")
            raise
    
    def get_statistics(
        self,
        tool_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取执行统计信息
        
        Args:
            tool_id: 工具ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            统计信息字典
        """
        try:
            query = self.session.query(MCPToolExecution)
            
            if tool_id:
                query = query.filter(MCPToolExecution.tool_id == tool_id)
            
            if start_date:
                query = query.filter(MCPToolExecution.created_at >= start_date)
            
            if end_date:
                query = query.filter(MCPToolExecution.created_at <= end_date)
            
            total = query.count()
            # MCPToolExecution使用status字段，不是success字段
            # 根据ExecutionStatus枚举判断成功/失败
            from ..models.mcp_models import ExecutionStatus
            successful = query.filter(MCPToolExecution.status == ExecutionStatus.COMPLETED).count()
            failed = query.filter(
                MCPToolExecution.status.in_([ExecutionStatus.FAILED, ExecutionStatus.ERROR])
            ).count()
            
            # 计算平均执行时间
            executions = query.all()
            avg_duration = 0
            if executions:
                durations = [
                    (e.end_time - e.start_time).total_seconds()
                    for e in executions
                    if e.end_time and e.start_time
                ]
                if durations:
                    avg_duration = sum(durations) / len(durations)
            
            return {
                "total": total,
                "successful": successful,
                "failed": failed,
                "success_rate": (successful / total * 100) if total > 0 else 0,
                "avg_duration_seconds": avg_duration
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting execution statistics: {str(e)}")
            raise









