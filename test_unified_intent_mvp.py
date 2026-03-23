"""
统一意图识别MVP测试脚本
测试SSE流式响应和API功能
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


def test_sse_stream(url: str, user_input: str, user_id: Optional[str] = None, session_id: Optional[str] = None):
    """测试SSE流式响应"""
    print(f"\n{'='*60}")
    print(f"测试SSE流式响应")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"用户输入: {user_input}")
    print(f"{'='*60}\n")
    
    # 构建查询参数
    params = {"input": user_input}
    if user_id:
        params["user_id"] = user_id
    if session_id:
        params["session_id"] = session_id
    
    try:
        # 使用requests的流式响应
        response = requests.get(url, params=params, stream=True, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        print(f"✅ 连接成功，开始接收流式数据...\n")
        
        chunk_count = 0
        for line in response.iter_lines():
            if not line:
                continue
            
            line = line.decode('utf-8').strip()
            
            if line.startswith('data: '):
                data_str = line[6:]  # 移除 'data: ' 前缀
                try:
                    chunk = json.loads(data_str)
                    chunk_count += 1
                    
                    # 显示接收到的数据块
                    print(f"[块 {chunk_count}] 阶段: {chunk.get('stage', 'unknown')}")
                    print(f"  状态: {chunk.get('status', 'unknown')}")
                    print(f"  进度: {chunk.get('progress', 0)}%")
                    
                    if chunk.get('message'):
                        print(f"  消息: {chunk.get('message')}")
                    
                    if chunk.get('result'):
                        result = chunk.get('result')
                        if isinstance(result, dict):
                            if 'task_type' in result:
                                print(f"  任务类型: {result.get('task_type')}")
                                print(f"  置信度: {result.get('confidence', 0)}")
                            elif 'success' in result:
                                print(f"  执行成功: {result.get('success')}")
                                if 'output' in result:
                                    output = result.get('output', '')
                                    if len(output) > 100:
                                        output = output[:100] + "..."
                                    print(f"  输出: {output}")
                    
                    if chunk.get('error'):
                        print(f"  [ERROR] 错误: {chunk.get('error')}")
                    
                    print()
                    
                    # 检查是否完成
                    if chunk.get('stage') in ['complete', 'error']:
                        print(f"✅ 流式响应完成（共接收 {chunk_count} 个数据块）")
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


def test_post_api(url: str, user_input: str, user_id: Optional[str] = None, session_id: Optional[str] = None):
    """测试POST API"""
    print(f"\n{'='*60}")
    print(f"测试POST API")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"用户输入: {user_input}")
    print(f"{'='*60}\n")
    
    payload = {
        "user_input": user_input
    }
    
    if user_id:
        payload["user_id"] = user_id
    if session_id:
        payload["session_id"] = session_id
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        print(f"✅ 连接成功，开始接收流式数据...\n")
        
        chunk_count = 0
        for line in response.iter_lines():
            if not line:
                continue
            
            line = line.decode('utf-8').strip()
            
            if line.startswith('data: '):
                data_str = line[6:]
                try:
                    chunk = json.loads(data_str)
                    chunk_count += 1
                    
                    print(f"[块 {chunk_count}] {chunk.get('stage', 'unknown')} - {chunk.get('progress', 0)}%")
                    
                    if chunk.get('stage') in ['complete', 'error']:
                        print(f"✅ 流式响应完成（共接收 {chunk_count} 个数据块）")
                        return True
                
                except json.JSONDecodeError:
                    pass
        
        return True
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("="*60)
    print("统一意图识别MVP测试")
    print("="*60)
    
    # 配置
    base_url = "http://localhost:8010"  # agent-service端口（从docker-compose.yml）
    api_url = f"{base_url}/api/v1/unified/process"
    
    # 首先检查服务是否可用
    print("\n检查服务状态...")
    try:
        health_response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        if health_response.status_code == 200:
            print("[OK] agent-service 服务正常")
        else:
            print(f"[WARN] agent-service 健康检查返回: {health_response.status_code}")
    except Exception as e:
        print(f"[ERROR] 无法连接到agent-service: {e}")
        print("请确保服务已启动: docker-compose up -d agent-service")
        print("等待服务启动中...")
        time.sleep(5)
        # 重试一次
        try:
            health_response = requests.get(f"{base_url}/api/v1/health", timeout=10)
            if health_response.status_code == 200:
                print("[OK] agent-service 服务已就绪")
            else:
                print(f"[WARN] 服务可能还在启动中，继续测试...")
        except:
            print("[WARN] 服务可能还在启动中，继续测试...")
    
    # 测试用例
    test_cases = [
        {
            "name": "简单查询",
            "input": "你好，介绍一下你自己",
            "user_id": "test_user_001",
            "session_id": "test_session_001"
        },
        {
            "name": "工具执行",
            "input": "查询采购订单",
            "user_id": "test_user_002",
            "session_id": "test_session_002"
        }
    ]
    
    # 测试SSE流式响应（GET方式）
    print("\n" + "="*60)
    print("测试1: SSE流式响应（GET方式）")
    print("="*60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {test_case['name']} ---")
        success = test_sse_stream(
            api_url,
            test_case['input'],
            test_case.get('user_id'),
            test_case.get('session_id')
        )
        
        if success:
            print(f"[OK] 测试用例 {i} 通过")
        else:
            print(f"[FAIL] 测试用例 {i} 失败")
        
        # 等待一下再进行下一个测试
        time.sleep(1)
    
    # 测试POST API
    print("\n" + "="*60)
    print("测试2: POST API")
    print("="*60)
    
    test_case = test_cases[0]
    success = test_post_api(
        api_url,
        test_case['input'],
        test_case.get('user_id'),
        test_case.get('session_id')
    )
    
    if success:
        print("[OK] POST API测试通过")
    else:
        print("[FAIL] POST API测试失败")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


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

