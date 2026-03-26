"""
API使用示例 - Python
"""
import httpx
import asyncio


# 基础配置
BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "your-auth-token"


def example_get_tools():
    """示例: 获取工具列表"""
    with httpx.Client() as client:
        response = client.get(
            f"{BASE_URL}/api/tools",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )
        print(response.json())


async def example_execute_tool():
    """示例: 执行工具"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/tools/test_tool/execute",
            json={"parameters": {"input": "test"}},
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )
        print(response.json())


def example_create_workflow():
    """示例: 创建工作流"""
    with httpx.Client() as client:
        response = client.post(
            "http://localhost:8001/api/workflows",
            json={
                "name": "example_workflow",
                "description": "Example workflow",
                "config": {
                    "nodes": [],
                    "connections": []
                }
            },
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
        )
        print(response.json())


def example_login():
    """示例: 用户登录"""
    with httpx.Client() as client:
        response = client.post(
            "http://localhost:8002/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass"
            }
        )
        data = response.json()
        token = data.get("access_token")
        print(f"Access Token: {token}")
        return token


if __name__ == "__main__":
    # 同步示例
    example_get_tools()
    
    # 异步示例
    asyncio.run(example_execute_tool())









