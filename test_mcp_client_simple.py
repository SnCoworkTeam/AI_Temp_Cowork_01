"""
简单测试MCP Client的list_tools方法
"""
import asyncio
import sys
import os

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test():
    sys.path.insert(0, "agent-service")
    from src.services.mcp_client import MCPClient
    
    client = MCPClient()
    
    print("测试MCP Client list_tools()...")
    tools = await client.list_tools()
    
    print(f"返回工具数量: {len(tools)}")
    print(f"工具类型: {type(tools)}")
    
    if tools:
        print(f"第一个工具: {tools[0]}")
        print(f"第一个工具类型: {type(tools[0])}")
        print(f"第一个工具的键: {list(tools[0].keys()) if isinstance(tools[0], dict) else 'N/A'}")
        
        # 查找sap_query和send_email
        for tool in tools:
            tool_name = tool.get("name") if isinstance(tool, dict) else getattr(tool, "name", None)
            if tool_name in ["sap_query", "send_email"]:
                print(f"找到工具: {tool_name}")
    else:
        print("工具列表为空")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test())

