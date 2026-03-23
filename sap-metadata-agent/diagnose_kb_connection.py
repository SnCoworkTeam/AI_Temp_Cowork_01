"""
诊断知识库服务连接问题
"""
import asyncio
import httpx
import os
import sys
from pathlib import Path

async def diagnose_connection():
    """诊断知识库服务连接"""
    print("=" * 80)
    print("知识库服务连接诊断")
    print("=" * 80)
    
    # 测试多个可能的URL
    possible_urls = [
        "http://localhost:8004",
        "http://127.0.0.1:8004",
        "http://knowledge-base:8004",
    ]
    
    # 从环境变量获取
    env_url = os.getenv("KNOWLEDGE_BASE_URL")
    if env_url:
        possible_urls.insert(0, env_url)
    
    print(f"\n环境变量 KNOWLEDGE_BASE_URL: {env_url or '未设置'}")
    print(f"\n将测试以下URL:")
    for i, url in enumerate(possible_urls, 1):
        print(f"  {i}. {url}")
    
    print("\n" + "-" * 80)
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for url in possible_urls:
            print(f"\n测试: {url}")
            print("-" * 80)
            
            # 测试根路径
            try:
                print(f"  1. 测试根路径: {url}/")
                response = await client.get(f"{url}/", timeout=5.0)
                print(f"     状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"     ✅ 根路径可访问")
                    print(f"     响应: {response.json()}")
                else:
                    print(f"     ⚠️  状态码异常: {response.text[:200]}")
            except httpx.ConnectError as e:
                print(f"     ❌ 连接失败: {e}")
                continue
            except httpx.TimeoutException:
                print(f"     ❌ 连接超时")
                continue
            except Exception as e:
                print(f"     ❌ 错误: {e}")
                continue
            
            # 测试健康检查
            try:
                print(f"\n  2. 测试健康检查: {url}/api/health")
                response = await client.get(f"{url}/api/health", timeout=5.0)
                print(f"     状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"     ✅ 健康检查成功")
                    health_data = response.json()
                    print(f"     服务状态: {health_data.get('status', 'unknown')}")
                else:
                    print(f"     ⚠️  状态码异常: {response.text[:200]}")
            except Exception as e:
                print(f"     ❌ 错误: {e}")
                continue
            
            # 测试创建文档端点
            try:
                print(f"\n  3. 测试创建文档端点: {url}/api/documents/create")
                test_doc = {
                    "title": "诊断测试文档",
                    "content": "这是一个诊断测试文档",
                    "category": "test",
                    "tags": ["test", "diagnosis"],
                    "metadata": {"test": True},
                    "process_async": False
                }
                response = await client.post(
                    f"{url}/api/documents/create",
                    json=test_doc,
                    timeout=30.0
                )
                print(f"     状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"     ✅ 文档创建成功")
                    print(f"     文档ID: {result.get('document_id', 'unknown')}")
                    print(f"\n✅✅✅ 找到可用的知识库服务: {url} ✅✅✅")
                    return url
                else:
                    print(f"     ⚠️  状态码异常: {response.text[:200]}")
            except httpx.HTTPStatusError as e:
                print(f"     ❌ HTTP错误: {e.response.status_code}")
                print(f"     响应内容: {e.response.text[:500]}")
            except httpx.ConnectError as e:
                print(f"     ❌ 连接失败: {e}")
            except httpx.TimeoutException:
                print(f"     ❌ 连接超时（可能服务正在处理，但响应太慢）")
            except Exception as e:
                print(f"     ❌ 错误: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("❌ 未找到可用的知识库服务")
    print("=" * 80)
    print("\n建议:")
    print("1. 确认知识库服务是否正在运行")
    print("2. 检查服务端口是否为8004")
    print("3. 检查防火墙设置")
    print("4. 如果使用Docker，检查容器是否运行: docker ps | grep knowledge")
    return None

if __name__ == "__main__":
    result = asyncio.run(diagnose_connection())
    if result:
        print(f"\n✅ 建议使用以下URL: {result}")
        print(f"   设置环境变量: export KNOWLEDGE_BASE_URL={result}")
        sys.exit(0)
    else:
        sys.exit(1)

