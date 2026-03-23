"""
测试所有智能体
从用户输入到结果输出的完整流程测试
"""
import asyncio
import json
import logging
import sys
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目路径
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.dynamic_execution_engine import DynamicExecutionEngine
try:
    from src.core.state_manager import InMemoryStateStore
except ImportError:
    # 如果state_manager不存在，使用None
    InMemoryStateStore = None


async def test_scenario(
    engine: DynamicExecutionEngine,
    scenario_name: str,
    user_input: str,
    context: Dict[str, Any] = None
):
    """测试单个场景"""
    print(f"\n{'='*80}")
    print(f"测试场景: {scenario_name}")
    print(f"用户输入: {user_input}")
    print(f"{'='*80}\n")
    
    context = context or {}
    
    try:
        # 执行动态工作流
        chunks = []
        async for chunk in engine.execute_dynamic_workflow(
            user_input=user_input,
            context=context,
            stream=True
        ):
            chunks.append(chunk)
            
            # 实时输出关键信息
            chunk_type = chunk.get("type", "unknown")
            stage = chunk.get("stage", "")
            message = chunk.get("message", "")
            
            if chunk_type == "thinking":
                print(f"🧠 [思考] {message}")
            elif chunk_type == "execution":
                if stage == "agent_start":
                    agent_id = chunk.get("agent_id", "unknown")
                    task = chunk.get("agent_task", "")
                    print(f"🚀 [执行] 智能体: {agent_id}")
                    if task:
                        print(f"   任务: {task}")
                elif stage == "agent_complete":
                    agent_id = chunk.get("agent_id", "unknown")
                    result = chunk.get("agent_result", {})
                    success = result.get("success", False)
                    time = result.get("execution_time", 0)
                    status = "✅" if success else "❌"
                    print(f"{status} [完成] 智能体: {agent_id} (耗时: {time:.2f}s)")
                elif stage == "execution_complete":
                    final_result = chunk.get("final_result", {})
                    print(f"\n🎉 [完成] 执行完成")
                    if final_result:
                        output = final_result.get("final_output") or final_result.get("output")
                        if output:
                            print(f"   结果: {str(output)[:200]}...")
            elif chunk_type == "error":
                error_msg = chunk.get("message", "未知错误")
                print(f"❌ [错误] {error_msg}")
        
        # 提取最终结果
        final_chunk = None
        for chunk in reversed(chunks):
            if chunk.get("type") == "execution" and chunk.get("stage") == "execution_complete":
                final_chunk = chunk
                break
        
        if final_chunk:
            final_result = final_chunk.get("final_result", {})
            print(f"\n{'='*80}")
            print("最终结果:")
            print(f"{'='*80}")
            print(json.dumps(final_result, ensure_ascii=False, indent=2))
        else:
            print("\n⚠️  未找到最终结果")
        
        return True
        
    except Exception as e:
        logger.error(f"测试场景 '{scenario_name}' 失败: {e}", exc_info=True)
        print(f"\n❌ [失败] {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("智能体系统完整测试")
    print("="*80)
    
    # 初始化执行引擎
    print("\n初始化执行引擎...")
    state_store = InMemoryStateStore() if InMemoryStateStore else None
    engine = DynamicExecutionEngine(
        enable_learning=False,  # 暂时禁用学习功能
        enable_state_persistence=state_store is not None,
        state_store=state_store
    )
    
    # 初始化智能体注册
    print("注册智能体...")
    await engine.initialize()
    print(f"✅ 已注册 {len(engine.agent_pool)} 个智能体")
    
    # 测试场景列表
    test_scenarios = [
        {
            "name": "简单问答",
            "input": "你好，介绍一下你自己",
            "context": {}
        },
        {
            "name": "知识库查询",
            "input": "查询一下关于SAP的知识",
            "context": {}
        },
        {
            "name": "数据查询",
            "input": "查询销售订单数据，只显示前5条",
            "context": {}
        },
        {
            "name": "工具执行",
            "input": "发送一封邮件给yubin.liu@pcitc.com，主题是测试，内容是这是一封测试邮件",
            "context": {}
        },
        {
            "name": "复杂分析",
            "input": "分析一下销售订单，生成分析报告",
            "context": {}
        }
    ]
    
    # 执行测试
    results = []
    for scenario in test_scenarios:
        success = await test_scenario(
            engine,
            scenario["name"],
            scenario["input"],
            scenario.get("context", {})
        )
        results.append({
            "scenario": scenario["name"],
            "success": success
        })
        
        # 等待一下，避免请求过快
        await asyncio.sleep(1)
    
    # 输出测试总结
    print(f"\n{'='*80}")
    print("测试总结")
    print(f"{'='*80}")
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    
    for result in results:
        status = "✅ 通过" if result["success"] else "❌ 失败"
        print(f"{status} - {result['scenario']}")
    
    print(f"\n总计: {total} 个场景")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"成功率: {passed/total*100:.1f}%")
    
    # 关闭引擎
    if hasattr(engine, 'close'):
        await engine.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        logger.error(f"测试执行失败: {e}", exc_info=True)
        sys.exit(1)

