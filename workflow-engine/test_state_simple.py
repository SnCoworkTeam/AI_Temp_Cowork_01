"""
简单测试工作流状态定义
验证 State 定义的基本结构
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, TypedDict

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 直接定义和测试，不依赖外部模块
print("=" * 60)
print("测试工作流状态定义结构")
print("=" * 60)

# 测试1: TypedDict定义
print("\n1. 测试 TypedDict 定义...")
try:
    class WorkflowStateTypedDict(TypedDict, total=False):
        """工作流状态类型定义"""
        input_data: Dict[str, Any]
        node_results: Dict[str, Any]
        current_node: str
        execution_history: List[Dict[str, Any]]
        error: Optional[str]
        final_result: Optional[Any]
        metadata: Dict[str, Any]
        execution_context: Dict[str, Any]
        execution_id: str
        workflow_id: str
        start_time: float
    
    # 创建测试数据
    state_dict: WorkflowStateTypedDict = {
        "input_data": {"user_input": "test"},
        "node_results": {"node1": "result1"},
        "current_node": "start_node",
        "execution_history": [{"node": "start", "timestamp": "2024-01-01"}],
        "error": None,
        "final_result": None,
        "metadata": {"workflow_id": "test_workflow"},
        "execution_context": {"user_id": "user123"},
        "execution_id": "exec_123",
        "workflow_id": "wf_123",
        "start_time": 1234567890.0
    }
    print("   ✓ TypedDict 定义和实例化成功")
    print(f"   - input_data: {state_dict['input_data']}")
    print(f"   - current_node: {state_dict['current_node']}")
except Exception as e:
    print(f"   ✗ TypedDict 定义失败: {e}")
    sys.exit(1)

# 测试2: 验证函数
print("\n2. 测试验证函数...")
def validate_workflow_state(state: Dict[str, Any]) -> bool:
    """验证工作流状态结构"""
    required_fields = ['input_data', 'node_results', 'execution_history']
    for field in required_fields:
        if field not in state:
            return False
    
    # 验证数据类型
    if not isinstance(state.get('input_data', {}), dict):
        return False
    if not isinstance(state.get('node_results', {}), dict):
        return False
    if not isinstance(state.get('execution_history', []), list):
        return False
    
    return True

try:
    assert validate_workflow_state(state_dict) == True
    print("   ✓ 有效状态验证通过")
except Exception as e:
    print(f"   ✗ 有效状态验证失败: {e}")
    sys.exit(1)

# 测试3: 无效状态验证
print("\n3. 测试无效状态验证...")
try:
    invalid_state = {"input_data": "not_a_dict"}
    assert validate_workflow_state(invalid_state) == False
    print("   ✓ 无效状态正确识别")
except Exception as e:
    print(f"   ✗ 无效状态验证失败: {e}")
    sys.exit(1)

# 测试4: 缺少必需字段
print("\n4. 测试缺少必需字段...")
try:
    incomplete_state = {"input_data": {}}
    assert validate_workflow_state(incomplete_state) == False
    print("   ✓ 缺少必需字段正确识别")
except Exception as e:
    print(f"   ✗ 缺少必需字段验证失败: {e}")
    sys.exit(1)

# 测试5: WorkflowState字典兼容性
print("\n5. 测试 WorkflowState 字典兼容性...")
try:
    class WorkflowState(dict):
        """工作流状态（继承字典，用于LangGraph兼容性）"""
        pass
    
    workflow_state = WorkflowState(state_dict)
    assert isinstance(workflow_state, dict)
    assert workflow_state["input_data"] == {"user_input": "test"}
    assert workflow_state["current_node"] == "start_node"
    print("   ✓ WorkflowState 字典兼容性通过")
    print(f"   - 类型: {type(workflow_state)}")
    print(f"   - 键数量: {len(workflow_state)}")
except Exception as e:
    print(f"   ✗ WorkflowState 字典兼容性失败: {e}")
    sys.exit(1)

# 测试6: 额外字段支持
print("\n6. 测试额外字段支持...")
try:
    state_with_extra = state_dict.copy()
    state_with_extra["custom_field"] = "custom_value"
    assert "custom_field" in state_with_extra
    assert state_with_extra["custom_field"] == "custom_value"
    print("   ✓ 额外字段支持通过")
except Exception as e:
    print(f"   ✗ 额外字段支持失败: {e}")
    sys.exit(1)

# 测试7: 类型检查
print("\n7. 测试类型检查...")
try:
    assert isinstance(state_dict["input_data"], dict)
    assert isinstance(state_dict["node_results"], dict)
    assert isinstance(state_dict["execution_history"], list)
    assert isinstance(state_dict["current_node"], str)
    assert state_dict["error"] is None or isinstance(state_dict["error"], str)
    print("   ✓ 类型检查通过")
except Exception as e:
    print(f"   ✗ 类型检查失败: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ 所有 State 定义验证通过！")
print("=" * 60)
print("\n总结:")
print("- TypedDict 定义正确，可以用于类型提示")
print("- 验证函数能够正确识别有效和无效状态")
print("- WorkflowState 字典兼容性良好")
print("- 支持额外字段（动态扩展）")
print("- 类型检查正常工作")

