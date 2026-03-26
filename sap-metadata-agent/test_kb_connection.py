"""
快速测试知识库服务连接
"""
import asyncio
import httpx
import os

async def test_kb_connection():
    """测试知识库服务连接"""
    knowledge_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://localhost:8004")
    
    print("=" * 80)
    print("测试知识库服务连接")
    print("=" * 80)
    print(f"知识库URL: {knowledge_base_url}\n")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试健康检查
            print("1. 测试健康检查端点...")
            health_url = f"{knowledge_base_url}/api/health"
            print(f"   URL: {health_url}")
            
            try:
                response = await client.get(health_url)
                print(f"   状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"   ✅ 健康检查成功")
                    print(f"   响应: {response.json()}")
                else:
                    print(f"   ⚠️  响应异常: {response.text}")
            except httpx.ConnectError as e:
                print(f"   ❌ 连接失败: {e}")
                print(f"   请确认知识库服务是否运行在 {knowledge_base_url}")
                return False
            except httpx.TimeoutException:
                print(f"   ❌ 连接超时")
                return False
            
            print()
            
            # 测试创建文档端点
            print("2. 测试创建文档端点...")
            create_url = f"{knowledge_base_url}/api/documents/create"
            print(f"   URL: {create_url}")
            
            test_doc = {
                "title": "测试文档",
                "content": "这是一个测试文档，用于验证知识库服务是否正常工作。",
                "category": "test",
                "tags": ["test", "sap_metadata"],
                "metadata": {"test": True},
                "process_async": False
            }
            
            try:
                response = await client.post(create_url, json=test_doc)
                print(f"   状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ 文档创建成功")
                    print(f"   文档ID: {result.get('document_id', 'unknown')}")
                    return True
                else:
                    print(f"   ⚠️  响应异常: {response.text}")
                    return False
            except httpx.ConnectError as e:
                print(f"   ❌ 连接失败: {e}")
                return False
            except httpx.TimeoutException:
                print(f"   ❌ 连接超时")
                return False
            except Exception as e:
                print(f"   ❌ 错误: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_kb_connection())
    exit(0 if success else 1)

