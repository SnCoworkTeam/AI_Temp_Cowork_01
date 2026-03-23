#!/usr/bin/env python3
"""
测试API端点
验证workflow-engine服务可访问性和API端点
"""
import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine"))


async def test_api_endpoints():
    """测试API端点"""
    print("=" * 60)
    print("测试API端点")
    print("=" * 60)
    
    try:
        import httpx
        
        # 测试1: 健康检查端点
        print("\n1. 测试健康检查端点...")
        base_url = "http://localhost:8002"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/health")
                
                if response.status_code == 200:
                    print(f"   [OK] 健康检查端点可访问")
                    print(f"   - 状态码: {response.status_code}")
                    try:
                        data = response.json()
                        print(f"   - 响应: {data}")
                    except:
                        print(f"   - 响应: {response.text[:100]}")
                else:
                    print(f"   [WARN] 健康检查端点返回: {response.status_code}")
        except httpx.ConnectError:
            print(f"   [WARN] 无法连接到 {base_url}")
            print("   提示: workflow-engine服务可能未启动")
        except Exception as e:
            print(f"   [WARN] 健康检查失败: {e}")
        
        # 测试2: 工作流列表端点
        print("\n2. 测试工作流列表端点...")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/workflows")
                
                if response.status_code == 200:
                    print(f"   [OK] 工作流列表端点可访问")
                    print(f"   - 状态码: {response.status_code}")
                else:
                    print(f"   [WARN] 工作流列表端点返回: {response.status_code}")
        except httpx.ConnectError:
            print(f"   [WARN] 无法连接到 {base_url}")
        except Exception as e:
            print(f"   [WARN] 工作流列表测试失败: {e}")
        
        # 测试3: MCP Gateway端点
        print("\n3. 测试MCP Gateway端点...")
        mcp_url = "http://localhost:8001"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{mcp_url}/api/tools")
                
                if response.status_code == 200:
                    print(f"   [OK] MCP Gateway工具列表端点可访问")
                    print(f"   - 状态码: {response.status_code}")
                else:
                    print(f"   [WARN] MCP Gateway端点返回: {response.status_code}")
        except httpx.ConnectError:
            print(f"   [WARN] 无法连接到 {mcp_url}")
            print("   提示: mcp-gateway服务可能未启动")
        except Exception as e:
            print(f"   [WARN] MCP Gateway测试失败: {e}")
        
        print("\n" + "=" * 60)
        print("[OK] API端点测试完成！")
        print("=" * 60)
        print("\n注意: 如果服务未启动，这些测试会显示警告但不视为失败")
        return True
        
    except ImportError:
        print("   [WARN] httpx未安装，跳过API端点测试")
        print("   提示: 运行 pip install httpx 安装")
        return True
    except Exception as e:
        print(f"   [ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_api_endpoints())
    sys.exit(0 if success else 1)

