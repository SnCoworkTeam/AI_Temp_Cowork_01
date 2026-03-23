#!/usr/bin/env python3
"""
测试共享工作流状态定义
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared_libs.schemas.workflow_states import (
    WorkflowStateTypedDict,
    WorkflowStateModel,
    WorkflowState,
    validate_workflow_state,
    create_workflow_state,
    AgentWorkflowState,
    MCPWorkflowState
)


def test_shared_state_integration():
    """测试共享状态集成"""
    print("=" * 60)
    print("测试共享工作流状态定义")
    print("=" * 60)
    
    # 测试1: 基本状态创建
    print("\n1. 测试基本状态创建...")
    try:
        state = create_workflow_state("test_workflow", {"input": "test"})
        assert state.workflow_id == "test_workflow"
        assert state.input_data["input"] == "test"
        assert state.metadata["thread_id"] is not None
        assert state.metadata["workflow_id"] == "test_workflow"
        print("   ✓ 基本状态创建测试通过")
        print(f"   - workflow_id: {state.workflow_id}")
        print(f"   - thread_id: {state.metadata.get('thread_id')}")
    except Exception as e:
        print(f"   ✗ 基本状态创建测试失败: {e}")
        return False
    
    # 测试2: 状态验证函数
    print("\n2. 测试状态验证...")
    try:
        assert validate_workflow_state(state.model_dump()) == True
        assert validate_workflow_state({"invalid": "state"}) == False
        print("   ✓ 状态验证测试通过")
    except Exception as e:
        print(f"   ✗ 状态验证测试失败: {e}")
        return False
    
    # 测试3: 扩展状态（Agent）
    print("\n3. 测试扩展状态（Agent）...")
    try:
        agent_state = AgentWorkflowState.create_agent_state(
            workflow_id="agent_workflow",
            agent_id="test_agent",
            input_data={"user_input": "hello"}
        )
        assert agent_state.agent_id == "test_agent"
        assert agent_state.workflow_id == "agent_workflow"
        assert isinstance(agent_state.conversation_history, list)
        assert isinstance(agent_state.user_context, dict)
        print("   ✓ 扩展状态（Agent）测试通过")
        print(f"   - agent_id: {agent_state.agent_id}")
    except Exception as e:
        print(f"   ✗ 扩展状态（Agent）测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试4: 扩展状态（MCP）
    print("\n4. 测试扩展状态（MCP）...")
    try:
        mcp_state = MCPWorkflowState(
            workflow_id="mcp_workflow",
            input_data={},
            tool_executions=[],
            available_tools=[]
        )
        mcp_state.record_tool_execution(
            tool_name="test_tool",
            parameters={"param1": "value1"},
            result="success",
            success=True
        )
        assert len(mcp_state.tool_executions) == 1
        assert mcp_state.tool_executions[0]["tool_name"] == "test_tool"
        print("   ✓ 扩展状态（MCP）测试通过")
        print(f"   - 工具执行记录数: {len(mcp_state.tool_executions)}")
    except Exception as e:
        print(f"   ✗ 扩展状态（MCP）测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试5: 状态序列化
    print("\n5. 测试状态序列化...")
    try:
        state_dict = state.model_dump()
        assert "input_data" in state_dict
        assert "metadata" in state_dict
        assert "node_results" in state_dict
        assert "execution_history" in state_dict
        print("   ✓ 状态序列化测试通过")
        print(f"   - 序列化键数量: {len(state_dict)}")
    except Exception as e:
        print(f"   ✗ 状态序列化测试失败: {e}")
        return False
    
    # 测试6: 状态反序列化
    print("\n6. 测试状态反序列化...")
    try:
        state_dict = state.model_dump()
        restored_state = WorkflowStateModel(**state_dict)
        assert restored_state.workflow_id == state.workflow_id
        assert restored_state.input_data == state.input_data
        print("   ✓ 状态反序列化测试通过")
    except Exception as e:
        print(f"   ✗ 状态反序列化测试失败: {e}")
        return False
    
    # 测试7: 额外字段支持
    print("\n7. 测试额外字段支持...")
    try:
        state_with_extra = create_workflow_state(
            "test_workflow",
            {"input": "test"},
            custom_field="custom_value"
        )
        assert hasattr(state_with_extra, "custom_field")
        assert state_with_extra.custom_field == "custom_value"
        print("   ✓ 额外字段支持测试通过")
    except Exception as e:
        print(f"   ✗ 额外字段支持测试失败: {e}")
        return False
    
    # 测试8: TypedDict兼容性
    print("\n8. 测试TypedDict兼容性...")
    try:
        typed_state: WorkflowStateTypedDict = {
            "input_data": {"test": "value"},
            "node_results": {},
            "execution_history": [],
            "workflow_id": "test"
        }
        # 验证可以转换为模型
        model_state = WorkflowStateModel(**typed_state)
        assert model_state.workflow_id == "test"
        print("   ✓ TypedDict兼容性测试通过")
    except Exception as e:
        print(f"   ✗ TypedDict兼容性测试失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 所有共享状态测试通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_shared_state_integration()
    sys.exit(0 if success else 1)

