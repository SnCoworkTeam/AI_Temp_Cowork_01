"""
统一智能体接口测试
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.core.agents.unified_base_agent import (
    BaseAgent,
    ExecutionPlan,
    ExecutionResult,
    AgentState
)
from src.core.agents.server_operation_agent import ServerOperationAgent
from src.core.agents.tool_registry import ToolRegistry, Tool
from src.core.agents.react_engine import ReActEngine


class MockAgent(BaseAgent):
    """测试用的Mock智能体"""

    def __init__(self):
        super().__init__(
            agent_id="mock_agent",
            name="Mock智能体",
            description="用于测试的Mock智能体",
            capabilities={"test": "测试能力"}
        )
        self.plans = []
        self.results = []

    async def plan(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """规划任务"""
        plan = ExecutionPlan(
            plan_name=f"计划: {task}",
            description=f"执行任务: {task}",
            execution_mode="sequence",
            commands=[f"echo {task}"]
        )
        self.plans.append(plan)
        return plan

    async def execute(
        self,
        plan: ExecutionPlan,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """执行计划"""
        result = ExecutionResult(
            plan_name=plan.plan_name,
            success=True,
            commands_executed=len(plan.commands),
            commands_succeeded=len(plan.commands),
            results=[{"command": cmd, "success": True} for cmd in plan.commands],
            summary="执行成功"
        )
        self.results.append(result)
        return result


class MockTool(Tool):
    """测试用的Mock工具"""

    def __init__(self):
        super().__init__(
            name="mock_tool",
            description="用于测试的Mock工具",
            parameters={"input": "输入参数"}
        )
        self.call_count = 0

    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        self.call_count += 1
        return {"result": f"执行了工具，参数: {kwargs}"}


@pytest.mark.asyncio
async def test_base_agent_interface():
    """测试BaseAgent接口"""
    agent = MockAgent()

    # 测试plan方法
    plan = await agent.plan("测试任务")
    assert isinstance(plan, ExecutionPlan)
    assert plan.plan_name == "计划: 测试任务"

    # 测试execute方法
    result = await agent.execute(plan)
    assert isinstance(result, ExecutionResult)
    assert result.success is True

    # 测试plan_and_execute方法
    result_dict = await agent.plan_and_execute("测试任务2")
    assert "plan" in result_dict
    assert "execution_result" in result_dict

    # 测试状态管理
    assert agent.get_state() == AgentState.IDLE
    agent.set_state(AgentState.PLANNING)
    assert agent.get_state() == AgentState.PLANNING

    # 测试统计信息
    stats = agent.get_stats()
    assert stats["execution_count"] > 0
    assert stats["success_count"] > 0


@pytest.mark.asyncio
async def test_tool_registry():
    """测试工具注册表"""
    registry = ToolRegistry()

    # 注册工具
    tool = MockTool()
    registry.register_tool(tool)
    assert registry.has_tool("mock_tool")

    # 获取工具
    retrieved_tool = registry.get_tool("mock_tool")
    assert retrieved_tool == tool

    # 列出工具
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0] == tool

    # 执行工具
    result = await tool.execute(input="test")
    assert "result" in result
    assert tool.call_count == 1

    # 注销工具
    registry.unregister_tool("mock_tool")
    assert not registry.has_tool("mock_tool")


@pytest.mark.asyncio
async def test_react_engine():
    """测试ReAct引擎"""
    # 创建Mock LLM
    mock_llm = AsyncMock()
    mock_llm.chat = AsyncMock(return_value='{"should_act": false, "reasoning": "任务已完成"}')

    # 创建工具注册表
    registry = ToolRegistry()
    tool = MockTool()
    registry.register_tool(tool)

    # 创建ReAct引擎
    engine = ReActEngine(mock_llm, registry)

    # 执行ReAct循环
    result = await engine.react_loop("测试任务", max_iterations=3)

    assert "success" in result
    assert "thoughts" in result
    assert "actions" in result
    assert "observations" in result


@pytest.mark.asyncio
async def test_server_operation_agent_inheritance():
    """测试ServerOperationAgent继承BaseAgent"""
    # 注意：这个测试需要SSH配置，在实际环境中运行
    # 这里只测试接口是否正确
    from src.core.agents.server_operation_agent import ServerOperationAgent

    # 检查是否继承BaseAgent
    assert issubclass(ServerOperationAgent, BaseAgent)

    # 检查是否有plan和execute方法
    assert hasattr(ServerOperationAgent, 'plan')
    assert hasattr(ServerOperationAgent, 'execute')

    # 检查是否有plan_and_execute方法
    assert hasattr(ServerOperationAgent, 'plan_and_execute')


def test_execution_plan():
    """测试ExecutionPlan数据类"""
    plan = ExecutionPlan(
        plan_name="测试计划",
        description="测试描述",
        execution_mode="sequence",
        commands=["cmd1", "cmd2"],
        expected_outcomes=["outcome1"]
    )

    assert plan.plan_name == "测试计划"
    assert len(plan.commands) == 2

    # 测试to_dict
    plan_dict = plan.to_dict()
    assert "plan_name" in plan_dict
    assert "commands" in plan_dict


def test_execution_result():
    """测试ExecutionResult数据类"""
    result = ExecutionResult(
        plan_name="测试计划",
        success=True,
        commands_executed=2,
        commands_succeeded=2,
        results=[{"command": "cmd1", "success": True}],
        summary="执行成功"
    )

    assert result.success is True
    assert result.commands_executed == 2

    # 测试to_dict
    result_dict = result.to_dict()
    assert "success" in result_dict
    assert "results" in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

