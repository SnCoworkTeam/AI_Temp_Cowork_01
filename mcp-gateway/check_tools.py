"""
检查MCP Gateway中注册的工具
验证sap_query和send_email工具是否已注册
"""
import asyncio
import httpx
import json
import sys

async def check_tools():
    """检查工具注册情况"""
    base_url = "http://localhost:8001"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 获取工具列表
            response = await client.get(f"{base_url}/api/tools")
            
            if response.status_code != 200:
                print(f"❌ 获取工具列表失败: HTTP {response.status_code}")
                print(f"响应: {response.text}")
                return False
            
            tools = response.json()
            
            # 如果是字典格式，提取工具列表
            if isinstance(tools, dict):
                if "tools" in tools:
                    tools = tools["tools"]
                elif "items" in tools:
                    tools = tools["items"]
                else:
                    print(f"⚠️  未知的响应格式: {list(tools.keys())}")
                    tools = []
            
            print(f"\n✅ 找到 {len(tools)} 个已注册的工具\n")
            
            # 检查sap_query
            sap_query_found = False
            send_email_found = False
            
            for tool in tools:
                tool_name = tool.get("name", "")
                tool_status = tool.get("status", "unknown")
                
                if tool_name == "sap_query":
                    sap_query_found = True
                    print(f"✅ sap_query 工具已注册")
                    print(f"   状态: {tool_status}")
                    print(f"   描述: {tool.get('description', 'N/A')}")
                    print(f"   版本: {tool.get('version', 'N/A')}")
                    
                elif tool_name == "send_email":
                    send_email_found = True
                    print(f"✅ send_email 工具已注册")
                    print(f"   状态: {tool_status}")
                    print(f"   描述: {tool.get('description', 'N/A')}")
                    print(f"   版本: {tool.get('version', 'N/A')}")
            
            print("\n" + "="*60)
            
            if not sap_query_found:
                print("❌ sap_query 工具未找到")
            if not send_email_found:
                print("❌ send_email 工具未找到")
            
            if sap_query_found and send_email_found:
                print("\n✅ 所有必需的工具都已注册！")
                return True
            else:
                print("\n⚠️  部分工具缺失，请检查服务启动日志")
                return False
                
    except httpx.ConnectError:
        print(f"❌ 无法连接到 MCP Gateway ({base_url})")
        print("   请确保 MCP Gateway 服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 检查工具时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(check_tools())
    sys.exit(0 if success else 1)

