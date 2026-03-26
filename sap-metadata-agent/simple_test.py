"""
最简单的测试 - 直接发送HTTP请求
"""
import asyncio
import httpx
import sys

async def simple_test():
    url = "http://localhost:8004/api/documents/create"
    data = {
        "title": "简单测试",
        "content": "测试内容",
        "category": "test",
        "tags": ["test"],
        "metadata": {},
        "process_async": False
    }
    
    print(f"发送请求到: {url}")
    print(f"数据: {data}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("正在发送...")
            response = await client.post(url, json=data)
            print(f"响应状态: {response.status_code}")
            print(f"响应内容: {response.text[:200]}")
            return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(simple_test())
    sys.exit(0 if result else 1)

