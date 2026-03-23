"""
最终测试MCP工具智能体
验证是否能正常列出工具和执行工具
"""
import asyncio
import sys
import os

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 设置正确的base_url（本地测试）
os.environ["MCP_GATEWAY_URL"] = "http://localhost:8001"

async def test():
    sys.path.insert(0, "agent-service")
    
    print("="*80)
    print("测试MCP工具智能体")
    print("="*80)
    
    # 测试1: 直接测试MCPClient
    print("\n[测试1] 测试MCPClient")
    try:
        from src.services.mcp_client import MCPClient
        
        client = MCPClient()
        print(f"  MCPClient base_url: {client.base_url}")
        
        tools = await client.list_tools()
        print(f"  工具数量: {len(tools)}")
        
        if tools:
            sap_found = any(t.get("name") == "sap_query" for t in tools)
            email_found = any(t.get("name") == "send_email" for t in tools)
            print(f"  sap_query: {'[OK]' if sap_found else '[ERROR]'}")
            print(f"  send_email: {'[OK]' if email_found else '[ERROR]'}")
        else:
            print("  [ERROR] 工具列表为空")
        
        await client.close()
    except Exception as e:
        print(f"  [ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2: 测试MCP工具智能体
    print("\n[测试2] 测试MCP工具智能体")
    try:
        from src.core.agents.mcp_tool_agent import MCPToolAgent
        
        agent = MCPToolAgent()
        print(f"  Agent MCP Gateway base_url: {agent.mcp_gateway.base_url}")
        
        # 测试analyze_task
        print("\n  测试 analyze_task - 邮件发送任务")
        execution_plan = await agent.analyze_task(
            "发送邮件给刘玉斌，yubin.liu@pcitc.com，主题是测试邮件",
            {}
        )
        
        print(f"    需要工具: {execution_plan.get('needs_tool', False)}")
        print(f"    选择的工具: {execution_plan.get('selected_tool', 'N/A')}")
        
        if execution_plan.get('needs_tool'):
            print("    [OK] 分析成功，选择了工具")
        else:
            print(f"    [WARN] 分析结果认为不需要工具: {execution_plan.get('reason', 'N/A')}")
        
        # 测试execute（如果选择了工具）
        if execution_plan.get('needs_tool') and execution_plan.get('selected_tool'):
            print(f"\n  测试 execute - 执行 {execution_plan.get('selected_tool')}")
            result = await agent.execute({
                "task": "发送邮件给刘玉斌，yubin.liu@pcitc.com",
                "execution_plan": execution_plan
            }, {})
            
            print(f"    执行成功: {result.get('execution_success', False)}")
            if result.get('execution_success'):
                print("    [OK] 工具执行成功")
            else:
                print(f"    [ERROR] 工具执行失败: {result.get('error', 'N/A')}")
        
    except Exception as e:
        print(f"  [ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试3: 测试service_clients
    print("\n[测试3] 测试service_clients")
    try:
        from src.core.service_clients import service_clients
        
        mcp_client = service_clients.mcp_gateway
        print(f"  Service Clients MCP Gateway base_url: {mcp_client.base_url}")
        
        tools = await mcp_client.list_tools()
        print(f"  工具数量: {len(tools)}")
        
        if tools:
            print("  [OK] service_clients可以正常获取工具列表")
        else:
            print("  [ERROR] service_clients无法获取工具列表")
    except Exception as e:
        print(f"  [ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test())

