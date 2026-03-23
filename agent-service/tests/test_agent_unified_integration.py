"""
智能体统一接口集成测试
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
from src.core.agents.analysis_agent import AnalysisAgent
from src.core.agents.server_operation_agent import ServerOperationAgent
from src.core.agents.agent_adapter_unified import AgentAdapter
from src.core.agents.base_agent import IntelligentAgent
from src.core.agent_manager import AgentManager


class MockLegacyAgent(IntelligentAgent):
    """模拟旧智能体"""

    def __init__(self):
        super().__init__(
            agent_id="mock_legacy",
            name="Mock旧智能体",
            description="用于测试的旧智能体",
            capabilities={"test": "测试"}
        )
        self.llm = Mock()

    async def analyze_task(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"needs_execution": True, "plan": "执行计划"}

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "result": "执行成功"}


@pytest.mark.asyncio
async def test_analysis_agent_unified_interface():
    """测试AnalysisAgent统一接口"""
    agent = AnalysisAgent()

    # 测试plan方法
    plan = await agent.plan("分析销售数据")
    assert isinstance(plan, ExecutionPlan)
    assert "数据分析" in plan.plan_name

    # 测试execute方法（需要数据）
    context = {
        "data": [{"sales": 100, "month": "2024-01"}]
    }
    result = await agent.execute(plan, context)
    assert isinstance(result, ExecutionResult)

    # 测试plan_and_execute
    result_dict = await agent.plan_and_execute("分析数据", context, auto_execute=False)
    assert "plan" in result_dict


@pytest.mark.asyncio
async def test_server_operation_agent_unified_interface():
    """测试ServerOperationAgent统一接口"""
    # 注意：这个测试需要SSH配置，在实际环境中运行
    # 这里只测试接口是否正确
    assert issubclass(ServerOperationAgent, BaseAgent)
    assert hasattr(ServerOperationAgent, 'plan')
    assert hasattr(ServerOperationAgent, 'execute')
    assert hasattr(ServerOperationAgent, 'plan_and_execute')


@pytest.mark.asyncio
async def test_agent_adapter():
    """测试智能体适配器"""
    legacy_agent = MockLegacyAgent()
    adapter = AgentAdapter(legacy_agent)

    # 测试plan
    plan = await adapter.plan("测试任务")
    assert isinstance(plan, ExecutionPlan)

    # 测试execute
    result = await adapter.execute(plan, {"test": "data"})
    assert isinstance(result, ExecutionResult)
    assert result.success is True

    # 测试plan_and_execute
    result_dict = await adapter.plan_and_execute("测试任务", {"test": "data"})
    assert "plan" in result_dict
    assert "execution_result" in result_dict


@pytest.mark.asyncio
async def test_agent_manager_unified_support():
    """测试AgentManager对统一接口的支持"""
    manager = AgentManager()

    # 测试是否能识别统一接口
    # 这里需要实际的智能体实例，所以只测试逻辑
    assert hasattr(manager, 'execute_agent')


def test_execution_plan_compatibility():
    """测试ExecutionPlan兼容性"""
    # 测试SSH智能体的ExecutionPlan格式
    plan1 = ExecutionPlan(
        plan_name="SSH任务",
        description="执行SSH命令",
        execution_mode="sequence",
        commands=["ls -la", "pwd"]
    )
    assert len(plan1.commands) == 2

    # 测试通用智能体的ExecutionPlan格式
    plan2 = ExecutionPlan(
        plan_name="分析任务",
        description="数据分析",
        execution_mode="sequence",
        steps=[{"step_type": "analysis"}]
    )
    assert len(plan2.steps) == 1

    # 两种格式都应该可以工作
    assert plan1.to_dict()["plan_name"] == "SSH任务"
    assert plan2.to_dict()["plan_name"] == "分析任务"


def test_execution_result_compatibility():
    """测试ExecutionResult兼容性"""
    # SSH智能体格式
    result1 = ExecutionResult(
        plan_name="SSH任务",
        success=True,
        commands_executed=2,
        commands_succeeded=2,
        results=[{"command": "ls", "success": True}]
    )

    # 通用智能体格式
    result2 = ExecutionResult(
        plan_name="分析任务",
        success=True,
        steps_executed=1,
        steps_succeeded=1,
        results=[{"analysis": "完成"}]
    )

    assert result1.success is True
    assert result2.success is True
    assert result1.to_dict()["success"] is True
    assert result2.to_dict()["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

