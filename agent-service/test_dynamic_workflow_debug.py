"""
测试动态工作流执行，追踪完整流程
"""
import asyncio
import json
import logging
import sys
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def test_dynamic_workflow():
    """测试动态工作流执行"""
    try:
        # 导入必要的模块
        from src.core.dynamic_execution_engine import DynamicExecutionEngine
        from src.core.agents.state_manager import InMemoryStateStore
        
        logger.info("=" * 80)
        logger.info("开始测试动态工作流执行")
        logger.info("=" * 80)
        
        # 创建执行引擎
        logger.info("\n[步骤1] 创建动态执行引擎...")
        engine = DynamicExecutionEngine(
            enable_learning=True,
            enable_state_persistence=True,
            state_store=InMemoryStateStore()
        )
        
        # 初始化引擎
        logger.info("[步骤2] 初始化引擎（注册智能体）...")
        await engine.initialize()
        logger.info("✓ 引擎初始化完成")
        
        # 准备测试输入
        user_input = "分析一下销售订单，生成分析报告"
        context = {
            "user_id": "test_user",
            "username": "test",
            "session_id": "test_session"
        }
        
        logger.info(f"\n[步骤3] 开始执行工作流")
        logger.info(f"用户输入: {user_input}")
        logger.info(f"上下文: {json.dumps(context, ensure_ascii=False, indent=2)}")
        logger.info("-" * 80)
        
        chunk_count = 0
        design_result = None
        execution_started = False
        error_occurred = False
        last_error = None
        
        try:
            async for chunk in engine.execute_dynamic_workflow(
                user_input=user_input,
                context=context,
                stream=True
            ):
                chunk_count += 1
                chunk_type = chunk.get('type', 'unknown')
                chunk_stage = chunk.get('stage', 'N/A')
                
                logger.info(f"\n[Chunk {chunk_count}] Type: {chunk_type}, Stage: {chunk_stage}")
                
                # 记录不同类型chunk的详细信息
                if chunk_type == 'thinking':
                    logger.info(f"  → 思考阶段: {chunk.get('message', 'N/A')}")
                    logger.info(f"  → 进度: {chunk.get('progress', 0)}%")
                    if chunk.get('analysis'):
                        logger.info(f"  → 分析结果: {json.dumps(chunk.get('analysis'), ensure_ascii=False, indent=4)}")
                
                elif chunk_type == 'design':
                    logger.info(f"  → 设计阶段: {chunk.get('message', 'N/A')}")
                    if chunk.get('network_summary'):
                        summary = chunk.get('network_summary')
                        logger.info(f"  → 网络摘要: {summary.get('total_agents', 0)}个智能体, {summary.get('execution_layers', 0)}个执行层")
                
                elif chunk_type == 'design_complete':
                    design_result = chunk.get('design')
                    logger.info(f"  → 设计完成!")
                    if design_result:
                        logger.info(f"  → 智能体数量: {len(design_result.get('agents', []))}")
                        logger.info(f"  → 执行层数: {len(design_result.get('execution_layers', []))}")
                        logger.info(f"  → 设计详情: {json.dumps(design_result, ensure_ascii=False, indent=4)}")
                    else:
                        logger.error("  ✗ 设计结果为空!")
                
                elif chunk_type == 'execution':
                    if not execution_started:
                        execution_started = True
                        logger.info("\n" + "=" * 80)
                        logger.info("开始执行智能体网络")
                        logger.info("=" * 80)
                    
                    stage = chunk.get('stage', 'unknown')
                    logger.info(f"  → 执行阶段: {stage}")
                    logger.info(f"  → 消息: {chunk.get('message', 'N/A')}")
                    
                    if stage == 'agent_start':
                        logger.info(f"    • 智能体: {chunk.get('agent_id')} ({chunk.get('agent_type')})")
                        logger.info(f"    • 任务: {chunk.get('agent_task', 'N/A')}")
                    
                    elif stage == 'agent_complete':
                        result = chunk.get('agent_result', {})
                        logger.info(f"    • 智能体: {chunk.get('agent_id')} 完成")
                        logger.info(f"    • 成功: {result.get('success', False)}")
                        logger.info(f"    • 执行时间: {result.get('execution_time', 0):.2f}s")
                        if not result.get('success'):
                            logger.error(f"    • 错误: {result.get('error', 'N/A')}")
                    
                    elif stage == 'execution_complete':
                        final_result = chunk.get('final_result', {})
                        logger.info(f"  → 执行完成!")
                        logger.info(f"  → 最终结果: {json.dumps(final_result, ensure_ascii=False, indent=4)}")
                
                elif chunk_type == 'error':
                    error_occurred = True
                    last_error = chunk
                    logger.error(f"  ✗ 错误发生!")
                    logger.error(f"  → 阶段: {chunk.get('stage', 'N/A')}")
                    logger.error(f"  → 消息: {chunk.get('message', 'N/A')}")
                    logger.error(f"  → 错误: {chunk.get('error', 'N/A')}")
                    logger.error(f"  → 错误类型: {chunk.get('error_type', 'N/A')}")
                    logger.error(f"  → 完整错误chunk: {json.dumps(chunk, ensure_ascii=False, indent=4)}")
                
                else:
                    logger.warning(f"  → 未知chunk类型: {chunk_type}")
                    logger.warning(f"  → 完整chunk: {json.dumps(chunk, ensure_ascii=False, indent=4)}")
        
        except Exception as e:
            logger.error(f"\n✗ 执行过程中发生异常: {e}", exc_info=True)
            error_occurred = True
            last_error = {
                "type": "exception",
                "error": str(e),
                "error_type": type(e).__name__
            }
        
        # 总结
        logger.info("\n" + "=" * 80)
        logger.info("执行总结")
        logger.info("=" * 80)
        logger.info(f"总chunk数: {chunk_count}")
        logger.info(f"设计结果: {'✓ 已获取' if design_result else '✗ 未获取'}")
        logger.info(f"执行开始: {'✓ 是' if execution_started else '✗ 否'}")
        logger.info(f"错误发生: {'✗ 是' if error_occurred else '✓ 否'}")
        
        if error_occurred and last_error:
            logger.error(f"\n最后错误信息:")
            logger.error(json.dumps(last_error, ensure_ascii=False, indent=4))
        
        if not design_result:
            logger.error("\n✗ 问题: 设计结果为空，工作流无法继续执行")
            logger.error("可能原因:")
            logger.error("  1. LLM调用失败")
            logger.error("  2. 设计器返回了错误chunk但没有抛出异常")
            logger.error("  3. design_complete chunk中的design字段为空")
        
        return {
            "success": not error_occurred and design_result is not None,
            "chunk_count": chunk_count,
            "design_result": design_result is not None,
            "execution_started": execution_started,
            "error_occurred": error_occurred,
            "last_error": last_error
        }
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

if __name__ == "__main__":
    result = asyncio.run(test_dynamic_workflow())
    print("\n" + "=" * 80)
    print("测试结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=" * 80)
    
    if not result.get("success"):
        sys.exit(1)

