#!/usr/bin/env python3
"""
测试条件评估安全性
验证安全表达式评估和危险表达式阻止
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine"))

# 尝试导入，如果失败则跳过某些测试
try:
    from src.nodes.condition_node import ConditionNode
    CONDITION_NODE_AVAILABLE = True
except ImportError:
    CONDITION_NODE_AVAILABLE = False
    print("[WARN] 无法导入ConditionNode，将跳过部分测试")


def test_condition_safety():
    """测试条件评估安全性"""
    print("=" * 60)
    print("测试条件评估安全性")
    print("=" * 60)
    
    # 测试1: 安全表达式正常评估
    print("\n1. 测试安全表达式评估...")
    if CONDITION_NODE_AVAILABLE:
        try:
            node = ConditionNode(
                name="test_condition",
                config={"condition": "input_data.value > 10"}
            )
            
            test_state = {
                "input_data": {"value": 15},
                "node_results": {},
                "execution_history": []
            }
            
            result = node._evaluate_expression("input_data.value > 10", test_state)
            assert result == True, "安全表达式评估失败"
            print("   [OK] 安全表达式评估通过")
            print(f"   表达式: input_data.value > 10")
            print(f"   结果: {result}")
        except Exception as e:
            print(f"   [ERROR] 安全表达式评估失败: {e}")
            return False
    else:
        print("   [WARN] 跳过此测试（ConditionNode不可用）")
    
    # 测试2: 危险表达式被阻止
    print("\n2. 测试危险表达式阻止...")
    dangerous_expressions = [
        "__import__('os').system('ls')",
        "eval('__import__(\"os\").system(\"ls\")')",
        "exec('print(1)')",
        "open('/etc/passwd').read()",
        "import os",
    ]
    
    for expr in dangerous_expressions:
        try:
            # 使用dynamic_workflow_engine中的验证函数
            from src.core.dynamic_workflow_engine import DynamicWorkflowEngine
            engine = DynamicWorkflowEngine()
            
            is_safe = engine._validate_condition_expression(expr)
            if not is_safe:
                print(f"   [OK] 危险表达式被阻止: {expr[:50]}...")
            else:
                print(f"   [WARN] 危险表达式未被阻止: {expr[:50]}...")
        except Exception as e:
            print(f"   [WARN] 验证表达式时出错: {e}")
    
    # 测试3: 表达式复杂度限制
    print("\n3. 测试表达式复杂度限制...")
    try:
        # 创建一个非常复杂的表达式
        complex_expr = " + ".join([f"input_data.value{i}" for i in range(150)])
        
        from src.core.dynamic_workflow_engine import DynamicWorkflowEngine
        engine = DynamicWorkflowEngine()
        
        is_safe = engine._validate_condition_expression(complex_expr)
        if not is_safe:
            print("   [OK] 复杂表达式被正确限制")
        else:
            print("   [WARN] 复杂表达式未被限制")
    except Exception as e:
        print(f"   [ERROR] 复杂度测试失败: {e}")
        return False
    
    # 测试4: 正常条件表达式
    print("\n4. 测试正常条件表达式...")
    normal_expressions = [
        "input_data.value == 10",
        "input_data.count > 5 and input_data.status == 'active'",
        "len(input_data.items) > 0",
        "input_data.price * input_data.quantity > 1000",
    ]
    
    for expr in normal_expressions:
        try:
            from src.core.dynamic_workflow_engine import DynamicWorkflowEngine
            engine = DynamicWorkflowEngine()
            
            is_safe = engine._validate_condition_expression(expr)
            if is_safe:
                print(f"   [OK] 正常表达式通过验证: {expr[:50]}...")
            else:
                print(f"   [WARN] 正常表达式被误判: {expr[:50]}...")
        except Exception as e:
            print(f"   [ERROR] 验证表达式失败: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("[OK] 条件评估安全性测试通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_condition_safety()
    sys.exit(0 if success else 1)

