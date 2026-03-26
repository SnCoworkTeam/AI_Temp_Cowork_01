"""
端到端测试：从用户输入到最终结果
测试完整的智能体执行流程
"""
import asyncio
import json
import logging
import sys
import os
import httpx
from typing import Dict, Any, List
from datetime import datetime

# 配置日志和输出编码
import sys
import io
# 设置标准输出为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# API Gateway URL
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
DYNAMIC_WORKFLOW_URL = f"{API_GATEWAY_URL}/api/v1/dynamic-workflow/execute"


async def test_scenario(
    scenario_name: str,
    user_input: str,
    context: Dict[str, Any] = None,
    timeout: float = 120.0
) -> Dict[str, Any]:
    """
    测试一个场景并收集流式输出
    
    Args:
        scenario_name: 场景名称
        user_input: 用户输入
        context: 上下文信息
        timeout: 超时时间（秒）
        
    Returns:
        测试结果
    """
    print(f"\n{'='*80}")
    print(f"测试场景: {scenario_name}")
    print(f"{'='*80}")
    print(f"用户输入: {user_input}")
    print(f"{'='*80}\n")
    
    chunks: List[Dict[str, Any]] = []
    final_result = None
    error_occurred = False
    error_message = None
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 准备请求数据
            request_data = {
                "user_input": user_input,
                "context": context or {},
                "stream": True
            }
            
            print(f"📤 发送请求到: {DYNAMIC_WORKFLOW_URL}")
            print(f"📝 请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}\n")
            
            # 发送流式请求
            async with client.stream(
                "POST",
                DYNAMIC_WORKFLOW_URL,
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                }
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_message = error_text.decode('utf-8', errors='ignore')
                    print(f"❌ [错误] HTTP {response.status_code}: {error_message}")
                    return {
                        "scenario_name": scenario_name,
                        "user_input": user_input,
                        "success": False,
                        "error": f"HTTP {response.status_code}: {error_message}",
                        "chunks": []
                    }
                
                print("📥 开始接收流式响应...\n")
                
                # 处理流式响应
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    # 解析SSE格式: data: {...}
                    if line.startswith("data: "):
                        try:
                            data_str = line[6:]  # 移除 "data: " 前缀
                            chunk = json.loads(data_str)
                            chunks.append(chunk)
                            
                            # 实时输出关键信息
                            chunk_type = chunk.get("type", "unknown")
                            stage = chunk.get("stage", "")
                            message = chunk.get("message", "")
                            
                            if chunk_type == "thinking":
                                print(f"🧠 [思考] {message}")
                            elif chunk_type == "design":
                                if stage == "network_designed":
                                    print(f"📐 [设计] 工作流网络已设计")
                                    network = chunk.get("network_summary", {})
                                    if network:
                                        layers = network.get("layers", [])
                                        print(f"   层数: {len(layers)}")
                                        for i, layer in enumerate(layers, 1):
                                            agents = layer.get("agents", [])
                                            print(f"   第{i}层: {len(agents)}个智能体")
                                elif stage == "design_complete":
                                    print(f"✅ [设计] 工作流设计完成")
                            elif chunk_type == "execution":
                                if stage == "layer_start":
                                    layer_num = chunk.get("layer_number", 0)
                                    total_layers = chunk.get("total_layers", 0)
                                    print(f"🚀 [执行] 开始执行第{layer_num}/{total_layers}层")
                                elif stage == "agent_start":
                                    agent_id = chunk.get("agent_id", "unknown")
                                    task = chunk.get("agent_task", "")
                                    print(f"   🤖 智能体: {agent_id}")
                                    if task:
                                        print(f"      任务: {task[:100]}...")
                                elif stage == "agent_complete":
                                    agent_id = chunk.get("agent_id", "unknown")
                                    result = chunk.get("agent_result", {})
                                    success = result.get("success", False)
                                    time = result.get("execution_time", 0)
                                    status = "✅" if success else "❌"
                                    print(f"   {status} 完成: {agent_id} (耗时: {time:.2f}s)")
                                    if not success:
                                        error_info = result.get("error", "")
                                        if error_info:
                                            print(f"      错误: {error_info[:100]}")
                                elif stage == "layer_complete":
                                    layer_num = chunk.get("layer_number", 0)
                                    print(f"✅ [执行] 第{layer_num}层执行完成")
                                elif stage == "execution_complete":
                                    final_result = chunk.get("final_result", {})
                                    print(f"\n🎉 [完成] 执行完成")
                            elif chunk_type == "error":
                                error_message = chunk.get("message", "未知错误")
                                print(f"❌ [错误] {error_message}")
                                error_occurred = True
                            
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse chunk: {line[:100]}... Error: {e}")
                        except Exception as e:
                            logger.error(f"Error processing chunk: {e}", exc_info=True)
    
    except httpx.TimeoutException:
        error_message = f"请求超时（{timeout}秒）"
        error_occurred = True
        print(f"❌ [超时] {error_message}")
    except Exception as e:
        error_message = str(e)
        error_occurred = True
        logger.error(f"Test scenario failed: {e}", exc_info=True)
        print(f"❌ [异常] {error_message}")
    
    # 提取最终结果
    if not final_result:
        for chunk in reversed(chunks):
            if chunk.get("type") == "execution" and chunk.get("stage") == "execution_complete":
                final_result = chunk.get("final_result", {})
                break
    
    # 输出最终结果摘要
    print(f"\n{'='*80}")
    print("测试结果摘要")
    print(f"{'='*80}")
    
    if error_occurred:
        print(f"❌ 测试失败: {error_message}")
        success = False
    elif final_result:
        output = final_result.get("final_output") or final_result.get("output")
        if output:
            print(f"✅ 测试成功")
            print(f"📊 最终输出: {str(output)[:200]}...")
        else:
            print(f"⚠️  测试完成但无输出")
            success = True
    else:
        print(f"⚠️  测试完成但未找到最终结果")
        success = len(chunks) > 0
    
    print(f"📦 接收到的数据块数: {len(chunks)}")
    print(f"{'='*80}\n")
    
    return {
        "scenario_name": scenario_name,
        "user_input": user_input,
        "success": success,
        "error": error_message if error_occurred else None,
        "chunks_count": len(chunks),
        "final_result": final_result,
        "chunks": chunks[:10]  # 只保存前10个chunk用于调试
    }


