"""
直接测试配置中心API和agent-service的配置读取
"""
import asyncio
import httpx
import os
import sys

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_direct():
    """直接测试"""
    print("="*80)
    print("直接测试配置中心API和agent-service配置读取")
    print("="*80)
    
    config_center_url = "http://localhost:8090"
    
    # 测试1: 直接读取配置
    print(f"\n[测试1] 直接读取llm.api_key配置")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{config_center_url}/api/config/llm.api_key",
                params={"environment": "default"}
            )
            
            print(f"  HTTP状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  响应数据: {data}")
                api_key = data.get("value", "")
                if api_key:
                    print(f"  ✅ API key存在 (长度: {len(api_key)})")
                    print(f"     前10个字符: {api_key[:10]}...")
                else:
                    print("  ⚠️  API key为空")
            else:
                print(f"  ❌ 读取失败")
                print(f"     响应: {response.text[:500]}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2: 测试agent-service的LLM集成（使用环境变量作为fallback）
    print(f"\n[测试2] 测试agent-service的LLM集成")
    try:
        # 设置环境变量（从配置中心读取的值）
        if 'api_key' in locals() and api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            print(f"  已设置环境变量 OPENAI_API_KEY (长度: {len(api_key)})")
        
        os.environ["LLM_BASE_URL"] = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        os.environ["LLM_MODEL"] = os.getenv("LLM_MODEL", "deepseek-chat")
        os.environ["MCP_GATEWAY_URL"] = "http://localhost:8001"
        
        sys.path.insert(0, "agent-service")
        from src.core.llm_integration import deepseek_llm
        
        print(f"\n  初始状态:")
        print(f"  config_client: {deepseek_llm.config_client}")
        print(f"  api_key: {'已设置' if deepseek_llm.api_key else '未设置'} (长度: {len(deepseek_llm.api_key) if deepseek_llm.api_key else 0})")
        print(f"  base_url: {deepseek_llm.base_url or 'N/A'}")
        print(f"  model: {deepseek_llm.model or 'N/A'}")
        print(f"  llm: {'已初始化' if deepseek_llm.llm else '未初始化'}")
        
        # 尝试异步加载配置
        print(f"\n  执行异步加载配置...")
        await deepseek_llm._load_config_async()
        
        print(f"\n  加载后状态:")
        print(f"  config_client: {deepseek_llm.config_client}")
        print(f"  api_key: {'已设置' if deepseek_llm.api_key else '未设置'} (长度: {len(deepseek_llm.api_key) if deepseek_llm.api_key else 0})")
        print(f"  base_url: {deepseek_llm.base_url or 'N/A'}")
        print(f"  model: {deepseek_llm.model or 'N/A'}")
        print(f"  llm: {'已初始化' if deepseek_llm.llm else '未初始化'}")
        
        if deepseek_llm.llm:
            print("\n  ✅ LLM初始化成功！")
            
            # 测试3: 测试MCP工具智能体
            print(f"\n[测试3] 测试MCP工具智能体")
            from src.core.agents.mcp_tool_agent import MCPToolAgent
            
            agent = MCPToolAgent()
            print(f"  Agent MCP Gateway base_url: {agent.mcp_gateway.base_url}")
            
            task_description = "发送邮件给刘玉斌，yubin.liu@pcitc.com，主题是测试邮件"
            
            execution_plan = await agent.analyze_task(task_description, {})
            
            print(f"  需要工具: {execution_plan.get('needs_tool', False)}")
            print(f"  选择的工具: {execution_plan.get('selected_tool', 'N/A')}")
            
            if execution_plan.get('needs_tool'):
                print("  ✅ 分析成功，选择了工具")
                print(f"  参数: {execution_plan.get('optimized_parameters', {})}")
                return True
            else:
                print(f"  ⚠️  分析结果认为不需要工具: {execution_plan.get('reason', 'N/A')}")
                return False
        else:
            print("\n  ❌ LLM未初始化")
            return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_direct())
    if result:
        print("\n" + "="*80)
        print("✅ 所有测试通过！")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("⚠️  部分测试未通过，请检查错误信息")
        print("="*80)

