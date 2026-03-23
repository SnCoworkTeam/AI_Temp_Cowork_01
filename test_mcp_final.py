"""
最终测试MCP智能体（使用配置中心的API key）
"""
import asyncio
import httpx
import os
import sys

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_final():
    """最终测试"""
    print("="*80)
    print("最终测试MCP智能体")
    print("="*80)
    
    # 步骤1: 从配置中心读取API key并设置环境变量
    print("\n[步骤1] 从配置中心读取API key")
    config_center_url = "http://localhost:8090"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{config_center_url}/api/config/llm.api_key",
                params={"environment": "default"}
            )
            
            if response.status_code == 200:
                data = response.json()
                api_key = data.get("value", "")
                if api_key:
                    os.environ["OPENAI_API_KEY"] = api_key
                    print(f"  ✅ 从配置中心读取API key成功 (长度: {len(api_key)})")
                else:
                    print("  ❌ API key为空")
                    return False
            else:
                print(f"  ❌ 读取失败: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"  ❌ 读取配置失败: {e}")
        return False
    
    # 设置其他环境变量
    os.environ["LLM_BASE_URL"] = "https://api.deepseek.com"
    os.environ["LLM_MODEL"] = "deepseek-chat"
    os.environ["MCP_GATEWAY_URL"] = "http://localhost:8001"
    
    # 步骤2: 测试LLM初始化
    print("\n[步骤2] 测试LLM初始化")
    try:
        sys.path.insert(0, "agent-service")
        from src.core.llm_integration import deepseek_llm
        
        # 重新初始化（强制从环境变量加载）
        deepseek_llm._load_config_from_env()
        
        print(f"  api_key: {'已设置' if deepseek_llm.api_key else '未设置'} (长度: {len(deepseek_llm.api_key) if deepseek_llm.api_key else 0})")
        print(f"  base_url: {deepseek_llm.base_url or 'N/A'}")
        print(f"  model: {deepseek_llm.model or 'N/A'}")
        print(f"  llm: {'已初始化' if deepseek_llm.llm else '未初始化'}")
        
        if not deepseek_llm.llm:
            print("  ⚠️  LLM未初始化，尝试手动初始化...")
            deepseek_llm._init_llm()
        
        if deepseek_llm.llm:
            print("  ✅ LLM初始化成功")
        else:
            print("  ❌ LLM初始化失败")
            return False
    except Exception as e:
        print(f"  ❌ LLM初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤3: 测试MCP工具智能体
    print("\n[步骤3] 测试MCP工具智能体")
    try:
        from src.core.agents.mcp_tool_agent import MCPToolAgent
        
        agent = MCPToolAgent()
        print(f"  Agent MCP Gateway base_url: {agent.mcp_gateway.base_url}")
        
        # 测试analyze_task
        task_description = "发送邮件给刘玉斌，yubin.liu@pcitc.com，主题是销售订单分析报告"
        print(f"\n  测试任务: {task_description}")
        
        execution_plan = await agent.analyze_task(task_description, {})
        
        print(f"  需要工具: {execution_plan.get('needs_tool', False)}")
        print(f"  选择的工具: {execution_plan.get('selected_tool', 'N/A')}")
        print(f"  原因: {execution_plan.get('reason', 'N/A')}")
        
        if execution_plan.get('needs_tool'):
            print("  ✅ 分析成功，选择了工具")
            print(f"  参数: {execution_plan.get('optimized_parameters', {})}")
            return True
        else:
            print(f"  ⚠️  分析结果认为不需要工具")
            return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_final())
    if result:
        print("\n" + "="*80)
        print("✅ 所有测试通过！MCP智能体可以正常使用！")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("⚠️  部分测试未通过，请检查错误信息")
        print("="*80)

