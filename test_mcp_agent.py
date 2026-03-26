"""
测试MCP工具智能体
验证是否能正常列出工具和执行工具
"""
import asyncio
import sys
import os
from pathlib import Path

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agent-service"))
sys.path.insert(0, str(project_root / "shared_libs"))

async def test_mcp_gateway_direct():
    """直接测试MCP Gateway API"""
    print("="*80)
    print("测试1: 直接调用MCP Gateway API")
    print("="*80)
    
    import httpx
    
    mcp_gateway_url = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试列出工具
            print(f"\n1. 测试列出工具: GET {mcp_gateway_url}/api/tools")
            response = await client.get(f"{mcp_gateway_url}/api/tools")
            
            if response.status_code == 200:
                tools = response.json()
                
                # 处理不同的响应格式
                if isinstance(tools, dict):
                    if "tools" in tools:
                        tools = tools["tools"]
                    elif "items" in tools:
                        tools = tools["items"]
                    else:
                        tools = []
                
                print(f"   [OK] 成功获取工具列表，共 {len(tools)} 个工具")
                
                # 查找sap_query和send_email
                sap_query_found = False
                send_email_found = False
                
                for tool in tools:
                    tool_name = tool.get("name", "")
                    if tool_name == "sap_query":
                        sap_query_found = True
                        print(f"   [OK] 找到 sap_query 工具")
                        print(f"      状态: {tool.get('status', 'unknown')}")
                    elif tool_name == "send_email":
                        send_email_found = True
                        print(f"   [OK] 找到 send_email 工具")
                        print(f"      状态: {tool.get('status', 'unknown')}")
                
                if not sap_query_found:
                    print(f"   [ERROR] 未找到 sap_query 工具")
                if not send_email_found:
                    print(f"   [ERROR] 未找到 send_email 工具")
                
                return tools
            else:
                print(f"   [ERROR] 获取工具列表失败: HTTP {response.status_code}")
                print(f"      响应: {response.text[:200]}")
                return None
                
    except httpx.ConnectError:
        print(f"   [ERROR] 无法连接到MCP Gateway ({mcp_gateway_url})")
        print("      请确保MCP Gateway服务正在运行")
        return None
    except Exception as e:
        print(f"   [ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_mcp_client():
    """测试MCP Client"""
    print("\n" + "="*80)
    print("测试2: 通过MCP Client测试")
    print("="*80)
    
    try:
        sys.path.insert(0, str(project_root / "agent-service"))
        from src.services.mcp_client import MCPClient
        
        client = MCPClient()
        
        # 测试列出工具
        print("\n1. 测试 list_tools()")
        tools = await client.list_tools()
        
        if tools:
            print(f"   [OK] 成功获取工具列表，共 {len(tools)} 个工具")
            
            # 查找sap_query和send_email
            for tool in tools:
                tool_name = tool.get("name", "")
                if tool_name in ["sap_query", "send_email"]:
                    print(f"   [OK] 找到 {tool_name} 工具")
        else:
            print(f"   [ERROR] 工具列表为空")
        
        await client.close()
        return tools
        
    except Exception as e:
        print(f"   [ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_mcp_tool_agent():
    """测试MCP工具智能体"""
    print("\n" + "="*80)
    print("测试3: 测试MCP工具智能体")
    print("="*80)
    
    try:
        sys.path.insert(0, str(project_root / "agent-service"))
        from src.core.agents.mcp_tool_agent import MCPToolAgent
        
        agent = MCPToolAgent()
        
        # 测试analyze_task
        print("\n1. 测试 analyze_task() - 分析邮件发送任务")
        task_description = "发送邮件给刘玉斌，yubin.liu@pcitc.com，主题是测试邮件"
        
        try:
            execution_plan = await agent.analyze_task(task_description, {})
            
            if execution_plan:
                print(f"   [OK] 分析成功")
                print(f"      需要工具: {execution_plan.get('needs_tool', False)}")
                print(f"      选择的工具: {execution_plan.get('selected_tool', 'N/A')}")
                print(f"      参数: {execution_plan.get('optimized_parameters', {})}")
                
                if not execution_plan.get('needs_tool'):
                    print(f"   [WARN] 分析结果认为不需要工具")
                    print(f"      原因: {execution_plan.get('reason', 'N/A')}")
            else:
                print(f"   [ERROR] 分析失败：返回None")
        except Exception as e:
            print(f"   [ERROR] 分析失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试execute - 发送邮件
        print("\n2. 测试 execute() - 执行邮件发送")
        try:
            result = await agent.execute({
                "task": "发送邮件给刘玉斌，yubin.liu@pcitc.com",
                "execution_plan": {
                    "needs_tool": True,
                    "selected_tool": "send_email",
                    "optimized_parameters": {
                        "to_emails": "yubin.liu@pcitc.com",
                        "subject": "测试邮件",
                        "body": "这是一封测试邮件"
                    }
                }
            }, {})
            
            if result:
                print(f"   [OK] 执行完成")
                print(f"      工具: {result.get('tool_executed', 'N/A')}")
                print(f"      成功: {result.get('execution_success', False)}")
                
                if result.get('execution_success'):
                    print(f"      结果: {str(result.get('raw_result', {}))[:200]}...")
                else:
                    print(f"      错误: {result.get('error', 'N/A')}")
            else:
                print(f"   [ERROR] 执行失败：返回None")
        except Exception as e:
            print(f"   [ERROR] 执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试execute - SAP查询
        print("\n3. 测试 execute() - 执行SAP查询")
        try:
            result = await agent.execute({
                "task": "查询销售订单数据",
                "execution_plan": {
                    "needs_tool": True,
                    "selected_tool": "sap_query",
                    "optimized_parameters": {
                        "table": "I_SalesOrder",
                        "$top": 10
                    }
                }
            }, {})
            
            if result:
                print(f"   [OK] 执行完成")
                print(f"      工具: {result.get('tool_executed', 'N/A')}")
                print(f"      成功: {result.get('execution_success', False)}")
                
                if result.get('execution_success'):
                    raw_result = result.get('raw_result', {})
                    if isinstance(raw_result, dict):
                        print(f"      结果类型: dict")
                        print(f"      结果键: {list(raw_result.keys())[:5]}")
                    elif isinstance(raw_result, list):
                        print(f"      结果类型: list, 长度: {len(raw_result)}")
                    else:
                        print(f"      结果: {str(raw_result)[:200]}...")
                else:
                    print(f"      错误: {result.get('error', 'N/A')}")
            else:
                print(f"   [ERROR] 执行失败：返回None")
        except Exception as e:
            print(f"   [ERROR] 执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("MCP工具智能体测试")
    print("="*80)
    
    # 测试1: 直接调用MCP Gateway API
    tools = await test_mcp_gateway_direct()
    
    # 测试2: 通过MCP Client
    if tools:
        await test_mcp_client()
    
    # 测试3: 测试MCP工具智能体
    await test_mcp_tool_agent()
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())

