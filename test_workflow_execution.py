#!/usr/bin/env python3
"""
测试动态工作流执行，详细检查每个智能体的执行状态
"""
import requests
import json
import sys

def test_workflow_execution():
    """测试工作流执行"""
    url = "http://43.143.139.197:8001/api/v1/dynamic-workflow/execute"
    payload = {
        "user_input": "查询组织架构"
    }
    
    print("=" * 80)
    print("开始测试工作流执行：查询组织架构")
    print("=" * 80)
    print()
    
    agent_results = {}
    agent_status = {}
    final_result = None
    chunk_count = 0
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=300)
        response.raise_for_status()
        
        print("开始接收流式响应...")
        print("-" * 80)
        
        for line in response.iter_lines():
            if not line:
                continue
                
            try:
                # 尝试解析 SSE 格式
                if line.startswith(b'data: '):
                    line = line[6:]  # 移除 'data: ' 前缀
                
                chunk = json.loads(line.decode('utf-8'))
                chunk_count += 1
                
                chunk_type = chunk.get("type", "unknown")
                stage = chunk.get("stage", "")
                message = chunk.get("message", "")
                
                # 打印关键信息
                if chunk_type == "thinking":
                    print(f"[思考] {message}")
                elif chunk_type == "execution":
                    if stage == "execution_start":
                        print(f"\n[执行开始] {message}")
                    elif stage == "layer_start":
                        print(f"\n[层开始] {message}")
                    elif stage == "agent_complete":
                        agent_id = chunk.get("agent_id", "unknown")
                        agent_result = chunk.get("agent_result", {})
                        success = agent_result.get("success", True)
                        execution_time = agent_result.get("execution_time", 0)
                        confidence = agent_result.get("confidence", 0)
                        
                        status = "✓ 成功" if success else "✗ 失败"
                        print(f"  [{status}] 智能体 {agent_id}: {execution_time:.2f}s, 置信度: {confidence*100:.0f}%")
                        
                        agent_status[agent_id] = {
                            "success": success,
                            "execution_time": execution_time,
                            "confidence": confidence
                        }
                        
                        # 保存详细结果
                        if agent_id not in agent_results:
                            agent_results[agent_id] = chunk
                    elif stage == "layer_complete":
                        print(f"[层完成] {message}")
                    elif stage == "execution_complete":
                        print(f"\n[执行完成] {message}")
                        final_result = chunk.get("final_result") or chunk.get("result") or chunk.get("data", {}).get("result")
                elif chunk_type == "error":
                    print(f"[错误] {message}")
                    if "error" in chunk:
                        print(f"  错误详情: {chunk['error']}")
                
            except json.JSONDecodeError as e:
                print(f"[解析错误] 无法解析JSON: {line[:100]}")
            except Exception as e:
                print(f"[处理错误] {e}")
        
        print()
        print("=" * 80)
        print("执行摘要")
        print("=" * 80)
        print(f"总chunk数: {chunk_count}")
        print(f"智能体数量: {len(agent_status)}")
        print()
        
        print("智能体执行状态:")
        print("-" * 80)
        for agent_id, status in agent_status.items():
            success_icon = "✓" if status["success"] else "✗"
            print(f"  {success_icon} {agent_id}: "
                  f"成功={status['success']}, "
                  f"时间={status['execution_time']:.2f}s, "
                  f"置信度={status['confidence']*100:.0f}%")
        
        print()
        if final_result:
            print("最终结果:")
            print("-" * 80)
            if isinstance(final_result, dict):
                formatted_output = final_result.get("formatted_output") or final_result.get("output") or final_result.get("final_output")
                if formatted_output:
                    print(f"格式化输出长度: {len(str(formatted_output))} 字符")
                    print(f"预览: {str(formatted_output)[:200]}...")
                else:
                    print(json.dumps(final_result, ensure_ascii=False, indent=2)[:500])
            else:
                print(str(final_result)[:500])
        else:
            print("⚠️  未找到最终结果")
        
        # 检查是否有失败的智能体
        failed_agents = [aid for aid, status in agent_status.items() if not status["success"]]
        if failed_agents:
            print()
            print("⚠️  失败的智能体:")
            for aid in failed_agents:
                print(f"  - {aid}")
        else:
            print()
            print("✓ 所有智能体执行成功")
        
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return False
    except Exception as e:
        print(f"执行错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return len(failed_agents) == 0 if 'failed_agents' in locals() else False

if __name__ == "__main__":
    success = test_workflow_execution()
    sys.exit(0 if success else 1)

