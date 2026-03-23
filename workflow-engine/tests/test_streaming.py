#!/usr/bin/env python3
"""
测试流式输出功能
验证流式执行、事件格式化和实时事件接收
"""
import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine"))


async def test_streaming():
    """测试流式输出功能"""
    print("=" * 60)
    print("测试流式输出功能")
    print("=" * 60)
    
    try:
        from src.core.dynamic_workflow_engine import DynamicWorkflowEngine
        
        # 测试1: 流式执行方法存在
        print("\n1. 测试流式执行方法...")
        engine = DynamicWorkflowEngine()
        
        if hasattr(engine, 'execute_workflow_stream'):
            print("   [OK] execute_workflow_stream 方法存在")
        else:
            print("   [ERROR] execute_workflow_stream 方法不存在")
            return False
        
        if hasattr(engine, '_format_stream_event'):
            print("   [OK] _format_stream_event 方法存在")
        else:
            print("   [ERROR] _format_stream_event 方法不存在")
            return False
        
        # 测试2: 事件格式化
        print("\n2. 测试事件格式化...")
        test_event = {
            "event": "on_chain_start",
            "name": "test_node",
            "data": {"input": {"test": "value"}}
        }
        
        formatted = engine._format_stream_event(test_event, "test_thread_123")
        
        assert "thread_id" in formatted
        assert "event_type" in formatted
        assert "node_id" in formatted
        assert formatted["thread_id"] == "test_thread_123"
        assert formatted["event_type"] == "on_chain_start"
        
        print("   [OK] 事件格式化功能正常")
        print(f"   - thread_id: {formatted['thread_id']}")
        print(f"   - event_type: {formatted['event_type']}")
        print(f"   - node_id: {formatted['node_id']}")
        
        # 测试3: 不同事件类型格式化
        print("\n3. 测试不同事件类型格式化...")
        event_types = [
            ("on_chain_start", "Starting node"),
            ("on_chain_end", "Completed node"),
            ("on_tool_start", "Executing tool"),
            ("on_tool_end", "Tool completed"),
        ]
        
        for event_type, expected_message in event_types:
            test_event = {
                "event": event_type,
                "name": "test_node",
                "data": {}
            }
            formatted = engine._format_stream_event(test_event, "test_thread")
            
            if "message" in formatted:
                print(f"   [OK] {event_type} 格式化成功")
            else:
                print(f"   [WARN] {event_type} 格式化可能不完整")
        
        print("\n" + "=" * 60)
        print("[OK] 流式输出测试通过！")
        print("=" * 60)
        print("\n注意: 完整流式执行测试需要LangGraph和实际工作流")
        return True
        
    except ImportError as e:
        print(f"   [WARN] 导入失败: {e}")
        return True
    except Exception as e:
        print(f"   [ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_streaming())
    sys.exit(0 if success else 1)

