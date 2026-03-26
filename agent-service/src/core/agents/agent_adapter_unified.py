"""
智能体适配器
将旧的IntelligentAgent接口适配到新的BaseAgent接口
"""
import logging
from typing import Dict, Any, Optional, Union, AsyncIterator
from datetime import datetime

from .unified_base_agent import BaseAgent, ExecutionPlan, ExecutionResult, AgentState
from .base_agent import IntelligentAgent

logger = logging.getLogger(__name__)


class AgentAdapter(BaseAgent):
    """
    智能体适配器
    将旧的IntelligentAgent适配到新的BaseAgent接口
    """

    def __init__(self, legacy_agent: IntelligentAgent):
        """
        初始化适配器

        Args:
            legacy_agent: 旧的智能体实例
        """
        super().__init__(
            agent_id=legacy_agent.agent_id,
            name=legacy_agent.name,
            description=legacy_agent.description,
            capabilities=legacy_agent.capabilities
        )
        self.legacy_agent = legacy_agent
        # 复制统计信息
        self.execution_count = legacy_agent.execution_count
        self.success_count = legacy_agent.success_count
        self.failure_count = legacy_agent.failure_count
        self.last_executed_at = legacy_agent.last_executed_at

    async def plan(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        规划任务（适配旧接口）

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            ExecutionPlan: 执行计划
        """
        self.set_state(AgentState.PLANNING)
        context = context or {}

        try:
            # 调用旧的analyze_task方法
            analysis_result = await self.legacy_agent.analyze_task(task, context)

            # 转换为ExecutionPlan
            plan = ExecutionPlan(
                plan_name=f"任务: {task[:50]}",
                description=task,
                execution_mode="sequence",
                steps=[{
                    "step_type": "legacy_agent",
                    "analysis_result": analysis_result
                }],
                expected_outcomes=["执行完成"],
                metadata={"legacy_analysis": analysis_result}
            )

            self.set_state(AgentState.IDLE)
            return plan
        except Exception as e:
            logger.error(f"规划任务失败: {e}", exc_info=True)
            self.set_state(AgentState.FAILED)
            raise

    async def execute(
        self,
        plan: ExecutionPlan,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        执行计划（适配旧接口）

        Args:
            plan: 执行计划
            context: 上下文信息

        Returns:
            ExecutionResult: 执行结果
        """
        self.set_state(AgentState.EXECUTING)
        context = context or {}

        try:
            # 从plan中提取信息
            legacy_analysis = plan.metadata.get("legacy_analysis", {})

            # 构建input_data（兼容旧接口）
            input_data = {
                "task": plan.description,
                "analysis_plan": legacy_analysis,
                **context
            }

            # 调用旧的execute方法
            old_result = await self.legacy_agent.execute(input_data, context)

            # 转换为ExecutionResult
            success = old_result.get("execution_success", True) or old_result.get("success", True)
            result = ExecutionResult(
                plan_name=plan.plan_name,
                success=success,
                steps_executed=1,
                steps_succeeded=1 if success else 0,
                results=[old_result],
                summary=old_result.get("summary", "执行完成"),
                metadata={"legacy_result": old_result}
            )

            self.set_state(AgentState.COMPLETED if result.success else AgentState.FAILED)
            self.execution_count += 1
            if result.success:
                self.success_count += 1
            else:
                self.failure_count += 1
            self.last_executed_at = datetime.utcnow()

            return result
        except Exception as e:
            logger.error(f"执行计划失败: {e}", exc_info=True)
            self.set_state(AgentState.FAILED)
            self.execution_count += 1
            self.failure_count += 1
            self.last_executed_at = datetime.utcnow()

            return ExecutionResult(
                plan_name=plan.plan_name,
                success=False,
                steps_executed=0,
                steps_succeeded=0,
                results=[],
                error=str(e),
                summary=f"执行失败: {e}"
            )

    def get_legacy_agent(self) -> IntelligentAgent:
        """获取原始智能体实例"""
        return self.legacy_agent

