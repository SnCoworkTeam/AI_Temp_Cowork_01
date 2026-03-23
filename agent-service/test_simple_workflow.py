"""
简单的动态工作流测试
快速验证修复是否生效
"""
import asyncio
import httpx
import json
import sys

async def test_simple():
    """测试简单的动态工作流"""
    url = "http://localhost:8080/api/v1/dynamic-workflow/execute"
    
    request_data = {
        "user_input": "你好",
        "context": {},
        "stream": True
    }
    
    print(f"发送请求到: {url}")
    print(f"请求数据: {json.dumps(request_data, ensure_ascii=False)}\n")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                url,
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                }
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"错误: HTTP {response.status_code}: {error_text.decode('utf-8', errors='ignore')}")
                    return False
                
                print("开始接收流式响应...\n")
                chunk_count = 0
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        try:
                            data_str = line[6:]
                            chunk = json.loads(data_str)
                            chunk_count += 1
                            
                            chunk_type = chunk.get("type", "unknown")
                            stage = chunk.get("stage", "")
                            message = chunk.get("message", "")
                            
                            print(f"[{chunk_count}] {chunk_type}/{stage}: {message[:80]}")
                            
                            # 如果收到完成或错误，退出
                            if chunk_type == "error" or (chunk_type == "execution" and stage == "execution_complete"):
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"解析错误: {line[:100]}")
                
                print(f"\n完成！收到 {chunk_count} 个数据块")
                return chunk_count > 0
                
    except httpx.TimeoutException:
        print("请求超时")
        return False
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple())
    sys.exit(0 if success else 1)

