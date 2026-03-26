"""
统一智能体基类
所有智能体都应该继承这个基类，实现统一的接口
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, AsyncIterator
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    """智能体状态"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionPlan:
    """执行计划 - 统一格式"""
    plan_name: str
    description: str
    execution_mode: str  # single, sequence, dynamic
    commands: List[str] = field(default_factory=list)
    steps: List[Dict[str, Any]] = field(default_factory=list)  # 通用步骤列表
    expected_outcomes: List[str] = field(default_factory=list)
    rollback_commands: Optional[List[str]] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "plan_name": self.plan_name,
            "description": self.description,
            "execution_mode": self.execution_mode,
            "commands": self.commands,
            "steps": self.steps,
            "expected_outcomes": self.expected_outcomes,
            "rollback_commands": self.rollback_commands,
            "dependencies": self.dependencies,
            "metadata": self.metadata
        }


@dataclass
class ExecutionResult:
    """执行结果 - 统一格式"""
    plan_name: str
    success: bool
    commands_executed: int = 0
    commands_succeeded: int = 0
    steps_executed: int = 0
    steps_succeeded: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    summary: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "plan_name": self.plan_name,
            "success": self.success,
            "commands_executed": self.commands_executed,
            "commands_succeeded": self.commands_succeeded,
            "steps_executed": self.steps_executed,
            "steps_succeeded": self.steps_succeeded,
            "results": self.results,
            "error": self.error,
            "summary": self.summary,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }


@dataclass
class Reflection:
    """反思结果"""
    issues: List[str] = field(default_factory=list)
    root_causes: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    correction_plan: Optional[str] = None
    quality_score: float = 0.0
    is_satisfactory: bool = False


class BaseAgent(ABC):
    """
    统一智能体基类
    所有智能体都应该继承这个基类并实现以下方法
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: Optional[Dict[str, str]] = None
    ):
        """
        初始化智能体

        Args:
            agent_id: 智能体ID
            name: 智能体名称
            description: 智能体描述
            capabilities: 智能体能力字典
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities or {}
        self.created_at = datetime.utcnow()
        self.last_executed_at: Optional[datetime] = None
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.state = AgentState.IDLE

    @abstractmethod
    async def plan(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Union[ExecutionPlan, AsyncIterator[str]]:
        """
        规划任务

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            ExecutionPlan: 执行计划
            或 AsyncIterator[str]: 流式输出（如果支持）
        """
        pass

    @abstractmethod
    async def execute(
        self,
        plan: ExecutionPlan,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        执行计划

        Args:
            plan: 执行计划
            context: 上下文信息

        Returns:
            ExecutionResult: 执行结果
        """
        pass

    async def reflect(
        self,
        result: ExecutionResult,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Reflection]:
        """
        反思执行结果（可选实现）

        Args:
            result: 执行结果
            context: 上下文信息

        Returns:
            Reflection: 反思结果，如果不支持反思则返回None
        """
        # 默认不实现反思，子类可以覆盖
        return None

    async def plan_and_execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        auto_execute: bool = True,
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
        """
        规划并执行任务（便捷方法）

        Args:
            task: 任务描述
            context: 上下文信息
            auto_execute: 是否自动执行
            stream: 是否流式输出

        Returns:
            Dict: 包含plan和execution_result的字典
            或 AsyncIterator[str]: 流式输出
        """
        context = context or {}

        # 规划
        plan_result = await self.plan(task, context)

        if stream and isinstance(plan_result, AsyncIterator):
            # 流式输出模式
            async def stream_generator():
                full_plan_text = ""
                async for chunk in plan_result:
                    full_plan_text += chunk
                    yield chunk

                # 解析计划
                try:
                    plan = self._parse_plan_from_text(full_plan_text)
                except Exception as e:
                    logger.error(f"Failed to parse plan: {e}")
                    yield f"\n[错误: 无法解析执行计划]"
                    return

                if auto_execute:
                    yield "\n\n[开始执行计划...]"
                    result = await self.execute(plan, context)
                    yield f"\n[执行完成: {result.summary or ('成功' if result.success else '失败')}]"
            return stream_generator()
        else:
            # 非流式模式
            if isinstance(plan_result, AsyncIterator):
                # 如果是流式返回，需要收集所有内容
                full_text = ""
                async for chunk in plan_result:
                    full_text += chunk
                plan = self._parse_plan_from_text(full_text)
            else:
                plan = plan_result

            result = {
                "plan": plan.to_dict() if isinstance(plan, ExecutionPlan) else plan,
                "execution_result": None
            }

            if auto_execute:
                execution_result = await self.execute(plan, context)
                result["execution_result"] = execution_result.to_dict()

            return result

    def _parse_plan_from_text(self, text: str) -> ExecutionPlan:
        """
        从文本解析执行计划（默认实现，子类可以覆盖）

        Args:
            text: 计划文本

        Returns:
            ExecutionPlan: 执行计划
        """
        # 默认实现：尝试从JSON解析
        import json
        import re

        # 尝试提取JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                plan_dict = json.loads(json_match.group())
                return ExecutionPlan(
                    plan_name=plan_dict.get("plan_name", "未命名计划"),
                    description=plan_dict.get("description", ""),
                    execution_mode=plan_dict.get("execution_mode", "sequence"),
                    commands=plan_dict.get("commands", []),
                    expected_outcomes=plan_dict.get("expected_outcomes", []),
                    rollback_commands=plan_dict.get("rollback_commands")
                )
            except json.JSONDecodeError:
                pass

        # 如果解析失败，返回默认计划
        return ExecutionPlan(
            plan_name="解析失败",
            description=text[:200],
            execution_mode="sequence",
            commands=[]
        )

    def get_capabilities(self) -> Dict[str, str]:
        """获取智能体能力"""
        return self.capabilities

    def get_stats(self) -> Dict[str, Any]:
        """获取智能体统计信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / self.execution_count if self.execution_count > 0 else 0.0,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "state": self.state.value
        }

    def get_state(self) -> AgentState:
        """获取当前状态"""
        return self.state

    def set_state(self, state: AgentState):
        """设置状态"""
        self.state = state
        logger.debug(f"Agent {self.name} state changed to {state.value}")

