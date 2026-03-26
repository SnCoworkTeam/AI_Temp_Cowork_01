"""
工具服务
工具业务逻辑层（集成数据库）
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID
import time

from ..repositories.tool_repository import ToolRepository
from ..repositories.execution_repository import ExecutionRepository
from ..core.rate_limiter import RateLimiter
from ..core.config_manager import ConfigManager
from ..core.audit import AuditLogger
from ..tools.tool_registry import ToolRegistry, ToolExecutionError

logger = logging.getLogger(__name__)


class ToolService:
    """工具服务（集成数据库）"""
    
    def __init__(self, db: Session, tool_registry: Optional[ToolRegistry] = None):
        self.db = db
        self.tool_repo = ToolRepository(db)
        self.execution_repo = ExecutionRepository(db)
        self.rate_limiter = RateLimiter(db)
        self.config_manager = ConfigManager(db)
        self.audit_logger = AuditLogger(db)
        self.tool_registry = tool_registry or ToolRegistry()
    
    async def register_tool(
        self,
        tool_def: Dict[str, Any],
        overwrite: bool = False,
        executor: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        注册工具
        
        Args:
            tool_def: 工具定义字典
            overwrite: 是否覆盖已存在的工具
            executor: 工具执行器（可选）
        
        Returns:
            注册结果
        """
        try:
            # 检查工具是否已存在
            existing = self.tool_repo.get_by_name(tool_def["name"])
            
            if existing and not overwrite:
                raise ValueError(f"Tool '{tool_def['name']}' already exists. Use overwrite=True to replace it.")
            
            # 创建或更新工具记录
            if existing:
                # 更新现有工具
                tool = self.tool_repo.update_tool(
                    str(existing.id),
                    description=tool_def.get("description", existing.description),
                    version=tool_def.get("version", existing.version),
                    tool_type=tool_def.get("tool_type", "custom"),
                    parameters=tool_def.get("parameters", {}),
                    required_parameters=tool_def.get("required_parameters", []),
                    return_type=tool_def.get("returns", {}).get("type") if tool_def.get("returns") else None,
                    config=tool_def.get("config", {}),
                    metadata=tool_def.get("metadata", {})
                )
                tool_id = str(existing.id)
            else:
                # 创建新工具
                tool = self.tool_repo.create_tool(
                    name=tool_def["name"],
                    description=tool_def.get("description", ""),
                    version=tool_def.get("version", "1.0.0"),
                    tool_type=tool_def.get("tool_type", "custom"),
                    parameters=tool_def.get("parameters", {}),
                    required_parameters=tool_def.get("required_parameters", []),
                    return_type=tool_def.get("returns", {}).get("type") if tool_def.get("returns") else None,
                    config=tool_def.get("config", {}),
                    metadata=tool_def.get("metadata", {})
                )
                tool_id = str(tool.id)
            
            self.db.commit()
            
            # 注册到内存注册表（用于执行）
            from ..models.tool_models import ToolDefinition
            pydantic_tool = ToolDefinition(**tool_def)
            self.tool_registry.register_tool(pydantic_tool, executor=executor, overwrite=overwrite)
            
            # 数据变更时：注册工具元数据到元数据服务
            try:
                from ..services.metadata_client import get_metadata_client
                from ..models.tool_metadata import ToolMetadataCreate
                
                metadata_client = get_metadata_client()
                tool_metadata = ToolMetadataCreate(
                    tool_name=tool.name,
                    description=tool.description or "",
                    category=tool.metadata.get("category", "general") if tool.metadata else "general",
                    input_schema=tool.parameters or {},
                    output_schema={"type": tool.return_type} if tool.return_type else {},
                    tags=tool.metadata.get("tags", []) if tool.metadata else [],
                    version=tool.version
                )
                await metadata_client.create_tool_metadata(tool_metadata)
            except Exception as e:
                logger.warning(f"Failed to register tool metadata: {str(e)}")
            
            # 向量化工具元数据（用于语义搜索）
            try:
                from ..services.tool_vectorization_service import get_tool_vectorization_service
                
                vectorization_service = get_tool_vectorization_service()
                await vectorization_service.vectorize_tool_metadata(
                    tool_name=tool.name,
                    tool_description=tool.description or "",
                    tool_parameters=tool.parameters or {},
                    tool_metadata=tool.metadata or {}
                )
                logger.info(f"Tool metadata vectorized: {tool.name}")
            except Exception as e:
                logger.warning(f"Failed to vectorize tool metadata: {str(e)}")
            
            logger.info(f"Tool registered: {tool_def['name']} (id: {tool_id})")
            
            return {
                "success": True,
                "tool_id": tool_id,
                "tool_name": tool_def["name"],
                "message": f"Tool '{tool_def['name']}' registered successfully"
            }
            
        except Exception as e:
            logger.error(f"Error registering tool: {str(e)}", exc_info=True)
            self.db.rollback()
            raise
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        executed_by: Optional[str] = None,
        workflow_execution_id: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            parameters: 执行参数
            executed_by: 执行者ID
            workflow_execution_id: 关联工作流执行ID
            timeout: 超时时间（秒）
        
        Returns:
            执行结果
        """
        start_time = time.time()
        execution_id = None
        
        try:
            # 获取工具
            tool = self.tool_repo.get_by_name(tool_name)
            if not tool:
                raise ValueError(f"Tool '{tool_name}' not found")
            
            tool_id = str(tool.id)
            
            # 检查工具状态
            if tool.status.value != "active":
                raise ValueError(f"Tool '{tool_name}' is not active (status: {tool.status.value})")
            
            # 检查频率限制
            config = tool.config or {}
            rate_limits = config.get("rate_limits", {})
            
            executed_by_uuid = None
            if executed_by:
                try:
                    executed_by_uuid = UUID(executed_by)
                except ValueError:
                    pass
            
            allowed, error_msg = self.rate_limiter.check_rate_limit(
                tool_id=tool_id,
                user_id=executed_by,
                max_calls_per_minute=rate_limits.get("per_minute"),
                max_calls_per_hour=rate_limits.get("per_hour"),
                max_calls_per_day=rate_limits.get("per_day")
            )
            
            if not allowed:
                raise ValueError(error_msg or "Rate limit exceeded")
            
            # 创建执行记录
            execution = self.execution_repo.create_execution(
                tool_id=tool_id,
                executed_by=executed_by_uuid,
                workflow_execution_id=workflow_execution_id,
                parameters=parameters,
                metadata={"timeout": timeout}
            )
            execution_id = str(execution.id)
            self.db.commit()
            
            # 标记执行开始
            self.execution_repo.start_execution(execution_id)
            self.db.commit()
            
            # 执行工具
            from ..models.tool_models import ToolExecutionRequest
            execution_request = ToolExecutionRequest(
                parameters=parameters,
                timeout=timeout
            )
            
            try:
                execution_response = await self.tool_registry.execute_tool(
                    tool_name,
                    execution_request
                )
                
                execution_time = time.time() - start_time
                
                # 标记执行完成
                self.execution_repo.complete_execution(
                    execution_id=execution_id,
                    result=execution_response.result,
                    execution_time=execution_time
                )
                
                # 更新工具统计
                self.tool_repo.increment_call_count(tool_id, success=True)
                self.tool_repo.update_avg_execution_time(tool_id, execution_time)
                
                self.db.commit()
                
                # 工具执行时：收集使用统计到元数据服务
                try:
                    from ..services.metadata_client import get_metadata_client
                    metadata_client = get_metadata_client()
                    await metadata_client.update_usage_statistics(
                        tool_name,
                        {
                            "total_calls": self.tool_repo.get_tool(tool_id).call_count if hasattr(self.tool_repo, 'get_tool') else 1,
                            "successful_calls": 1,
                            "average_execution_time": execution_time,
                            "last_execution_time": datetime.now().isoformat(),
                            "last_execution_success": True
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to update metadata usage statistics: {str(e)}")
                
                # 追踪MCP工具执行血缘
                try:
                    import httpx
                    from ..config import settings
                    async with httpx.AsyncClient() as client:
                        lineage_data = {
                            "tool_name": tool_name,
                            "input_data": parameters,
                            "output_data": execution_response.result,
                            "execution_id": execution_id,
                            "execution_time": execution_time
                        }
                        await client.post(
                            f"{getattr(settings, 'METADATA_SERVICE_URL', 'http://metadata-service:8005')}/api/collection/lineage/tool-execution",
                            json=lineage_data
                        )
                except Exception as e:
                    logger.warning(f"Failed to track tool execution lineage: {str(e)}")
                
                # 记录审计日志
                self.audit_logger.log_execution(
                    execution_id=execution_id,
                    tool_id=tool_id,
                    tool_name=tool_name,
                    executed_by=executed_by,
                    parameters=parameters,
                    result=execution_response.result,
                    success=True,
                    execution_time=execution_time
                )
                
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "tool_name": tool_name,
                    "result": execution_response.result,
                    "execution_time": execution_time
                }
                
            except ToolExecutionError as e:
                execution_time = time.time() - start_time
                
                # 标记执行失败
                self.execution_repo.fail_execution(
                    execution_id=execution_id,
                    error_message=e.message,
                    execution_time=execution_time
                )
                
                # 更新工具统计
                self.tool_repo.increment_call_count(tool_id, success=False)
                
                self.db.commit()
                
                # 记录审计日志
                self.audit_logger.log_execution(
                    execution_id=execution_id,
                    tool_id=tool_id,
                    tool_name=tool_name,
                    executed_by=executed_by,
                    parameters=parameters,
                    result=None,
                    success=False,
                    execution_time=execution_time,
                    error_message=e.message
                )
                
                raise ValueError(f"Tool execution failed: {e.message}")
            
            except Exception as e:
                execution_time = time.time() - start_time
                
                # 标记执行失败
                if execution_id:
                    self.execution_repo.fail_execution(
                        execution_id=execution_id,
                        error_message=str(e),
                        execution_time=execution_time
                    )
                
                # 更新工具统计
                self.tool_repo.increment_call_count(tool_id, success=False)
                
                self.db.commit()
                
                # 记录审计日志
                if execution_id:
                    self.audit_logger.log_execution(
                        execution_id=execution_id,
                        tool_id=tool_id,
                        tool_name=tool_name,
                        executed_by=executed_by,
                        parameters=parameters,
                        result=None,
                        success=False,
                        execution_time=execution_time,
                        error_message=str(e)
                    )
                
                raise
        
        except Exception as e:
            logger.error(f"Error executing tool: {str(e)}", exc_info=True)
            self.db.rollback()
            raise
    
    async def list_tools(
        self,
        page: int = 1,
        page_size: int = 100,
        status: Optional[str] = None,
        tool_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """列出工具"""
        try:
            skip = (page - 1) * page_size
            tools = self.tool_repo.list_tools(
                skip=skip,
                limit=page_size,
                status=status,
                tool_type=tool_type
            )
            
            # 转换为字典
            tool_dicts = []
            for tool in tools:
                tool_dicts.append({
                    "tool_id": str(tool.id),
                    "name": tool.name,
                    "description": tool.description,
                    "version": tool.version,
                    "tool_type": tool.tool_type.value if hasattr(tool.tool_type, 'value') else str(tool.tool_type),
                    "status": tool.status.value if hasattr(tool.status, 'value') else str(tool.status),
                    "call_count": tool.call_count,
                    "success_count": tool.success_count,
                    "failure_count": tool.failure_count,
                    "avg_execution_time": tool.avg_execution_time,
                    "created_at": tool.created_at.isoformat() if tool.created_at else None,
                    "updated_at": tool.updated_at.isoformat() if tool.updated_at else None
                })
            
            return {
                "tools": tool_dicts,
                "total": len(tool_dicts),  # 简化实现
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}", exc_info=True)
            return {
                "tools": [],
                "total": 0,
                "page": page,
                "page_size": page_size
            }
    
    async def search_tools(
        self,
        query: str,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """搜索工具"""
        try:
            # 从内存注册表搜索（包含所有已注册的工具）
            all_tools = self.tool_registry.list_tools()
            
            # 过滤匹配的工具
            query_lower = query.lower()
            matched_tools = []
            for tool_data in all_tools:
                name = tool_data.get("name", "").lower()
                description = tool_data.get("description", "").lower()
                
                if query_lower in name or query_lower in description:
                    matched_tools.append(tool_data)
            
            # 分页
            skip = (page - 1) * page_size
            paginated_tools = matched_tools[skip:skip + page_size]
            
            return {
                "tools": paginated_tools,
                "total": len(matched_tools),
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"Error searching tools: {str(e)}", exc_info=True)
            return {
                "tools": [],
                "total": 0,
                "page": page,
                "page_size": page_size
            }
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        try:
            tool = self.tool_repo.get_by_name(tool_name)
            if not tool:
                return None
            
            # 获取统计信息
            stats = self.execution_repo.get_statistics(tool_id=str(tool.id))
            
            return {
                "tool_id": str(tool.id),
                "name": tool.name,
                "description": tool.description,
                "version": tool.version,
                "tool_type": tool.tool_type.value if hasattr(tool.tool_type, 'value') else str(tool.tool_type),
                "status": tool.status.value if hasattr(tool.status, 'value') else str(tool.status),
                "parameters": tool.parameters or {},
                "required_parameters": tool.required_parameters or [],
                "return_type": tool.return_type,
                "config": tool.config or {},
                "metadata": tool.metadata or {},
                "statistics": {
                    "call_count": tool.call_count,
                    "success_count": tool.success_count,
                    "failure_count": tool.failure_count,
                    "success_rate": (tool.success_count / tool.call_count * 100) if tool.call_count > 0 else 0.0,
                    "avg_execution_time": tool.avg_execution_time,
                    **stats
                },
                "rate_limit_info": self.rate_limiter.get_rate_limit_info(str(tool.id)),
                "created_at": tool.created_at.isoformat() if tool.created_at else None,
                "updated_at": tool.updated_at.isoformat() if tool.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting tool info: {str(e)}", exc_info=True)
            return None
    
    async def unregister_tool(self, tool_name: str) -> bool:
        """注销工具"""
        try:
            tool = self.tool_repo.get_by_name(tool_name)
            if not tool:
                return False
            
            # 标记为deprecated
            success = self.tool_repo.delete_tool(str(tool.id))
            
            if success:
                self.db.commit()
                # 从内存注册表移除
                self.tool_registry.unregister_tool(tool_name)
                
                # 记录审计日志
                self.audit_logger.log_tool_registration(
                    tool_id=str(tool.id),
                    tool_name=tool_name,
                    registered_by=None,  # 可以从请求中获取
                    action="unregister"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error unregistering tool: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    async def get_execution_history(
        self,
        tool_id: Optional[str] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """获取执行历史"""
        try:
            skip = (page - 1) * page_size
            
            if tool_id:
                executions = self.execution_repo.get_by_tool_id(tool_id, skip=skip, limit=page_size)
            elif user_id:
                executions = self.execution_repo.get_by_user_id(user_id, skip=skip, limit=page_size)
            else:
                executions = self.execution_repo.get_recent_executions(limit=page_size)
            
            execution_dicts = []
            for execution in executions:
                execution_dicts.append({
                    "execution_id": str(execution.id),
                    "tool_id": str(execution.tool_id),
                    "status": execution.status.value if hasattr(execution.status, 'value') else str(execution.status),
                    "execution_time": execution.execution_time,
                    "start_time": execution.start_time.isoformat() if execution.start_time else None,
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "error_message": execution.error_message,
                    "created_at": execution.created_at.isoformat() if execution.created_at else None
                })
            
            return {
                "executions": execution_dicts,
                "page": page,
                "page_size": page_size,
                "total": len(execution_dicts)
            }
            
        except Exception as e:
            logger.error(f"Error getting execution history: {str(e)}", exc_info=True)
            return {
                "executions": [],
                "page": page,
                "page_size": page_size,
                "total": 0
            }
    
    def update_tool_config(
        self,
        tool_id: str,
        config: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """更新工具配置"""
        return self.config_manager.update_tool_config(tool_id, config, merge=merge)
    
    def get_tool_config(self, tool_id: str) -> Dict[str, Any]:
        """获取工具配置"""
        return self.config_manager.get_tool_config(tool_id)
    
    def set_credentials(
        self,
        tool_id: str,
        credential_key: str,
        credential_value: Dict[str, Any]
    ) -> bool:
        """设置认证凭据"""
        return self.config_manager.set_credentials(tool_id, credential_key, credential_value)
    
    def get_credentials(
        self,
        tool_id: str,
        credential_key: str
    ) -> Optional[Dict[str, Any]]:
        """获取认证凭据"""
        return self.config_manager.get_credentials(tool_id, credential_key)

