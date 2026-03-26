"""
测试动态工作流执行，调试问题
"""
import asyncio
import sys
import os
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_workflow():
    """测试工作流执行"""
    from src.core.dynamic_execution_engine import DynamicExecutionEngine
    from src.core.agents.state_manager import InMemoryStateStore
    
    # 初始化引擎
    engine = DynamicExecutionEngine(
        enable_learning=False,
        enable_state_persistence=False,
        state_store=InMemoryStateStore()
    )
    
    await engine.initialize()
    
    # 测试用户输入
    user_input = "分析一下销售订单，生成分析报告，作为邮件主体发送给刘玉斌，yubin.liu@pcitc.com"
    
    print("="*80)
    print("测试动态工作流执行")
    print("="*80)
    print(f"用户输入: {user_input}\n")
    
    # 执行工作流
    chunk_count = 0
    agent_results = {}
    
    try:
        async for chunk in engine.execute_dynamic_workflow(
            user_input=user_input,
            context={},
            stream=True
        ):
            chunk_count += 1
            chunk_type = chunk.get("type", "unknown")
            stage = chunk.get("stage", "")
            
            print(f"\n[Chunk {chunk_count}] Type: {chunk_type}, Stage: {stage}")
            
            if chunk_type == "thinking":
                print(f"  消息: {chunk.get('message', '')}")
            elif chunk_type == "execution":
                if stage == "agent_start":
                    agent_id = chunk.get("agent_id")
                    agent_type = chunk.get("agent_type")
                    print(f"  开始执行: {agent_id} ({agent_type})")
                elif stage == "agent_complete":
                    agent_id = chunk.get("agent_id")
                    result = chunk.get("result", {})
                    agent_results[agent_id] = result
                    
                    # 检查结果
                    if isinstance(result, dict):
                        if result.get("decision") == "no_tool_needed":
                            print(f"  ⚠️  {agent_id} 决定不需要工具: {result.get('reason')}")
                        elif result.get("execution_success") == False:
                            print(f"  ❌ {agent_id} 执行失败: {result.get('error', 'Unknown error')}")
                        elif "raw_result" in result or "formatted_result" in result:
                            print(f"  ✅ {agent_id} 执行成功")
                            if "raw_result" in result:
                                raw = result["raw_result"]
                                if isinstance(raw, (dict, list)):
                                    print(f"     结果类型: {type(raw).__name__}, 大小: {len(str(raw))} 字符")
                                else:
                                    print(f"     结果: {str(raw)[:100]}...")
                        else:
                            print(f"  ✅ {agent_id} 执行完成")
                            print(f"     结果键: {list(result.keys())[:5]}")
                    else:
                        print(f"  ✅ {agent_id} 执行完成 (结果类型: {type(result).__name__})")
            elif chunk_type == "complete":
                final_result = chunk.get("final_result", {})
                print(f"\n最终结果:")
                if isinstance(final_result, dict):
                    print(f"  键: {list(final_result.keys())}")
                    if "content" in final_result:
                        content = final_result["content"]
                        print(f"  内容长度: {len(str(content))} 字符")
                        print(f"  内容预览: {str(content)[:200]}...")
                else:
                    print(f"  结果类型: {type(final_result).__name__}")
                    print(f"  结果预览: {str(final_result)[:200]}...")
            
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print(f"总共收到 {chunk_count} 个chunk")
    print(f"智能体结果数量: {len(agent_results)}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_workflow())

