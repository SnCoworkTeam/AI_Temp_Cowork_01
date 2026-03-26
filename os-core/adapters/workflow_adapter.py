"""
工作流适配器
从工作流引擎适配工作流为统一资源
"""
from typing import List, Dict, Any, Optional
import logging

try:
    from ..resource_model import WorkflowResource, ResourceType
    from ..resource_registry import ResourceRegistry
except ImportError:
    from resource_model import WorkflowResource, ResourceType
    from resource_registry import ResourceRegistry

logger = logging.getLogger(__name__)


class WorkflowAdapter:
    """工作流适配器"""
    
    def __init__(self, registry: ResourceRegistry):
        """
        初始化工作流适配器
        
        Args:
            registry: 资源注册表
        """
        self.registry = registry
        logger.info("工作流适配器初始化完成")
    
    def adapt_from_workflow_definition(
        self,
        workflow_def: Dict[str, Any]
    ) -> WorkflowResource:
        """
        从工作流定义适配为工作流资源
        
        Args:
            workflow_def: 工作流定义字典
            
        Returns:
            WorkflowResource: 工作流资源对象
        """
        workflow_id = workflow_def.get("id", workflow_def.get("workflow_id", "unknown"))
        workflow_name = workflow_def.get("name", workflow_def.get("workflow_name", "未知工作流"))
        
        resource = WorkflowResource(
            id=f"workflow:{workflow_id}",
            name=workflow_name,
            description=workflow_def.get("description", ""),
            uri=f"workflow://{workflow_id}",
            workflow_definition=workflow_def,
            workflow_type=workflow_def.get("type", "static"),  # "static" | "dynamic"
            status=workflow_def.get("status", "active"),
            execution_count=workflow_def.get("execution_count", 0),
            success_rate=workflow_def.get("success_rate", 0.0),
            capabilities=["execute", "analyze", "optimize"],
            workflow_metadata={
                "source": "workflow_engine",
                "workflow_id": workflow_id,
                "steps": workflow_def.get("steps", []),
                "triggers": workflow_def.get("triggers", []),
                "created_by": workflow_def.get("created_by"),
                "created_at": workflow_def.get("created_at"),
                "original_definition": workflow_def
            }
        )
        
        return resource
    
    def adapt_from_workflow_execution(
        self,
        execution: Dict[str, Any]
    ) -> Optional[WorkflowResource]:
        """
        从工作流执行记录适配为工作流资源（用于动态工作流）
        
        Args:
            execution: 工作流执行记录字典
            
        Returns:
            WorkflowResource: 工作流资源对象，如果无法适配则返回None
        """
        workflow_id = execution.get("workflow_id", "unknown")
        
        # 从执行记录中提取工作流定义
        workflow_def = execution.get("workflow_definition", {})
        if not workflow_def:
            # 如果没有定义，尝试从执行步骤重建
            steps = execution.get("steps", [])
            if not steps:
                return None
            
            workflow_def = {
                "id": workflow_id,
                "name": execution.get("workflow_name", f"动态工作流_{workflow_id}"),
                "type": "dynamic",
                "steps": steps
            }
        
        resource = WorkflowResource(
            id=f"workflow:{workflow_id}",
            name=workflow_def.get("name", f"工作流_{workflow_id}"),
            description=workflow_def.get("description", "动态生成的工作流"),
            uri=f"workflow://{workflow_id}",
            workflow_definition=workflow_def,
            workflow_type="dynamic",
            status=execution.get("status", "completed"),
            execution_count=1,
            success_rate=1.0 if execution.get("status") == "success" else 0.0,
            capabilities=["execute", "analyze"],
            workflow_metadata={
                "source": "workflow_execution",
                "execution_id": execution.get("execution_id"),
                "started_at": execution.get("started_at"),
                "completed_at": execution.get("completed_at"),
                "duration": execution.get("duration"),
                "original_execution": execution
            }
        )
        
        return resource
    
    def register_workflows(
        self,
        workflows: List[Dict[str, Any]],
        source: str = "definition"
    ) -> int:
        """
        批量注册工作流
        
        Args:
            workflows: 工作流信息列表
            source: 数据源类型（"definition" | "execution"）
            
        Returns:
            int: 成功注册的数量
        """
        registered_count = 0
        
        for workflow in workflows:
            try:
                if source == "definition":
                    resource = self.adapt_from_workflow_definition(workflow)
                else:
                    resource = self.adapt_from_workflow_execution(workflow)
                    if resource is None:
                        continue
                
                if self.registry.register(resource):
                    registered_count += 1
                    
            except Exception as e:
                logger.error(f"注册工作流失败: {e}")
        
        logger.info(f"批量注册工作流完成: {registered_count}/{len(workflows)}")
        return registered_count

