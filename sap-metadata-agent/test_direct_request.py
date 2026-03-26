"""
直接测试HTTP请求到知识库服务
不经过任何封装，直接发送请求
"""
import asyncio
import httpx
import os
import json
from datetime import datetime

async def test_direct_request():
    """直接测试HTTP请求"""
    print("=" * 80)
    print("直接HTTP请求测试")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 测试多个URL
    test_urls = [
        "http://localhost:8004",
        "http://127.0.0.1:8004",
        "http://knowledge-base:8004",
    ]
    
    # 从环境变量获取
    env_url = os.getenv("KNOWLEDGE_BASE_URL")
    if env_url:
        test_urls.insert(0, env_url)
    
    print(f"环境变量 KNOWLEDGE_BASE_URL: {env_url or '未设置'}\n")
    
    test_doc = {
        "title": "直接测试文档",
        "content": "这是一个直接测试文档，用于验证HTTP请求是否能到达知识库服务。",
        "category": "test",
        "tags": ["test", "direct"],
        "metadata": {"test": True, "source": "direct_test"},
        "process_async": False
    }
    
    for url in test_urls:
        print(f"\n{'=' * 80}")
        print(f"测试URL: {url}")
        print(f"{'=' * 80}\n")
        
        create_url = f"{url}/api/documents/create"
        
        try:
            print(f"1. 测试连接...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 先测试健康检查
                health_url = f"{url}/api/health"
                print(f"   健康检查: {health_url}")
                try:
                    health_response = await client.get(health_url)
                    print(f"   ✅ 健康检查成功: status={health_response.status_code}")
                except Exception as e:
                    print(f"   ❌ 健康检查失败: {e}")
                    continue
                
                print(f"\n2. 发送POST请求到: {create_url}")
                print(f"   请求数据:")
                print(f"     title: {test_doc['title']}")
                print(f"     content_length: {len(test_doc['content'])}")
                print(f"     tags: {test_doc['tags']}")
                
                # 发送请求
                print(f"\n   正在发送请求...")
                response = await client.post(
                    create_url,
                    json=test_doc,
                    timeout=60.0
                )
                
                print(f"\n3. 收到响应:")
                print(f"   状态码: {response.status_code}")
                print(f"   响应头: {dict(response.headers)}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ 请求成功！")
                    print(f"   文档ID: {result.get('document_id', 'unknown')}")
                    print(f"   状态: {result.get('status', 'unknown')}")
                    print(f"\n✅✅✅ 找到可用的知识库服务: {url} ✅✅✅")
                    print(f"\n请检查知识库服务日志，应该能看到这个请求的记录")
                    return True
                else:
                    print(f"   ⚠️  状态码异常: {response.status_code}")
                    print(f"   响应内容: {response.text[:500]}")
                    
        except httpx.ConnectError as e:
            print(f"   ❌ 连接错误: {e}")
            print(f"   无法连接到 {url}")
            continue
        except httpx.TimeoutException:
            print(f"   ❌ 请求超时")
            print(f"   服务可能正在处理，但响应太慢")
            continue
        except httpx.HTTPStatusError as e:
            print(f"   ❌ HTTP错误: {e.response.status_code}")
            print(f"   响应内容: {e.response.text[:500]}")
            # 即使有HTTP错误，也说明请求到达了服务
            print(f"   ⚠️  但请求确实到达了服务（有响应）")
            continue
        except Exception as e:
            print(f"   ❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'=' * 80}")
    print("❌ 所有URL测试都失败")
    print(f"{'=' * 80}")
    return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_request())
    exit(0 if success else 1)