async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("智能体系统端到端测试")
    print("="*80)
    print(f"API Gateway: {API_GATEWAY_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 测试场景列表
    test_scenarios = [
        {
            "name": "简单查询",
            "input": "你好，请介绍一下你自己",
            "context": {}
        },
        {
            "name": "数据分析请求",
            "input": "帮我分析一下数据",
            "context": {}
        },
        {
            "name": "知识库查询",
            "input": "查询SAP相关的知识",
            "context": {}
        }
    ]
    
    results = []
    
    # 执行测试场景
    for scenario in test_scenarios:
        try:
            result = await test_scenario(
                scenario_name=scenario["name"],
                user_input=scenario["input"],
                context=scenario.get("context", {}),
                timeout=120.0
            )
            results.append(result)
            
            # 场景之间稍作延迟
            await asyncio.sleep(2)
            
        except KeyboardInterrupt:
            print("\n\n测试被用户中断")
            break
        except Exception as e:
            logger.error(f"Test scenario '{scenario['name']}' failed: {e}", exc_info=True)
            results.append({
                "scenario_name": scenario["name"],
                "user_input": scenario["input"],
                "success": False,
                "error": str(e),
                "chunks_count": 0
            })
    
    # 输出测试总结
    print(f"\n{'='*80}")
    print("测试总结")
    print(f"{'='*80}")
    
    total = len(results)
    passed = sum(1 for r in results if r.get("success", False))
    failed = total - passed
    
    for result in results:
        status = "✅ 通过" if result.get("success", False) else "❌ 失败"
        scenario_name = result.get("scenario_name", "Unknown")
        chunks_count = result.get("chunks_count", 0)
        error = result.get("error")
        
        print(f"{status} - {scenario_name} (数据块: {chunks_count})")
        if error:
            print(f"   错误: {error[:100]}...")
    
    print(f"\n总计: {total} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    if total > 0:
        print(f"成功率: {passed/total*100:.1f}%")
    print(f"{'='*80}\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}", exc_info=True)
        sys.exit(1)

