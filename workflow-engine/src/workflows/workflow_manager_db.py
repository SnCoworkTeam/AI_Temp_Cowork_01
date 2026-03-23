"""
工作流管理器（数据库集成版本）
使用PostgreSQL存储工作流定义和执行历史
"""
from typing import Dict, List, Any, Optional
import logging
import uuid
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
import sys
from pathlib import Path
import httpx
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ..models.workflow_models import (
    WorkflowDefinition,
    WorkflowDetailResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse
)
from shared_libs.luminaos_common.schemas.workflow_schemas import ExecutionStatus
from ..repositories.workflow_repository import WorkflowRepository
from ..repositories.execution_repository import ExecutionRepository
from ..repositories.node_repository import NodeRepository
from ..core.state_manager import WorkflowStateManager
from ..core.performance_monitor import WorkflowPerformanceMonitor

logger = logging.getLogger(__name__)


# 自定义异常类
class WorkflowEngineError(Exception):
    """工作流引擎基础异常"""
    pass


class WorkflowNotFoundError(WorkflowEngineError):
    """工作流未找到异常"""
    pass


class WorkflowDataError(WorkflowEngineError):
    """工作流数据错误异常"""
    pass


class NodeExecutionError(WorkflowEngineError):
    """节点执行错误异常"""
    pass


class ConfigurationError(WorkflowEngineError):
    """配置错误异常"""
    pass


