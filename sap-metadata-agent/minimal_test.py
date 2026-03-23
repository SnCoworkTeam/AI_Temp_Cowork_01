"""
最小化测试 - 只测试发送POST请求
"""
import asyncio
import httpx
import json

async def test():
    url = "http://localhost:8004/api/documents/create"
    data = {
        "title": "最小测试",
        "content": "这是最小测试",
        "category": "test",
        "tags": ["test"],
        "metadata": {},
        "process_async": False
    }
    
    print("=" * 60)
    print("最小化测试 - 直接发送POST请求")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    print("\n发送请求...")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=data)
            print(f"\n收到响应!")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            if response.status_code == 200:
                print("\n✅ 成功!")
                return True
            else:
                print("\n❌ 失败")
                return False
    except httpx.ConnectError as e:
        print(f"\n❌ 连接错误: {e}")
        return False
    except httpx.TimeoutException:
        print(f"\n❌ 超时")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    print(f"\n结果: {'成功' if result else '失败'}")

