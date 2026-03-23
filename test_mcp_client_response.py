"""
测试MCPClient的响应解析
"""
import asyncio
import sys
import os

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test():
    # 设置正确的base_url（本地测试）
    os.environ["MCP_GATEWAY_URL"] = "http://localhost:8001"
    
    sys.path.insert(0, "agent-service")
    from src.services.mcp_client import MCPClient
    
    client = MCPClient()
    
    print(f"MCPClient base_url: {client.base_url}")
    print("\n测试 list_tools()...")
    
    try:
        tools = await client.list_tools()
        print(f"返回工具数量: {len(tools)}")
        
        if tools:
            print(f"第一个工具: {tools[0].get('name') if isinstance(tools[0], dict) else 'N/A'}")
            # 查找sap_query和send_email
            for tool in tools:
                tool_name = tool.get("name") if isinstance(tool, dict) else getattr(tool, "name", None)
                if tool_name in ["sap_query", "send_email"]:
                    print(f"[OK] 找到工具: {tool_name}")
        else:
            print("[ERROR] 工具列表为空")
            
            # 直接测试HTTP请求
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                print("\n直接测试HTTP请求...")
                response = await http_client.get(f"{client.base_url}/api/tools")
                print(f"HTTP状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"响应类型: {type(result)}")
                    print(f"响应键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                    if isinstance(result, dict) and "tools" in result:
                        print(f"工具数量: {len(result['tools'])}")
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test())

