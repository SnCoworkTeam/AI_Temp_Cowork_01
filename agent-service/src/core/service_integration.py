"""
服务集成层
统一管理所有外部服务的调用
"""
import logging
from typing import Dict, Any, Optional, List

from ..services.mcp_client import mcp_client
from ..services.workflow_client import workflow_client
from ..services.knowledge_client import knowledge_client
from ..services.dag_client import dag_client
from ..services.memory_client import MemoryClient
from .task_classifier import ExecutionStrategy, RoutingDecision
from .conversation_agent import TaskType

logger = logging.getLogger(__name__)


class ServiceIntegration:
    """服务集成层"""
    
    def __init__(self):
        self.mcp = mcp_client
        self.workflow = workflow_client
        self.knowledge = knowledge_client
        self.dag = dag_client
        self.memory = MemoryClient()
    
    async def execute_routing_decision(
        self,
        routing_decision: RoutingDecision,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        根据路由决策执行任务
        
        Args:
            routing_decision: 路由决策结果
            task: 任务描述
            context: 上下文信息
            
        Returns:
            执行结果
        """
        strategy = routing_decision.strategy
        context = context or {}
        
        try:
            if strategy == ExecutionStrategy.TOOL_CALL:
                return await self._execute_tool_call(
                    routing_decision, task, context
                )
            elif strategy == ExecutionStrategy.WORKFLOW_EXECUTION:
                return await self._execute_workflow(
                    routing_decision, task, context
                )
            elif strategy == ExecutionStrategy.ORCHESTRATION:
                return await self._execute_orchestration(
                    routing_decision, task, context
                )
            elif strategy == ExecutionStrategy.SERVICE_DELEGATION:
                return await self._delegate_to_service(
                    routing_decision, task, context
                )
            else:
                # DIRECT_LLM 策略由调用者处理
                return {
                    "success": False,
                    "error": "Direct LLM execution should be handled by agent manager"
                }
        except Exception as e:
            logger.error(f"Service integration execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_tool_call(
        self,
        routing_decision: RoutingDecision,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行工具调用"""
        # 首先搜索合适的工具
        if routing_decision.required_tools:
            tool_id = routing_decision.required_tools[0]
        else:
            # 根据任务描述搜索工具
            tools = await self.mcp.search_tools(task)
            if not tools:
                return {
                    "success": False,
                    "error": "No suitable tool found"
                }
            tool_id = tools[0].get("id")
        
        # 提取工具参数（从上下文或任务描述中）
        parameters = routing_decision.execution_params.get("parameters", {})
        
        # 执行工具
        result = await self.mcp.execute_tool(tool_id, parameters, context)
        
        return {
            "success": result.get("success", False),
            "output": result.get("result") or result.get("output"),
            "tool_id": tool_id,
            "raw_result": result
        }
    
    async def _execute_workflow(
        self,
        routing_decision: RoutingDecision,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行工作流"""
        # 从上下文或任务描述中提取工作流ID
        workflow_id = context.get("workflow_id") or routing_decision.execution_params.get("workflow_id")
        
        if not workflow_id:
            return {
                "success": False,
                "error": "Workflow ID not specified"
            }
        
        # 准备输入数据
        input_data = context.get("input", {})
        
        # 执行工作流
        result = await self.workflow.execute_workflow(workflow_id, input_data, context)
        
        return {
            "success": result.get("success", False),
            "output": result.get("result") or result.get("output"),
            "workflow_id": workflow_id,
            "raw_result": result
        }
    
    async def _execute_orchestration(
        self,
        routing_decision: RoutingDecision,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行智能体编排"""
        # 调用agent-orchestrator
        import httpx
        import os
        
        orchestrator_url = os.getenv("AGENT_ORCHESTRATOR_URL", "http://agent-orchestrator:8011")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{orchestrator_url}/api/v1/orchestrate",
                    json={
                        "task": task,
                        "context": context
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Orchestration execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _delegate_to_service(
        self,
        routing_decision: RoutingDecision,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """委托给其他服务"""
        target_service = routing_decision.target_service
        
        if target_service == "knowledge-base":
            # 知识库搜索
            results = await self.knowledge.search(task, limit=10)
            return {
                "success": True,
                "output": results,
                "service": "knowledge-base"
            }
        elif target_service == "dag-orchestrator":
            # DAG任务分解和执行
            decomposition = await self.dag.decompose_task(task, context)
            if decomposition:
                return {
                    "success": True,
                    "output": decomposition,
                    "service": "dag-orchestrator"
                }
            else:
                return {
                    "success": False,
                    "error": "Task decomposition failed"
                }
        else:
            return {
                "success": False,
                "error": f"Unknown service: {target_service}"
            }
    
    async def close_all(self):
        """关闭所有客户端连接"""
        await self.mcp.close()
        await self.workflow.close()
        await self.knowledge.close()
        await self.dag.close()
        await self.memory.close()


# 全局服务集成实例
service_integration = ServiceIntegration()

