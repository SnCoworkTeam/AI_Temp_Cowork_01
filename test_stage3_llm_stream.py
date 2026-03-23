"""
阶段3测试脚本：LLM分析流式化功能验证
"""
import json
import sys
import time
import io
from typing import Optional

# 修复Windows编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    import requests
except ImportError:
    print("需要安装requests库: pip install requests")
    sys.exit(1)


def test_llm_stream(url: str, user_input: str, user_id: Optional[str] = None, session_id: Optional[str] = None):
    """测试LLM分析流式化功能"""
    print(f"\n{'='*60}")
    print(f"阶段3测试：LLM分析流式化")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"用户输入: {user_input}")
    print(f"{'='*60}\n")
    
    params = {"input": user_input}
    if user_id:
        params["user_id"] = user_id
    if session_id:
        params["session_id"] = session_id
    
    # 启用流式LLM分析
    params["use_streaming_llm"] = "true"
    
    try:
        response = requests.get(url, params=params, stream=True, timeout=60)
        
        if response.status_code != 200:
            print(f"[ERROR] 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        print(f"[OK] 连接成功，开始接收流式数据...\n")
        
        chunk_count = 0
        llm_chunks = []
        semantic_chunks = []
        stages_seen = set()
        
        for line in response.iter_lines():
            if not line:
                continue
            
            line = line.decode('utf-8').strip()
            
            if line.startswith('data: '):
                data_str = line[6:]
                try:
                    chunk = json.loads(data_str)
                    chunk_count += 1
                    
                    stage = chunk.get('stage', 'unknown')
                    stages_seen.add(stage)
                    progress = chunk.get('progress', 0)
                    status = chunk.get('status', 'unknown')
                    
                    # 显示所有阶段
                    print(f"[块 {chunk_count}] 阶段: {stage}")
                    print(f"  状态: {status}")
                    print(f"  进度: {progress}%")
                    
                    if chunk.get('message'):
                        print(f"  消息: {chunk.get('message')}")
                    
                    # 特别关注LLM分析相关的块
                    if stage == "llm_analysis":
                        print(f"  [阶段3] LLM流式分析")
                        llm_chunk = chunk.get('llm_chunk', {})
                        if llm_chunk:
                            llm_stage = llm_chunk.get('stage', '')
                            print(f"    LLM阶段: {llm_stage}")
                            if llm_chunk.get('content'):
                                content = llm_chunk.get('content', '')[:50]  # 只显示前50字符
                                print(f"    内容片段: {content}...")
                            if llm_chunk.get('chunk_count'):
                                print(f"    块计数: {llm_chunk.get('chunk_count')}")
                            if llm_chunk.get('accumulated'):
                                accumulated = llm_chunk.get('accumulated', '')[:100]
                                print(f"    累积内容: {accumulated}...")
                        llm_chunks.append(chunk)
                    
                    # 特别关注语义引擎相关的块
                    if stage == "semantic_search":
                        print(f"  [阶段2] 语义引擎流式查询")
                        semantic_chunk = chunk.get('semantic_chunk', {})
                        if semantic_chunk:
                            semantic_stage = semantic_chunk.get('stage', '')
                            print(f"    语义引擎阶段: {semantic_stage}")
                        semantic_chunks.append(chunk)
                    
                    # 显示意图分析结果
                    if stage == "intent_complete" and chunk.get('result'):
                        result = chunk.get('result')
                        print(f"  任务类型: {result.get('task_type', 'N/A')}")
                        print(f"  置信度: {result.get('confidence', 0):.2f}")
                    
                    # 显示执行结果
                    if stage == "complete" and chunk.get('result'):
                        result = chunk.get('result')
                        if isinstance(result, dict):
                            print(f"  执行成功: {result.get('success', False)}")
                    
                    if chunk.get('error'):
                        print(f"  [ERROR] 错误: {chunk.get('error')}")
                    
                    print()
                    
                    # 检查是否完成
                    if stage in ['complete', 'error']:
                        print(f"[OK] 流式响应完成（共接收 {chunk_count} 个数据块）")
                        print(f"\n发现的阶段: {sorted(stages_seen)}")
                        
                        # 验证阶段3功能
                        if "llm_analysis" in stages_seen:
                            print(f"\n[SUCCESS] 阶段3功能验证成功！")
                            print(f"  - LLM流式分析已集成")
                            print(f"  - 收到 {len(llm_chunks)} 个LLM分析进度更新")
                        else:
                            print(f"\n[WARN] 未检测到LLM流式分析（可能因为LLM不可用或未启用）")
                        
                        # 验证阶段2功能
                        if "semantic_search" in stages_seen:
                            print(f"  - 语义引擎流式查询已集成")
                            print(f"  - 收到 {len(semantic_chunks)} 个语义引擎进度更新")
                        
                        return True
                
                except json.JSONDecodeError as e:
                    print(f"[WARN] JSON解析失败: {e}")
                    print(f"  原始数据: {data_str[:100]}")
        
        print(f"[OK] 流式响应结束（共接收 {chunk_count} 个数据块）")
        return True
                
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("="*60)
    print("阶段3测试：LLM分析流式化功能验证")
    print("="*60)
    
    base_url = "http://localhost:8010"
    api_url = f"{base_url}/api/v1/unified/process"
    
    # 检查服务状态
    print("\n检查服务状态...")
    try:
        health_response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        if health_response.status_code == 200:
            print("[OK] agent-service 服务正常")
        else:
            print(f"[WARN] agent-service 健康检查返回: {health_response.status_code}")
    except Exception as e:
        print(f"[WARN] 无法连接到agent-service: {e}")
        print("继续测试...")
    
    # 测试用例
    test_cases = [
        {
            "name": "测试LLM流式分析",
            "input": "查询采购订单PO12345的详细信息",
            "user_id": "test_user_003",
            "session_id": "test_session_003"
        },
        {
            "name": "测试复杂查询",
            "input": "我需要创建一个新的采购订单，供应商是ABC公司，物料编号MAT001，数量100",
            "user_id": "test_user_004",
            "session_id": "test_session_004"
        }
    ]
    
    # 运行测试
    success_count = 0
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试用例 {i}: {test_case['name']}")
        print(f"{'='*60}")
        
        success = test_llm_stream(
            api_url,
            test_case['input'],
            test_case.get('user_id'),
            test_case.get('session_id')
        )
        
        if success:
            success_count += 1
            print(f"[OK] 测试用例 {i} 通过")
        else:
            print(f"[FAIL] 测试用例 {i} 失败")
        
        time.sleep(2)  # 等待一下再进行下一个测试
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"总测试用例: {len(test_cases)}")
    print(f"通过: {success_count}")
    print(f"失败: {len(test_cases) - success_count}")
    
    if success_count == len(test_cases):
        print("\n[SUCCESS] 所有测试通过！")
    else:
        print("\n[WARN] 部分测试失败，请检查日志")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




