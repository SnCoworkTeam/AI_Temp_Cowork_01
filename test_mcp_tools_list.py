"""
测试MCP工具列表获取
"""
import asyncio
import sys
import os

sys.path.insert(0, "agent-service")
os.environ["MCP_GATEWAY_URL"] = "http://localhost:8001"

async def test():
    from src.services.mcp_client import MCPClient
    
    client = MCPClient()
    tools = await client.list_tools()
    
    print("="*80)
    print("MCP工具列表")
    print("="*80)
    print(f"工具数量: {len(tools)}")
    print()
    
    for tool in tools:
        print(f"工具名称: {tool.get('name')}")
        print(f"  描述: {tool.get('description', 'N/A')[:100]}")
        print(f"  状态: {tool.get('status', 'N/A')}")
        print()
    
    # 检查send_email工具
    send_email = next((t for t in tools if t.get("name") == "send_email"), None)
    if send_email:
        print("✅ send_email工具存在")
        print(f"   参数: {send_email.get('parameters', {})}")
    else:
        print("❌ send_email工具不存在")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test())

