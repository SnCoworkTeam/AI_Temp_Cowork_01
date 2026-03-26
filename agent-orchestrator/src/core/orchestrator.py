"""
智能体编排器核心逻辑
"""
import logging
from typing import Dict, List, Any, Optional
import httpx
import os
from datetime import datetime
import uuid

from ..models.plan_models import ExecutionPlan, PlanStep, PlanStatus, TaskDecomposition
from ..models.task_models import OrchestrationRequest, AgentSelection, CoordinationStrategy

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """智能体编排器"""
    
    def __init__(self):
        self.agent_service_url = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8010")
        self.registry_service_url = os.getenv("REGISTRY_SERVICE_URL", "http://registry-service:8000")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._plans: Dict[str, ExecutionPlan] = {}  # 内存存储（生产环境应使用数据库）
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
    
    async def orchestrate_agents(
        self,
        request: OrchestrationRequest
    ) -> Dict[str, Any]:
        """
        编排多个智能体协同完成任务
        
        Args:
            request: 编排请求
            
        Returns:
            编排结果
        """
        try:
            # 1. 任务分解和规划
            plan = await self._create_plan(request)
            
            # 2. 智能体选择
            agent_selections = await self._select_agents(plan)
            
            # 3. 执行计划
            execution_id = str(uuid.uuid4())
            results = await self._execute_plan(plan, agent_selections, request.strategy)
            
            return {
                "execution_id": execution_id,
                "plan_id": plan.plan_id,
                "status": "completed" if all(r.get("success") for r in results.values()) else "partial",
                "results": results,
                "agent_selections": [s.dict() for s in agent_selections],
                "metadata": {
                    "strategy": request.strategy.value,
                    "total_steps": len(plan.steps),
                    "completed_steps": sum(1 for r in results.values() if r.get("success")),
                }
            }
        except Exception as e:
            logger.error(f"Orchestration failed: {str(e)}", exc_info=True)
            raise
    
    async def _create_plan(self, request: OrchestrationRequest) -> ExecutionPlan:
        """创建执行计划"""
        from .planning import PlanningEngine
        
        planner = PlanningEngine()
        decomposition = await planner.decompose_task(request.task, request.context)
        
        plan_id = str(uuid.uuid4())
        steps = []
        
        for i, subtask in enumerate(decomposition.subtasks):
            step = PlanStep(
                step_id=f"step_{i+1}",
                name=subtask.get("name", f"步骤 {i+1}"),
                description=subtask.get("description", ""),
                task=subtask.get("task", ""),
                agent_capabilities=subtask.get("capabilities", []),
                dependencies=decomposition.dependencies.get(f"step_{i+1}", []),
                parameters=subtask.get("parameters", {}),
            )
            steps.append(step)
        
        plan = ExecutionPlan(
            plan_id=plan_id,
            name=request.task[:50] + "..." if len(request.task) > 50 else request.task,
            description=f"任务编排计划: {request.task}",
            task=request.task,
            context=request.context,
            steps=steps,
            status=PlanStatus.READY,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self._plans[plan_id] = plan
        return plan
    
    async def _select_agents(self, plan: ExecutionPlan) -> List[AgentSelection]:
        """选择智能体"""
        agent_selections = []
        
        try:
            # 从 Agent Service 获取智能体列表
            response = await self.http_client.get(f"{self.agent_service_url}/api/v1/agents")
            if response.status_code == 200:
                agents = response.json()
                
                for step in plan.steps:
                    # 根据能力匹配智能体
                    best_agent = None
                    best_score = 0.0
                    
                    for agent in agents:
                        if not isinstance(agent, dict):
                            continue
                        
                        agent_capabilities = agent.get("capabilities", [])
                        if not agent_capabilities:
                            continue
                        
                        # 计算匹配度
                        matching_capabilities = set(step.agent_capabilities) & set(agent_capabilities)
                        score = len(matching_capabilities) / max(len(step.agent_capabilities), 1)
                        
                        if score > best_score:
                            best_score = score
                            best_agent = agent
                    
                    if best_agent:
                        selection = AgentSelection(
                            agent_id=best_agent.get("id", ""),
                            agent_name=best_agent.get("name", ""),
                            capabilities=best_agent.get("capabilities", []),
                            confidence=best_score,
                            reason=f"匹配能力: {', '.join(step.agent_capabilities)}"
                        )
                        agent_selections.append(selection)
                        step.agent_id = best_agent.get("id")
                    else:
                        logger.warning(f"No suitable agent found for step: {step.step_id}")
        except Exception as e:
            logger.error(f"Agent selection failed: {str(e)}", exc_info=True)
        
        return agent_selections
    
    async def _execute_plan(
        self,
        plan: ExecutionPlan,
        agent_selections: List[AgentSelection],
        strategy: CoordinationStrategy
    ) -> Dict[str, Any]:
        """执行计划"""
        results = {}
        
        if strategy == CoordinationStrategy.SEQUENTIAL:
            # 顺序执行
            for step in plan.steps:
                agent_id = step.agent_id
                if not agent_id:
                    results[step.step_id] = {"success": False, "error": "No agent assigned"}
                    continue
                
                try:
                    response = await self.http_client.post(
                        f"{self.agent_service_url}/api/v1/agents/{agent_id}/execute",
                        json={
                            "task": step.task,
                            "context": plan.context,
                            "parameters": step.parameters
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        results[step.step_id] = result
                        step.status = PlanStatus.COMPLETED if result.get("success") else PlanStatus.FAILED
                        step.result = result
                    else:
                        results[step.step_id] = {"success": False, "error": f"HTTP {response.status_code}"}
                        step.status = PlanStatus.FAILED
                except Exception as e:
                    logger.error(f"Step execution failed: {str(e)}", exc_info=True)
                    results[step.step_id] = {"success": False, "error": str(e)}
                    step.status = PlanStatus.FAILED
        else:
            # 其他策略（简化实现，实际应该更复杂）
            # 这里先实现顺序执行，后续可以扩展
            return await self._execute_plan(plan, agent_selections, CoordinationStrategy.SEQUENTIAL)
        
        plan.status = PlanStatus.COMPLETED if all(r.get("success") for r in results.values()) else PlanStatus.FAILED
        plan.updated_at = datetime.utcnow()
        
        # 整合结果
        from .result_aggregator import result_aggregator
        aggregated_result = await result_aggregator.aggregate_results(
            results,
            plan.context
        )
        
        return aggregated_result
    
    async def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """获取计划"""
        return self._plans.get(plan_id)
    
    async def list_plans(self, limit: int = 100, offset: int = 0) -> List[ExecutionPlan]:
        """列出计划"""
        plans = list(self._plans.values())
        plans.sort(key=lambda x: x.created_at, reverse=True)
        return plans[offset:offset + limit]


# 全局编排器实例
agent_orchestrator = AgentOrchestrator()

