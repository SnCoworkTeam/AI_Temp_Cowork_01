"""
工具Repository
工具配置数据访问层（适配层）
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from enum import Enum

# 导入数据库模型
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.mcp_models import (
    MCPTool as DBMCPTool,
    ToolType,
    ToolStatus
)
from database.src.repositories.mcp_repository import (
    MCPToolRepository as DBMCPToolRepository
)

logger = logging.getLogger(__name__)


class ToolRepository:
    """工具Repository（适配层）"""
    
    def __init__(self, session: Session):
        self.session = session
        self._db_repo = DBMCPToolRepository(session)
    
    def get_by_id(self, tool_id: str) -> Optional[DBMCPTool]:
        """根据ID获取工具"""
        try:
            uuid_id = UUID(tool_id) if isinstance(tool_id, str) else tool_id
            return self._db_repo.get_by_id(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid tool_id format: {tool_id}")
            return None
    
    def get_by_name(self, name: str) -> Optional[DBMCPTool]:
        """根据名称获取工具"""
        return self._db_repo.get_by_name(name)

    def _normalize_tool_type(self, tool_type_value: Any) -> ToolType:
        """将上层ToolType映射为数据库ToolType"""
        if isinstance(tool_type_value, Enum):
            tool_type_value = tool_type_value.value
        if not isinstance(tool_type_value, str):
            return ToolType.CUSTOM
        normalized = tool_type_value.strip()
        if normalized.startswith("ToolType."):
            normalized = normalized.split(".", 1)[1]
        normalized = normalized.lower()
        normalized = {
            "function": "custom",
            "api": "http",
            "script": "custom",
            "workflow": "custom",
        }.get(normalized, normalized)
        try:
            return ToolType[normalized.upper()]
        except KeyError:
            logger.warning(f"Invalid tool_type: {tool_type_value}")
            return ToolType.CUSTOM

    def _normalize_status(self, status_value: Any) -> ToolStatus | None:
        """将上层状态映射为数据库ToolStatus"""
        if isinstance(status_value, Enum):
            status_value = status_value.value
        if not isinstance(status_value, str):
            return None
        normalized = status_value.strip().lower()
        try:
            return ToolStatus[normalized.upper()]
        except KeyError:
            return None
    
    def create_tool(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        tool_type: str = "custom",
        parameters: Optional[Dict[str, Any]] = None,
        required_parameters: Optional[List[str]] = None,
        return_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DBMCPTool:
        """创建工具记录"""
        try:
            # 检查工具是否已存在
            existing = self._db_repo.get_by_name(name)
            if existing:
                raise ValueError(f"Tool with name '{name}' already exists")
            
            # 转换工具类型
            db_tool_type = self._normalize_tool_type(tool_type)
            
            tool = DBMCPTool(
                name=name,
                description=description,
                version=version,
                tool_type=db_tool_type,
                status=ToolStatus.ACTIVE,
                parameters=parameters or {},
                required_parameters=required_parameters or [],
                return_type=return_type,
                config=config or {},
                metadata=metadata or {},
                call_count=0,
                success_count=0,
                failure_count=0
            )
            self.session.add(tool)
            self.session.flush()
            return tool
        except SQLAlchemyError as e:
            logger.error(f"Error creating tool: {str(e)}")
            self.session.rollback()
            raise
    
    def update_tool(
        self,
        tool_id: str,
        **updates
    ) -> Optional[DBMCPTool]:
        """更新工具"""
        try:
            uuid_id = UUID(tool_id) if isinstance(tool_id, str) else tool_id
            
            # 处理特殊字段
            if "status" in updates:
                status_value = self._normalize_status(updates["status"])
                if status_value is None:
                    logger.warning(f"Invalid status: {updates['status']}")
                    del updates["status"]
                else:
                    updates["status"] = status_value
            
            if "tool_type" in updates:
                updates["tool_type"] = self._normalize_tool_type(updates["tool_type"])
            
            return self._db_repo.update(uuid_id, **updates)
        except (ValueError, TypeError):
            logger.warning(f"Invalid tool_id format: {tool_id}")
            return None
    
    def delete_tool(self, tool_id: str) -> bool:
        """删除工具（软删除，标记为deprecated）"""
        try:
            uuid_id = UUID(tool_id) if isinstance(tool_id, str) else tool_id
            tool = self._db_repo.get_by_id(uuid_id)
            if tool:
                tool.status = ToolStatus.DEPRECATED
                self.session.flush()
                return True
            return False
        except (ValueError, TypeError):
            logger.warning(f"Invalid tool_id format: {tool_id}")
            return False
    
    def list_tools(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        tool_type: Optional[str] = None
    ) -> List[DBMCPTool]:
        """列出工具"""
        try:
            filters = {}
            if status:
                try:
                    filters["status"] = ToolStatus[status.upper()]
                except KeyError:
                    pass
            
            if tool_type:
                try:
                    filters["tool_type"] = ToolType[tool_type.upper()]
                except KeyError:
                    pass
            
            tools = self._db_repo.get_all(skip=skip, limit=limit, filters=filters)
            return tools
        except SQLAlchemyError as e:
            logger.error(f"Error listing tools: {str(e)}")
            raise
    
    def get_active_tools(self) -> List[DBMCPTool]:
        """获取活跃工具列表"""
        try:
            # 使用status字段而不是is_active
            return self.session.query(DBMCPTool).filter(
                DBMCPTool.status == ToolStatus.ACTIVE
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active tools: {str(e)}")
            raise
    
    def increment_call_count(self, tool_id: str, success: bool = True) -> bool:
        """增加工具调用计数"""
        try:
            tool = self.get_by_id(tool_id)
            if tool:
                tool.call_count += 1
                if success:
                    tool.success_count += 1
                else:
                    tool.failure_count += 1
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error incrementing call count: {str(e)}")
            self.session.rollback()
            return False
    
    def update_avg_execution_time(
        self,
        tool_id: str,
        execution_time: float
    ) -> bool:
        """更新平均执行时间"""
        try:
            tool = self.get_by_id(tool_id)
            if tool:
                # 计算新的平均执行时间
                if tool.avg_execution_time:
                    # 基于现有平均和新的执行时间计算
                    # 简化实现：使用移动平均
                    tool.avg_execution_time = (tool.avg_execution_time * 0.9 + execution_time * 0.1)
                else:
                    tool.avg_execution_time = execution_time
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating avg execution time: {str(e)}")
            self.session.rollback()
            return False
    
    def update_tool_version(
        self,
        tool_id: str,
        new_version: str
    ) -> bool:
        """更新工具版本"""
        try:
            return self.update_tool(tool_id, version=new_version) is not None
        except Exception as e:
            logger.error(f"Error updating tool version: {str(e)}")
            return False
    
    def update_tool_config(
        self,
        tool_id: str,
        config: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """更新工具配置"""
        try:
            tool = self.get_by_id(tool_id)
            if tool:
                if merge and tool.config:
                    tool.config.update(config)
                else:
                    tool.config = config
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating tool config: {str(e)}")
            self.session.rollback()
            return False