class WorkflowManagerDB:
    """工作流管理器（数据库版本）"""
    
    def __init__(self, db: Session):
        self.db = db
        self.workflow_repo = WorkflowRepository(db)
        self.execution_repo = ExecutionRepository(db)
        self.node_repo = NodeRepository(db)
        self.state_manager = WorkflowStateManager(db)
        self.performance_monitor = WorkflowPerformanceMonitor(db)
    
    async def save_workflow(
        self,
        workflow: WorkflowDefinition,
        overwrite: bool = False,
        create_version: bool = False,
        created_by: Optional[str] = None
    ) -> str:
        """
        保存工作流
        
        Args:
            workflow: 工作流定义
            overwrite: 是否覆盖已存在的工作流
            create_version: 是否创建新版本
            created_by: 创建者ID
        
        Returns:
            工作流ID
        """
        try:
            created_by_uuid = None
            if created_by:
                try:
                    created_by_uuid = uuid.UUID(created_by)
                except ValueError as e:
                    logger.warning(f"Invalid created_by UUID format: {created_by}, error: {e}")
                    # 不抛出异常，但记录警告
            
            # 检查是否已存在同名工作流（按名称和版本检查）
            # 注意：允许同名但不同版本的工作流存在
            workflow_version = workflow.version or "1.0.0"
            existing = self.workflow_repo.get_by_name_and_version(workflow.name, workflow_version)
            
            if existing:
                if create_version:
                    # 创建新版本（自动递增版本号）
                    db_workflow = self.workflow_repo.create_new_version(
                        name=workflow.name,
                        description=workflow.description,
                        created_by=created_by_uuid,
                        config=self._workflow_to_db_config(workflow),
                        metadata={"source": "workflow_designer"}
                    )
                elif overwrite:
                    # 更新现有版本
                    db_workflow = self.workflow_repo.update_workflow(
                        str(existing.id),
                        description=workflow.description,
                        config=self._workflow_to_db_config(workflow),
                        workflow_metadata={"source": "workflow_designer", "updated_at": datetime.utcnow().isoformat()}  # 使用正确的字段名
                    )
                    if not db_workflow:
                        raise ValueError("Failed to update workflow")
                else:
                    # 如果同名同版本已存在，自动创建新版本而不是报错
                    logger.info(f"Workflow '{workflow.name}' version '{workflow_version}' already exists, creating new version")
                    db_workflow = self.workflow_repo.create_new_version(
                        name=workflow.name,
                        description=workflow.description,
                        created_by=created_by_uuid,
                        config=self._workflow_to_db_config(workflow),
                        metadata={"source": "workflow_designer"}
                    )
            else:
                # 创建新工作流
                db_workflow = self.workflow_repo.create_workflow(
                    name=workflow.name,
                    description=workflow.description,
                    version=workflow_version,
                    status="draft",
                    created_by=created_by_uuid,
                    config=self._workflow_to_db_config(workflow),
                    metadata={"source": "workflow_designer"}
                )
            
            workflow_id = str(db_workflow.id)
            
            # 保存节点和连接
            await self._save_nodes_and_connections(workflow_id, workflow)
            
            self.db.commit()

            logger.info(f"Workflow saved: {workflow.name} (id: {workflow_id})")
            
            # 同步工作流元数据到元数据服务
            try:
                await self._sync_workflow_metadata(workflow_id, workflow)
            except Exception as e:
                logger.warning(f"Failed to sync workflow metadata for {workflow_id}: {str(e)}")
                # 不阻止工作流保存，但会影响元数据功能
            
            return workflow_id
        
        except Exception as e:
            logger.error(f"Error saving workflow: {str(e)}", exc_info=True)
            # rollback由get_db依赖自动处理，这里直接抛出异常
            raise
    
    async def _sync_workflow_metadata(
        self,
        workflow_id: str,
        workflow: WorkflowDefinition
    ):
        """
        同步工作流元数据到元数据服务
        
        Args:
            workflow_id: 工作流ID
            workflow: 工作流定义
        """
        try:
            metadata_service_url = os.getenv(
                "METADATA_SERVICE_URL",
                "http://metadata-service:8005"
            )
            
            # 提取节点类型和工具信息
            node_types = []
            tool_names = []
            for node in workflow.nodes:
                node_type = node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type)
                node_types.append(node_type)
                
                # 如果是工具节点，提取工具名称
                if node_type == "tool" and node.config:
                    tool_name = node.config.get("tool_name") or node.config.get("name")
                    if tool_name:
                        tool_names.append(tool_name)
            
            # 构建工作流元数据
            workflow_metadata = {
                "workflow_id": workflow_id,
                "name": workflow.name,
                "display_name": workflow.name,
                "description": workflow.description or "",
                "category": "workflow",
                "workflow_type": "custom",
                "input_schema": workflow.input_schema if hasattr(workflow, 'input_schema') else {},
                "output_schema": workflow.output_schema if hasattr(workflow, 'output_schema') else {},
                "dependencies": {
                    "tools": list(set(tool_names))  # 去重
                },
                "tags": workflow.tags if hasattr(workflow, 'tags') else [],
                "metadata": {
                    "node_types": list(set(node_types)),  # 去重
                    "node_count": len(workflow.nodes),
                    "connection_count": len(workflow.connections),
                    "version": workflow.version or "1.0.0",
                    "source": "workflow_engine"
                }
            }
            
            # 发送到元数据服务
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{metadata_service_url}/api/workflows",
                    json=workflow_metadata
                )
                response.raise_for_status()
                logger.info(f"Workflow metadata synced to metadata service: {workflow_id}")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to sync workflow metadata: HTTP {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Error syncing workflow metadata: {str(e)}", exc_info=True)
    
    async def _save_nodes_and_connections(
        self,
        workflow_id: str,
        workflow: WorkflowDefinition
    ):
        """保存节点和连接"""
        try:
            # 先删除连接，再删除节点（避免外键约束问题）
            # 删除方法内部已经调用了 flush()，所以这里不需要额外调用
            self.node_repo.delete_workflow_connections(workflow_id)
            # 等待连接删除完成后再删除节点
            self.node_repo.delete_workflow_nodes(workflow_id)
            
            # 保存节点
            for node in workflow.nodes:
                position = None
                if node.position:
                    position = {"x": node.position.x, "y": node.position.y}
                
                style = node.style or {}
                
                self.node_repo.create_node(
                    workflow_id=workflow_id,
                    node_id=node.id,
                    name=node.name or node.id,
                    node_type=node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                    description=node.description,
                    config=node.config or {},
                    position=position,
                    style=style
                )
            
            # 保存连接
            for conn in workflow.connections:
                self.node_repo.create_connection(
                    workflow_id=workflow_id,
                    source_node_id=conn.source.node_id,
                    target_node_id=conn.target.node_id,
                    condition=conn.condition,
                    label=conn.label,
                    style=conn.style or {}
                )
            
        except Exception as e:
            logger.error(f"Error saving nodes and connections: {str(e)}", exc_info=True)
            raise
    
    async def get_workflow_by_id(self, workflow_id: str) -> Optional[WorkflowDetailResponse]:
        """根据ID获取工作流详情"""
        try:
            db_workflow = self.workflow_repo.get_by_id(workflow_id)
            if not db_workflow:
                return None
            
            # 加载节点和连接
            nodes = self.node_repo.get_by_workflow_id(workflow_id)
            connections = self.node_repo.get_connections_by_workflow_id(workflow_id)
            
            # 转换为Pydantic模型
            workflow_def = self._db_workflow_to_pydantic(db_workflow, nodes, connections)
            
            # 获取执行统计
            execution_stats = self.execution_repo.get_statistics(workflow_id=workflow_id)
            
            # 获取最后执行时间
            executions = self.execution_repo.get_by_workflow_id(workflow_id, skip=0, limit=1)
            last_executed_at = None
            if executions:
                last_executed_at = executions[0].created_at
            
            return WorkflowDetailResponse(
                workflow=workflow_def,
                workflow_id=workflow_id,
                created_at=db_workflow.created_at,
                updated_at=db_workflow.updated_at,
                version=db_workflow.version,
                execution_count=execution_stats.get("total", 0),
                last_executed_at=last_executed_at
            )
            
        except Exception as e:
            logger.error(f"Error getting workflow: {str(e)}", exc_info=True)
            return None
    
    async def get_workflow_by_name(
        self,
        workflow_name: str,
        version: Optional[str] = None
    ) -> Optional[WorkflowDetailResponse]:
        """根据名称获取工作流详情"""
        try:
            if version:
                db_workflow = self.workflow_repo.get_by_name_and_version(workflow_name, version)
            else:
                db_workflow = self.workflow_repo.get_active_version(workflow_name)
                if not db_workflow:
                    db_workflow = self.workflow_repo.get_latest_version(workflow_name)
            
            if not db_workflow:
                return None
            
            return await self.get_workflow_by_id(str(db_workflow.id))
            
        except Exception as e:
            logger.error(f"Error getting workflow by name: {str(e)}", exc_info=True)
            return None
    
    async def list_workflows(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出工作流"""
        try:
            # 如果 session 处于错误状态，先回滚
            if self.db.is_active and self.db.in_transaction():
                try:
                    self.db.rollback()
                except Exception:
                    pass
            
            created_by_uuid = None
            if created_by:
                try:
                    created_by_uuid = uuid.UUID(created_by)
                except ValueError as e:
                    logger.warning(f"Invalid created_by UUID format: {created_by}, error: {e}")
                    # 不抛出异常，但记录警告
            
            skip = (page - 1) * page_size
            workflows = self.workflow_repo.list_workflows(
                skip=skip,
                limit=page_size,
                status=status,
                created_by=created_by_uuid,
                search=search
            )
            
            # 转换为响应格式
            result = []
            for w in workflows:
                try:
                    stats = self.execution_repo.get_statistics(workflow_id=str(w.id))
                except Exception as e:
                    logger.warning(f"Error getting statistics for workflow {w.id}: {str(e)}")
                    stats = {"total": 0}
                
                try:
                    executions = self.execution_repo.get_by_workflow_id(str(w.id), skip=0, limit=1)
                    last_executed_at = None
                    if executions:
                        last_executed_at = executions[0].created_at
                except Exception as e:
                    logger.warning(f"Error getting executions for workflow {w.id}: {str(e)}")
                    last_executed_at = None
                
                result.append({
                    "id": str(w.id),
                    "name": w.name,
                    "description": w.description,
                    "version": w.version,
                    "status": w.status.value if hasattr(w.status, 'value') else str(w.status),
                    "created_at": w.created_at.isoformat() if w.created_at else None,
                    "updated_at": w.updated_at.isoformat() if w.updated_at else None,
                    "execution_count": stats.get("total", 0) if isinstance(stats, dict) else 0,
                    "last_executed_at": last_executed_at.isoformat() if last_executed_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing workflows: {str(e)}", exc_info=True)
            return []
    
    async def get_workflow_count(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> int:
        """获取工作流总数"""
        try:
            # 如果 session 处于错误状态，先回滚
            if self.db.is_active and self.db.in_transaction():
                try:
                    self.db.rollback()
                except Exception:
                    pass
            
            workflows = self.workflow_repo.list_workflows(
                skip=0,
                limit=10000,  # 获取所有用于计数
                status=status,
                search=search
            )
            return len(workflows)
        except Exception as e:
            logger.error(f"Error getting workflow count: {str(e)}", exc_info=True)
            # 发生错误时回滚
            try:
                self.db.rollback()
            except Exception:
                pass
            return 0
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        try:
            success = self.workflow_repo.delete_workflow(workflow_id)
            if success:
                self.db.commit()
            return success
        except Exception as e:
            logger.error(f"Error deleting workflow: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    async def list_versions(self, workflow_name: str) -> List[Dict[str, Any]]:
        """列出工作流的所有版本"""
        try:
            return self.workflow_repo.list_versions(workflow_name)
        except Exception as e:
            logger.error(f"Error listing versions: {str(e)}", exc_info=True)
            return []
    
    async def execute_workflow(
        self,
        workflow_id: str,
        request: WorkflowExecutionRequest,
        executed_by: Optional[str] = None
    ) -> WorkflowExecutionResponse:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            request: 执行请求
            executed_by: 执行者ID
        
        Returns:
            执行响应
        """
        import time
        
        try:
            # 获取工作流定义
            workflow_detail = await self.get_workflow_by_id(workflow_id)
            if not workflow_detail:
                raise ValueError(f"Workflow '{workflow_id}' not found")
            
            workflow = workflow_detail.workflow
            
            # 创建执行记录
            executed_by_uuid = None
            if executed_by:
                try:
                    executed_by_uuid = uuid.UUID(executed_by)
                except ValueError as e:
                    logger.warning(f"Invalid executed_by UUID format: {executed_by}, error: {e}")
                    # 不抛出异常，但记录警告
            
            # 安全地获取 request_id（如果存在）
            request_id = getattr(request, 'request_id', None)
            execution = self.execution_repo.create_execution(
                workflow_id=workflow_id,
                executed_by=executed_by_uuid,
                input_data=request.input_data or {},
                metadata={"request_id": request_id} if request_id else {}
            )
            
            execution_id = str(execution.id)
            
            # 初始化状态
            initial_state = {
                "input": request.input_data or {},
                "context": request.context or {},
                "current_node": None,
                "node_results": {},
                "variables": {}
            }
            await self.state_manager.save_state(execution_id, initial_state, is_active=True)
            
            # 标记执行开始
            self.execution_repo.start_execution(execution_id)
            self.db.commit()
            
            start_time = time.time()
            
            try:
                # 使用动态工作流引擎执行
                from ..core.dynamic_workflow_engine import DynamicWorkflowEngine
                
                # 转换为JSON配置
                workflow_config = self._workflow_definition_to_config(workflow)
                
                # 创建引擎实例
                engine = DynamicWorkflowEngine()
                try:
                    temp_workflow_id = engine.build_from_config(workflow_config)
                except Exception as build_error:
                    logger.error(f"Failed to build workflow graph: {str(build_error)}", exc_info=True)
                    # 如果构建失败，仍然尝试执行（会使用模拟模式）
                    # 生成一个临时ID用于执行
                    import uuid
                    temp_workflow_id = f"wf-{uuid.uuid4().hex[:12]}"
                    # 手动构建工作流定义并添加到引擎
                    from ..core.config_parser import WorkflowConfigParser
                    parser = WorkflowConfigParser()
                    workflow_def = parser.parse(workflow_config)
                    engine._workflow_definitions[temp_workflow_id] = workflow_def
                    engine._workflows[temp_workflow_id] = None  # None表示使用模拟模式
                    logger.warning(f"Using simulation mode for workflow {workflow_id} due to build error")
                
                # 合并输入数据和上下文
                combined_input = {**(request.input_data or {}), **(request.context or {})}
                
                # 执行工作流（带状态更新回调）
                execution_result = await self._execute_with_state_tracking(
                    engine,
                    temp_workflow_id,
                    combined_input,
                    execution_id,
                    request.timeout
                )
                
                execution_time = time.time() - start_time
                
                # 标记执行完成
                self.execution_repo.complete_execution(
                    execution_id=execution_id,
                    output_data=execution_result.get("result", {}),
                    progress=1.0
                )
                
                # 记录性能指标
                self.performance_monitor.record_workflow_execution(
                    workflow_id=workflow_id,
                    execution_id=execution_id,
                    duration=execution_time,
                    success=execution_result.get("success", False)
                )
                
                # 工作流运行时：收集执行指标到元数据服务
                try:
                    from ..services.metadata_integration import MetadataIntegration
                    metadata_integration = MetadataIntegration()
                    await metadata_integration.update_execution_statistics(
                        str(workflow_id),
                        {
                            "total_executions": execution.execution_count + 1 if hasattr(execution, 'execution_count') else 1,
                            "last_execution_time": datetime.now().isoformat(),
                            "last_execution_success": execution_result.get("success", False)
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to update metadata execution metrics: {str(e)}")
                
                # 追踪工作流执行血缘
                try:
                    import httpx
                    from ..config import settings
                    
                    # 构建节点执行信息
                    node_executions = []
                    node_results = execution_result.get("node_results", {})
                    for node_id, node_result in node_results.items():
                        node_exec = {
                            "node_id": node_id,
                            "node_type": node_result.get("node_type", "unknown"),
                            "input_data": node_result.get("input", {}),
                            "output_data": node_result.get("output", {}),
                            "execution_time": node_result.get("execution_time"),
                            "success": node_result.get("success", True)
                        }
                        node_executions.append(node_exec)
                    
                    # 发送到元数据服务
                    async with httpx.AsyncClient() as client:
                        lineage_data = {
                            "workflow_id": str(workflow_id),
                            "execution_id": execution_id,
                            "node_executions": node_executions
                        }
                        await client.post(
                            f"{getattr(settings, 'METADATA_SERVICE_URL', 'http://metadata-service:8005')}/api/collection/lineage/workflow-execution",
                            json=lineage_data
                        )
                except Exception as e:
                    logger.warning(f"Failed to track workflow execution lineage: {str(e)}")
                
                self.db.commit()
                
                # 判断执行是否成功
                success = execution_result.get("success", True)
                if not success:
                    # 如果有错误信息，也标记为失败
                    if execution_result.get("error"):
                        success = False
                
                return WorkflowExecutionResponse(
                    success=success,
                    execution_id=execution_id,
                    workflow_id=workflow_id,
                    workflow_name=workflow.name,  # 添加必需的 workflow_name
                    status=ExecutionStatus.COMPLETED,
                    result=execution_result.get("result", {}),
                    execution_time=execution_time,
                    node_results=execution_result.get("node_results", {}),
                    metadata=execution_result.get("metadata", {}),
                    error=execution_result.get("error")  # 如果有错误，也包含进去
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # 标记执行失败
                self.execution_repo.fail_execution(
                    execution_id=execution_id,
                    error_message=str(e),
                    node_results={}
                )
                
                # 记录性能指标
                self.performance_monitor.record_workflow_execution(
                    workflow_id=workflow_id,
                    execution_id=execution_id,
                    duration=execution_time,
                    success=False
                )
                
                self.db.commit()
                
                raise
        
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}", exc_info=True)
            self.db.rollback()
            raise
    
    async def _execute_with_state_tracking(
        self,
        engine,
        workflow_id: str,
        input_data: Dict[str, Any],
        execution_id: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """执行工作流并跟踪状态"""
        try:
            # 执行工作流
            result = await engine.execute_workflow(
                workflow_id=workflow_id,
                input_data=input_data,
                timeout=timeout
            )
            
            # 更新状态
            if result.get("state"):
                await self.state_manager.save_state(execution_id, result["state"], is_active=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in state-tracked execution: {str(e)}", exc_info=True)
            raise
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态"""
        try:
            execution = self.execution_repo.get_by_id(execution_id)
            if not execution:
                return None
            
            # 加载状态
            state = await self.state_manager.load_state(execution_id)
            
            return {
                "execution_id": execution_id,
                "workflow_id": str(execution.workflow_id),
                "status": execution.status.value if hasattr(execution.status, 'value') else str(execution.status),
                "progress": execution.progress,
                "current_node_id": execution.current_node_id,
                "input_data": execution.input_data,
                "output_data": execution.output_data,
                "error_message": execution.error_message,
                "node_results": execution.node_results,
                "start_time": execution.start_time.isoformat() if execution.start_time else None,
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "execution_time": execution.execution_time,
                "state": state,
                "metadata": execution.metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting execution status: {str(e)}", exc_info=True)
            return None
    
    async def get_execution_history(
        self,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取执行历史"""
        try:
            if workflow_id:
                executions = self.execution_repo.get_by_workflow_id(workflow_id, skip=skip, limit=limit)
            elif user_id:
                executions = self.execution_repo.get_by_user_id(user_id, skip=skip, limit=limit)
            else:
                # 获取所有执行（需要添加通用方法）
                executions = []
            
            return [
                {
                    "execution_id": str(e.id),
                    "workflow_id": str(e.workflow_id),
                    "status": e.status.value if hasattr(e.status, 'value') else str(e.status),
                    "progress": e.progress,
                    "current_node_id": e.current_node_id,
                    "start_time": e.start_time.isoformat() if e.start_time else None,
                    "end_time": e.end_time.isoformat() if e.end_time else None,
                    "execution_time": e.execution_time
                }
                for e in executions
            ]
            
        except Exception as e:
            logger.error(f"Error getting execution history: {str(e)}", exc_info=True)
            return []
    
    async def replay_execution(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """回放执行"""
        try:
            execution = self.execution_repo.get_by_id(execution_id)
            if not execution:
                raise ValueError(f"Execution '{execution_id}' not found")
            
            # 加载状态
            state = await self.state_manager.load_state(execution_id)
            if not state:
                raise ValueError(f"State not found for execution '{execution_id}'")
            
            # 获取工作流定义
            workflow_detail = await self.get_workflow_by_id(str(execution.workflow_id))
            if not workflow_detail:
                raise ValueError(f"Workflow not found for execution '{execution_id}'")
            
            workflow = workflow_detail.workflow
            
            # 重新执行（使用相同的输入）
            from ..core.dynamic_workflow_engine import DynamicWorkflowEngine
            
            workflow_config = self._workflow_definition_to_config(workflow)
            engine = DynamicWorkflowEngine()
            temp_workflow_id = engine.build_from_config(workflow_config)
            
            input_data = execution.input_data or {}
            result = await engine.execute_workflow(
                workflow_id=temp_workflow_id,
                input_data=input_data
            )
            
            return {
                "original_execution_id": execution_id,
                "replay_result": result,
                "original_state": state
            }
            
        except Exception as e:
            logger.error(f"Error replaying execution: {str(e)}", exc_info=True)
            raise
    
    async def resume_execution(
        self,
        execution_id: str,
        checkpoint_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """从检查点恢复执行"""
        try:
            # 从检查点恢复状态
            state = await self.state_manager.resume_from_checkpoint(execution_id, checkpoint_name)
            if not state:
                raise ValueError(f"Failed to resume from checkpoint: {execution_id}")
            
            # 获取工作流定义
            execution = self.execution_repo.get_by_id(execution_id)
            if not execution:
                raise ValueError(f"Execution '{execution_id}' not found")
            
            workflow_detail = await self.get_workflow_by_id(str(execution.workflow_id))
            if not workflow_detail:
                raise ValueError(f"Workflow not found")
            
            workflow = workflow_detail.workflow
            
            # 继续执行
            from ..core.dynamic_workflow_engine import DynamicWorkflowEngine
            
            workflow_config = self._workflow_definition_to_config(workflow)
            engine = DynamicWorkflowEngine()
            temp_workflow_id = engine.build_from_config(workflow_config)
            
            # 使用恢复的状态继续执行
            result = await self._execute_with_state_tracking(
                engine,
                temp_workflow_id,
                state.get("input", {}),
                execution_id,
                timeout=300
            )
            
            return {
                "execution_id": execution_id,
                "resumed_from_checkpoint": checkpoint_name or "latest",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error resuming execution: {str(e)}", exc_info=True)
            raise
    
    def get_performance_metrics(
        self,
        workflow_id: str,
        node_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            if node_id:
                return self.performance_monitor.get_node_metrics(workflow_id, node_id)
            else:
                return self.performance_monitor.get_workflow_metrics(workflow_id)
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}", exc_info=True)
            return {}
    
    def _workflow_to_db_config(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        """将Pydantic工作流定义转换为数据库配置"""
        return {
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                    "config": node.config or {}
                }
                for node in workflow.nodes
            ],
            "connections": [
                {
                    "id": conn.id,
                    "source": conn.source.node_id,
                    "target": conn.target.node_id,
                    "condition": conn.condition
                }
                for conn in workflow.connections
            ]
        }
    
    def _db_workflow_to_pydantic(
        self,
        db_workflow,
        nodes: List,
        connections: List
    ) -> WorkflowDefinition:
        """将数据库工作流转换为Pydantic模型"""
        from ..models.workflow_models import WorkflowNode, WorkflowConnection, NodePosition, ConnectionPoint
        
        # 转换节点
        pydantic_nodes = []
        for node in nodes:
            position = None
            if node.position:
                position = NodePosition(x=node.position.get("x", 0), y=node.position.get("y", 0))
            
            pydantic_nodes.append(WorkflowNode(
                id=node.node_id,
                name=node.name,
                node_type=node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                description=node.description,
                config=node.config or {},
                position=position,
                style=node.style or {}
            ))
        
        # 转换连接
        pydantic_connections = []
        for conn in connections:
            # 需要找到源和目标节点的node_id
            source_node = next((n for n in nodes if n.id == conn.source_node_id), None)
            target_node = next((n for n in nodes if n.id == conn.target_node_id), None)
            
            if source_node and target_node:
                pydantic_connections.append(WorkflowConnection(
                    id=str(conn.id),
                    source=ConnectionPoint(node_id=source_node.node_id),
                    target=ConnectionPoint(node_id=target_node.node_id),
                    condition=conn.condition,
                    label=conn.label,
                    style=conn.style or {}
                ))
        
        return WorkflowDefinition(
            name=db_workflow.name,
            description=db_workflow.description,
            version=db_workflow.version,
            status=db_workflow.status.value if hasattr(db_workflow.status, 'value') else str(db_workflow.status),
            nodes=pydantic_nodes,
            connections=pydantic_connections
        )
    
    def _workflow_definition_to_config(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        """将WorkflowDefinition转换为JSON配置（用于动态引擎）"""
        # 确保 start_node_id 已设置（如果没有，自动推断）
        start_node_id = workflow.start_node_id
        if not start_node_id and workflow.nodes:
            # 查找类型为 "start" 的节点
            start_nodes = [
                node for node in workflow.nodes 
                if (node.node_type.value == "start" if hasattr(node.node_type, 'value') else str(node.node_type) == "start")
            ]
            if start_nodes:
                start_node_id = start_nodes[0].id
            else:
                # 如果没有 start 节点，使用第一个节点
                start_node_id = workflow.nodes[0].id
        
        return {
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "start_node_id": start_node_id,  # 添加必需的 start_node_id
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                    "config": node.config or {}
                }
                for node in workflow.nodes
            ],
            "connections": [
                {
                    "source": {"node_id": conn.source.node_id},
                    "target": {"node_id": conn.target.node_id},
                    "condition": conn.condition
                }
                for conn in workflow.connections
            ]
        }

