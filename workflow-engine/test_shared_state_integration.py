"""
测试workflow-engine使用共享State定义
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine"))

from shared_libs.schemas.workflow_states import (
    create_workflow_state,
    validate_workflow_state,
    AgentWorkflowState
)

from src.core.dynamic_workflow_engine import DynamicWorkflowEngine


def test_workflow_engine_with_shared_state():
    """测试工作流引擎使用共享State"""
    print("=" * 60)
    print("测试workflow-engine使用共享State")
    print("=" * 60)
    
    # 测试1: 创建引擎实例
    print("\n1. 创建DynamicWorkflowEngine实例...")
    try:
        engine = DynamicWorkflowEngine()
        print("   ✓ 引擎实例创建成功")
    except Exception as e:
        print(f"   ✗ 引擎实例创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试2: 使用共享State创建状态
    print("\n2. 使用共享State创建状态...")
    try:
        state = create_workflow_state(
            workflow_id="test_workflow",
            input_data={"test": "value"}
        )
        assert state.workflow_id == "test_workflow"
        assert state.input_data["test"] == "value"
        print("   ✓ 共享State创建成功")
        print(f"   - workflow_id: {state.workflow_id}")
        print(f"   - thread_id: {state.metadata.get('thread_id')}")
    except Exception as e:
        print(f"   ✗ 共享State创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试3: 验证状态
    print("\n3. 验证状态...")
    try:
        assert engine._validate_initial_state(state.model_dump()) == True
        print("   ✓ 状态验证通过")
    except Exception as e:
        print(f"   ✗ 状态验证失败: {e}")
        return False
    
    # 测试4: 创建Agent工作流状态
    print("\n4. 创建Agent工作流状态...")
    try:
        agent_state = engine._create_agent_workflow_state(
            workflow_id="agent_workflow",
            agent_id="test_agent",
            input_data={"user_input": "hello"}
        )
        assert agent_state.agent_id == "test_agent"
        assert agent_state.workflow_id == "agent_workflow"
        print("   ✓ Agent工作流状态创建成功")
        print(f"   - agent_id: {agent_state.agent_id}")
    except Exception as e:
        print(f"   ✗ Agent工作流状态创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试5: 状态转换为字典（LangGraph兼容）
    print("\n5. 测试状态转换为字典...")
    try:
        state_dict = state.model_dump()
        assert isinstance(state_dict, dict)
        assert "input_data" in state_dict
        assert "metadata" in state_dict
        print("   ✓ 状态转换成功")
        print(f"   - 字典键数量: {len(state_dict)}")
    except Exception as e:
        print(f"   ✗ 状态转换失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 workflow-engine共享State集成测试通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_workflow_engine_with_shared_state()
    sys.exit(0 if success else 1)

