"""
通过API测试智能体系统
测试从用户输入到最终结果输出的完整流程
"""
import asyncio
import json
import logging
import sys
import os
import httpx
from typing import Dict, Any, AsyncIterator

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
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    测试一个场景并收集流式输出
    
    Args:
        scenario_name: 场景名称
        user_input: 用户输入
        context: 上下文信息
        
    Returns:
        测试结果
    """
    print(f"\n{'='*80}")
    print(f"测试场景: {scenario_name}")
    print(f"{'='*80}")
    print(f"用户输入: {user_input}")
    print(f"{'='*80}\n")
    
    full_response_content = []
    final_result = {}
    error_occurred = False
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # 准备请求数据
            request_data = {
                "user_input": user_input,
                "context": context or {},
                "stream": True
            }
            
            # 发送流式请求
            async with client.stream(
                "POST",
                DYNAMIC_WORKFLOW_URL,
                json=request_data,
                headers={"Content-Type": "application/json", "Accept": "text/event-stream"}
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"[错误] HTTP {response.status_code}: {error_text.decode('utf-8', errors='ignore')}")
                    return {
                        "scenario_name": scenario_name,
                        "user_input": user_input,
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "full_response_content": ""
                    }
                
                # 处理流式响应
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    # 解析SSE格式
                    if line.startswith("data: "):
                        data_str = line[6:]  # 移除 "data: " 前缀
                        try:
                            chunk = json.loads(data_str)
                            
                            # 实时输出关键信息
                            chunk_type = chunk.get("type", "unknown")
                            stage = chunk.get("stage", "")
                            message = chunk.get("message", "")
                            
                            if chunk_type == "thinking":
                                print(f"[思考] {message}")
                            elif chunk_type == "execution":
                                if stage == "agent_start":
                                    agent_id = chunk.get("agent_id", "unknown")
                                    task = chunk.get("agent_task", "")
                                    print(f"[执行] 智能体: {agent_id}")
                                    if task:
                                        print(f"       任务: {task}")
                                elif stage == "agent_complete":
                                    agent_id = chunk.get("agent_id", "unknown")
                                    success = chunk.get("agent_result", {}).get("success", False)
                                    print(f"[完成] 智能体: {agent_id} - 成功: {success}")
                                elif stage == "agent_error":
                                    agent_id = chunk.get("agent_id", "unknown")
                                    error_msg = chunk.get("error", "未知错误")
                                    print(f"[错误] 智能体: {agent_id} - 错误: {error_msg}")
                                    error_occurred = True
                                else:
                                    print(f"[执行] {message}")
                            elif chunk_type == "design_complete":
                                print(f"[设计完成] {message}")
                                if chunk.get("design"):
                                    design = chunk.get("design", {})
                                    print(f"       网络设计: {json.dumps(design, ensure_ascii=False, indent=2)}")
                            elif chunk_type == "execution_complete":
                                final_result = chunk.get("final_result", {})
                                print(f"[执行完成] {message}")
                                if final_result.get("formatted_output"):
                                    print(f"\n最终输出:\n{final_result['formatted_output']}")
                            elif chunk_type == "error":
                                error_msg = chunk.get("error", message)
                                print(f"[全局错误] {message}")
                                if error_msg and error_msg != message:
                                    print(f"        详细错误: {error_msg}")
                                error_occurred = True
                            else:
                                if message:
                                    print(f"[消息] {message}")
                            
                            # 收集最终输出
                            if chunk_type == "execution_complete" and final_result.get("formatted_output"):
                                full_response_content.append(final_result["formatted_output"])
                            elif message and chunk_type not in ["thinking", "execution"]:
                                full_response_content.append(message)
                                
                        except json.JSONDecodeError:
                            # 如果不是JSON，直接输出
                            if data_str.strip():
                                print(f"[数据] {data_str}")
                                full_response_content.append(data_str)
                                
        return {
            "scenario_name": scenario_name,
            "user_input": user_input,
            "success": not error_occurred and bool(final_result),
            "final_result": final_result,
            "full_response_content": "\n".join(full_response_content)
        }
        
    except Exception as e:
        logger.error(f"测试场景 '{scenario_name}' 执行失败: {e}", exc_info=True)
        print(f"[异常] 测试执行失败: {e}")
        return {
            "scenario_name": scenario_name,
            "user_input": user_input,
            "success": False,
            "error": str(e),
            "full_response_content": "\n".join(full_response_content)
        }


async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("智能体系统API测试")
    print("="*80)
    print(f"API Gateway URL: {API_GATEWAY_URL}")
    print(f"动态工作流URL: {DYNAMIC_WORKFLOW_URL}")
    print("="*80)
    
    # 检查服务是否可用
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            health_response = await client.get(f"{API_GATEWAY_URL}/health")
            if health_response.status_code != 200:
                print(f"[警告] API Gateway健康检查失败: {health_response.status_code}")
            else:
                print("[成功] API Gateway 可用")
    except Exception as e:
        print(f"[警告] 无法连接到API Gateway: {e}")
        print("请确保服务正在运行: docker-compose ps")
        return False
    
    results = []
    
    # 场景1: 简单的知识库查询
    print("\n开始测试场景1...")
    results.append(await test_scenario(
        "知识库查询 - 销售订单",
        "什么是销售订单？",
        {"user_id": "test_user_1"}
    ))
    
    # 场景2: MCP工具执行 - 发送邮件（如果配置了）
    print("\n开始测试场景2...")
    results.append(await test_scenario(
        "MCP工具执行 - 发送邮件",
        "发送一封邮件给yubin.liu@pcitc.com，主题是测试邮件，内容是这是一封测试邮件。",
        {"user_id": "test_user_2"}
    ))
    
    # 输出测试总结
    print(f"\n{'='*80}")
    print("测试总结")
    print(f"{'='*80}")
    
    for res in results:
        status = "[通过]" if res.get("success") else "[失败]"
        print(f"\n{status} - {res['scenario_name']}")
        print(f"  用户输入: {res['user_input']}")
        if res.get("error"):
            print(f"  错误: {res['error']}")
        if res.get("full_response_content"):
            content_preview = res['full_response_content'][:200] + "..." if len(res['full_response_content']) > 200 else res['full_response_content']
            print(f"  输出预览: {content_preview}")
    
    total = len(results)
    passed = sum(1 for r in results if r.get("success"))
    failed = total - passed
    
    print(f"\n总计: {total} 个测试场景")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    if total > 0:
        print(f"成功率: {passed/total*100:.1f}%")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试执行失败: {e}", exc_info=True)
        sys.exit(1)

