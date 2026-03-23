"""
工作流管理器
使用LangGraph管理工作流的定义和执行
支持工作流设计器的保存、查询和执行功能
"""
from typing import Dict, List, Any, Optional
import logging
import uuid
import asyncio
from datetime import datetime

from ..models.workflow_models import (
    WorkflowDefinition,
    WorkflowDetailResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse
)
from shared_libs.luminaos_common.schemas.workflow_schemas import ExecutionStatus

logger = logging.getLogger(__name__)


class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self):
        # 使用ID作为key存储工作流
        self._workflows: Dict[str, Dict[str, Any]] = {}
        # 使用名称作为key的索引（支持名称查找）
        self._workflow_name_index: Dict[str, str] = {}
        self._executions: Dict[str, Dict[str, Any]] = {}
        # 延迟初始化标志
        self._initialized = False
    
    async def _initialize_default_workflows(self):
        """初始化默认工作流（异步）"""
        if self._initialized:
            return
        
        from ..models.workflow_models import WorkflowNode, WorkflowDefinition
        
        default_node = WorkflowNode(
            id="start",
            name="开始",
            node_type="start"
        )
        
        default_workflow = WorkflowDefinition(
            name="sap_data_analysis",
            description="SAP数据分析工作流",
            version="1.0.0",
            nodes=[default_node],
            start_node_id="start",
            end_node_ids=["start"]
        )
        
        try:
            await self.save_workflow(default_workflow, overwrite=True, skip_init=True)
            self._initialized = True
        except Exception as e:
            logger.warning(f"Failed to register default workflows: {e}")
    
    async def _ensure_initialized(self):
        """确保已初始化"""
        if not self._initialized:
            await self._initialize_default_workflows()
    
    async def save_workflow(
        self,
        workflow: WorkflowDefinition,
        overwrite: bool = False,
        skip_init: bool = False
    ) -> str:
        """
        保存工作流
        
        Args:
            workflow: 工作流定义
            overwrite: 是否覆盖已存在的工作流
        
        Returns:
            工作流ID
        """
        if not skip_init:
            await self._ensure_initialized()
        
        # 检查是否已存在同名工作流
        existing_id = self._workflow_name_index.get(workflow.name)
        
        if existing_id and not overwrite:
            raise ValueError(
                f"Workflow with name '{workflow.name}' already exists. "
                "Use overwrite=True to replace it."
            )
        
        # 生成或使用现有ID
        workflow_id = existing_id or f"wf-{uuid.uuid4().hex}"
        
        # 保存工作流
        workflow_data = {
            "id": workflow_id,
            "definition": workflow,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": workflow.version,
            "execution_count": 0,
            "last_executed_at": None
        }
        
        self._workflows[workflow_id] = workflow_data
        self._workflow_name_index[workflow.name] = workflow_id
        
        logger.info(f"Workflow saved: {workflow.name} (id: {workflow_id})")
        
        return workflow_id
    
    async def get_workflow_by_id(self, workflow_id: str) -> Optional[WorkflowDetailResponse]:
        """
        根据ID获取工作流详情
        
        Args:
            workflow_id: 工作流ID
        
        Returns:
            工作流详情响应，如果不存在则返回None
        """
        await self._ensure_initialized()
        workflow_data = self._workflows.get(workflow_id)
        
        if not workflow_data:
            return None
        
        workflow = workflow_data["definition"]
        
        return WorkflowDetailResponse(
            workflow=workflow,
            workflow_id=workflow_id,
            created_at=datetime.fromisoformat(workflow_data["created_at"]) if workflow_data.get("created_at") else None,
            updated_at=datetime.fromisoformat(workflow_data["updated_at"]) if workflow_data.get("updated_at") else None,
            version=workflow_data["version"],
            execution_count=workflow_data.get("execution_count", 0),
            last_executed_at=datetime.fromisoformat(workflow_data["last_executed_at"]) if workflow_data.get("last_executed_at") else None
        )
    
    async def get_workflow_by_name(self, workflow_name: str) -> Optional[WorkflowDetailResponse]:
        """
        根据名称获取工作流详情
        
        Args:
            workflow_name: 工作流名称
        
        Returns:
            工作流详情响应，如果不存在则返回None
        """
        workflow_id = self._workflow_name_index.get(workflow_name)
        
        if not workflow_id:
            return None
        
        return await self.get_workflow_by_id(workflow_id)
    
    async def list_workflows(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出工作流
        
        Args:
            page: 页码
            page_size: 每页大小
            status: 状态过滤
            search: 搜索关键词
        
        Returns:
            工作流列表
        """
        await self._ensure_initialized()
        workflows = list(self._workflows.values())
        
        # 过滤
        if status:
            workflows = [
                w for w in workflows
                if w["definition"].status.value == status.lower()
            ]
        
        if search:
            search_lower = search.lower()
            workflows = [
                w for w in workflows
                if search_lower in w["definition"].name.lower()
                or search_lower in w["definition"].description.lower()
            ]
        
        # 排序（按更新时间倒序）
        workflows.sort(
            key=lambda x: x.get("updated_at", ""),
            reverse=True
        )
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        workflows = workflows[start:end]
        
        # 转换为响应格式
        result = []
        for w in workflows:
            workflow = w["definition"]
            result.append({
                "id": w["id"],
                "name": workflow.name,
                "description": workflow.description,
                "version": w["version"],
                "status": workflow.status.value,
                "created_at": w["created_at"],
                "updated_at": w["updated_at"],
                "execution_count": w.get("execution_count", 0),
                "last_executed_at": w.get("last_executed_at")
            })
        
        return result
    
    async def get_workflow_count(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> int:
        """
        获取工作流总数
        
        Args:
            status: 状态过滤
            search: 搜索关键词
        
        Returns:
            工作流总数
        """
        workflows = list(self._workflows.values())
        
        if status:
            workflows = [
                w for w in workflows
                if w["definition"].status.value == status.lower()
            ]
        
        if search:
            search_lower = search.lower()
            workflows = [
                w for w in workflows
                if search_lower in w["definition"].name.lower()
                or search_lower in w["definition"].description.lower()
            ]
        
        return len(workflows)
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        删除工作流
        
        Args:
            workflow_id: 工作流ID
        
        Returns:
            是否删除成功
        """
        workflow_data = self._workflows.get(workflow_id)
        
        if not workflow_data:
            return False
        
        # 从名称索引中删除
        workflow_name = workflow_data["definition"].name
        if workflow_name in self._workflow_name_index:
            del self._workflow_name_index[workflow_name]
        
        # 删除工作流
        del self._workflows[workflow_id]
        
        logger.info(f"Workflow deleted: {workflow_id}")
        
        return True
    
    async def execute_workflow_by_id(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        timeout: Optional[int] = 300,
        async_execution: bool = False
    ) -> Dict[str, Any]:
        """
        执行工作流（根据ID）
        
        Args:
            workflow_id: 工作流ID
            input_data: 输入数据
            context: 执行上下文
            timeout: 超时时间
            async_execution: 是否异步执行
        
        Returns:
            执行结果
        """
        import time
        
        workflow_data = self._workflows.get(workflow_id)
        if not workflow_data:
            raise ValueError(f"Workflow with id '{workflow_id}' not found")
        
        workflow = workflow_data["definition"]
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(
            f"Executing workflow: {workflow.name} "
            f"(id: {workflow_id}, execution_id: {execution_id})"
        )
        
        try:
            # 使用动态工作流引擎执行
            from ..core import DynamicWorkflowEngine
            
            # 将WorkflowDefinition转换为JSON配置
            workflow_config = self._workflow_definition_to_config(workflow)
            
            # 创建临时引擎实例
            engine = DynamicWorkflowEngine()
            temp_workflow_id = engine.build_from_config(workflow_config)
            
            # 合并输入数据和上下文
            combined_input = {**input_data, **context}
            
            # 执行工作流
            execution_result = await engine.execute_workflow(
                workflow_id=temp_workflow_id,
                input_data=combined_input,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            # 更新执行统计
            workflow_data["execution_count"] = workflow_data.get("execution_count", 0) + 1
            workflow_data["last_executed_at"] = datetime.now().isoformat()
            
            result = {
                "success": execution_result.get("success", False),
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "workflow_name": workflow.name,
                "status": ExecutionStatus.COMPLETED.value if execution_result.get("success") else ExecutionStatus.FAILED.value,
                "result": execution_result.get("result", {}),
                "error": execution_result.get("error"),
                "execution_time": execution_time,
                "node_results": {},
                "metadata": execution_result.get("metadata", {})
            }
            
            self._executions[execution_id] = {
                **result,
                "workflow_id": workflow_id,
                "context": context
            }
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            result = {
                "success": False,
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "workflow_name": workflow.name,
                "status": ExecutionStatus.FAILED.value,
                "error": str(e),
                "execution_time": execution_time,
                "node_results": {},
                "metadata": {}
            }
            
            self._executions[execution_id] = result
            
            raise
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态"""
        return self._executions.get(execution_id)
    
    # 保持向后兼容的方法
    def register_workflow(self, workflow_def: Dict[str, Any]):
        """注册工作流（向后兼容方法）"""
        from ..models.workflow_models import WorkflowNode, WorkflowDefinition
        
        # 转换为新的模型格式
        nodes = [
            WorkflowNode(
                id=node_id,
                name=node_id,
                node_type="task"
            )
            for node_id in workflow_def.get("nodes", [])
        ]
        
        workflow = WorkflowDefinition(
            name=workflow_def["name"],
            description=workflow_def.get("description", ""),
            version=workflow_def.get("version", "1.0.0"),
            nodes=nodes,
            start_node_id=nodes[0].id if nodes else "start",
            end_node_ids=[nodes[-1].id] if nodes else []
        )
        
        asyncio.run(self.save_workflow(workflow))
    
    def list_workflows_legacy(self) -> List[Dict[str, Any]]:
        """列出工作流（向后兼容方法）"""
        return [
            {
                "name": w["definition"].name,
                "description": w["definition"].description,
                "nodes": [node.id for node in w["definition"].nodes],
                "version": w["version"]
            }
            for w in self._workflows.values()
        ]
    
    def get_workflow_info(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """获取工作流信息（向后兼容方法）"""
        workflow_id = self._workflow_name_index.get(workflow_name)
        if not workflow_id:
            return None
        
        workflow_data = self._workflows[workflow_id]
        workflow = workflow_data["definition"]
        
        return {
            "name": workflow.name,
            "description": workflow.description,
            "nodes": [node.id for node in workflow.nodes],
            "version": workflow_data["version"]
        }
    
    async def execute_workflow(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行工作流（向后兼容方法）"""
        workflow_id = self._workflow_name_index.get(workflow_name)
        if not workflow_id:
            raise ValueError(f"Workflow {workflow_name} not found")
        
        result = await self.execute_workflow_by_id(
            workflow_id=workflow_id,
            input_data=input_data,
            context=context
        )
        
        return {
            "execution_id": result["execution_id"],
            "status": result["status"],
            "result": result["result"]
        }
    
    def _workflow_definition_to_config(self, workflow_def: WorkflowDefinition) -> Dict[str, Any]:
        """将WorkflowDefinition转换为JSON配置格式"""
        nodes_config = []
        for node in workflow_def.nodes:
            node_config = {
                "id": node.id,
                "name": node.name,
                "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                "config": node.config,
                "inputs": node.inputs,
                "outputs": node.outputs,
                "next_nodes": node.next_nodes
            }
            if node.condition:
                node_config["condition"] = node.condition
            if hasattr(node, 'position') and node.position:
                node_config["position"] = {"x": node.position.x, "y": node.position.y}
            if hasattr(node, 'size') and node.size:
                node_config["size"] = {"width": node.size.width, "height": node.size.height}
            nodes_config.append(node_config)
        
        connections_config = []
        for conn in workflow_def.connections:
            conn_config = {
                "id": conn.id,
                "source": {
                    "node_id": conn.source.node_id,
                    "port": conn.source.port
                },
                "target": {
                    "node_id": conn.target.node_id,
                    "port": conn.target.port
                }
            }
            if conn.condition:
                conn_config["condition"] = conn.condition
            connections_config.append(conn_config)
        
        return {
            "name": workflow_def.name,
            "description": workflow_def.description,
            "version": workflow_def.version,
            "nodes": nodes_config,
            "connections": connections_config,
            "start_node_id": workflow_def.start_node_id,
            "end_node_ids": workflow_def.end_node_ids,
            "variables": workflow_def.variables,
            "metadata": workflow_def.metadata
        }
