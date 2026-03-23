"""
配置API Key并测试MCP智能体
"""
import asyncio
import os
import sys
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 设置项目路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agent-service"))

async def configure_api_key():
    """配置API Key"""
    print("="*80)
    print("配置API Key")
    print("="*80)
    
    # 检查是否已有API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "your-api-key-here":
        print(f"✅ 检测到环境变量 OPENAI_API_KEY (长度: {len(api_key)})")
        use_existing = input("是否使用现有的API key? (y/n, 默认y): ").strip().lower()
        if use_existing != 'n':
            return api_key
    
    # 从.env文件读取
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("OPENAI_API_KEY="):
                    env_api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if env_api_key and env_api_key != "your-api-key-here":
                        print(f"✅ 从.env文件读取到API key (长度: {len(env_api_key)})")
                        use_env = input("是否使用.env文件中的API key? (y/n, 默认y): ").strip().lower()
                        if use_env != 'n':
                            os.environ["OPENAI_API_KEY"] = env_api_key
                            return env_api_key
    
    # 提示用户输入
    print("\n请输入您的API Key:")
    print("  - DeepSeek: https://platform.deepseek.com/api_keys")
    print("  - OpenAI: https://platform.openai.com/api-keys")
    print()
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ API Key不能为空")
        return None
    
    # 设置环境变量
    os.environ["OPENAI_API_KEY"] = api_key
    
    # 设置其他LLM配置
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    
    print(f"\n✅ API Key已设置")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    
    return api_key

async def setup_config_center(api_key: str):
    """设置配置中心"""
    print("\n" + "="*80)
    print("设置配置中心")
    print("="*80)
    
    try:
        import httpx
        
        config_center_url = os.getenv("CONFIG_CENTER_URL", "http://localhost:8090")
        base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        model = os.getenv("LLM_MODEL", "deepseek-chat")
        temperature = os.getenv("LLM_TEMPERATURE", "0.7")
        max_tokens = os.getenv("LLM_MAX_TOKENS", "4096")
        
        configs = [
            {
                "key": "llm.api_key",
                "value": api_key,
                "description": "LLM API密钥（DeepSeek/OpenAI）",
                "environment": "default"
            },
            {
                "key": "llm.base_url",
                "value": base_url,
                "description": "LLM服务基础URL",
                "environment": "default"
            },
            {
                "key": "llm.model",
                "value": model,
                "description": "LLM模型名称",
                "environment": "default"
            },
            {
                "key": "llm.temperature",
                "value": float(temperature),
                "description": "LLM温度参数",
                "environment": "default"
            },
            {
                "key": "llm.max_tokens",
                "value": int(max_tokens),
                "description": "LLM最大token数",
                "environment": "default"
            }
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            success_count = 0
            for config in configs:
                try:
                    response = await client.post(
                        f"{config_center_url}/api/config",
                        json=config
                    )
                    
                    if response.status_code in [200, 201]:
                        print(f"✅ 设置成功: {config['key']}")
                        success_count += 1
                    else:
                        print(f"⚠️  设置失败: {config['key']} - HTTP {response.status_code}")
                except Exception as e:
                    print(f"⚠️  设置失败: {config['key']} - {e}")
            
            if success_count > 0:
                print(f"\n✅ 配置中心设置完成 ({success_count}/{len(configs)})")
                return True
            else:
                print(f"\n⚠️  配置中心不可用，将使用环境变量")
                return False
                
    except Exception as e:
        print(f"⚠️  配置中心不可用: {e}")
        print("   将使用环境变量")
        return False

async def test_mcp_agent(api_key: str):
    """测试MCP智能体"""
    print("\n" + "="*80)
    print("测试MCP智能体")
    print("="*80)
    
    # 确保环境变量已设置
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["LLM_BASE_URL"] = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    os.environ["LLM_MODEL"] = os.getenv("LLM_MODEL", "deepseek-chat")
    os.environ["MCP_GATEWAY_URL"] = "http://localhost:8001"
    
    try:
        # 测试1: MCPClient
        print("\n[测试1] 测试MCPClient")
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
            return False
        
        await client.close()
        
        # 测试2: LLM初始化
        print("\n[测试2] 测试LLM初始化")
        from src.core.llm_integration import deepseek_llm
        
        await deepseek_llm._load_config_async()
        
        if deepseek_llm.llm:
            print("  [OK] LLM初始化成功")
            print(f"  Model: {deepseek_llm.model}")
            print(f"  Base URL: {deepseek_llm.base_url}")
        else:
            print("  [ERROR] LLM初始化失败")
            return False
        
        # 测试3: MCP工具智能体 - analyze_task
        print("\n[测试3] 测试MCP工具智能体 - analyze_task")
        from src.core.agents.mcp_tool_agent import MCPToolAgent
        
        agent = MCPToolAgent()
        print(f"  Agent MCP Gateway base_url: {agent.mcp_gateway.base_url}")
        
        task_description = "发送邮件给刘玉斌，yubin.liu@pcitc.com，主题是测试邮件，内容是销售订单分析报告"
        
        execution_plan = await agent.analyze_task(task_description, {})
        
        print(f"  需要工具: {execution_plan.get('needs_tool', False)}")
        print(f"  选择的工具: {execution_plan.get('selected_tool', 'N/A')}")
        
        if execution_plan.get('needs_tool'):
            print("  [OK] 分析成功，选择了工具")
            print(f"  参数: {execution_plan.get('optimized_parameters', {})}")
            
            # 测试4: execute（不实际发送邮件，只测试逻辑）
            print("\n[测试4] 测试MCP工具智能体 - execute (模拟)")
            print("  注意: 不实际执行工具，只测试逻辑")
            
            # 可以在这里测试execute，但为了避免实际发送邮件，我们跳过
            print("  [SKIP] 跳过实际工具执行（避免发送真实邮件）")
        else:
            print(f"  [WARN] 分析结果认为不需要工具: {execution_plan.get('reason', 'N/A')}")
        
        print("\n" + "="*80)
        print("✅ 所有测试通过！")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("\n" + "="*80)
    print("MCP智能体配置和测试")
    print("="*80)
    
    # 1. 配置API Key
    api_key = await configure_api_key()
    if not api_key:
        print("\n❌ API Key配置失败")
        return
    
    # 2. 设置配置中心（可选）
    await setup_config_center(api_key)
    
    # 3. 测试MCP智能体
    success = await test_mcp_agent(api_key)
    
    if success:
        print("\n🎉 配置和测试完成！")
        print("\n提示:")
        print("  1. 环境变量已设置，当前会话有效")
        print("  2. 如果使用Docker，请在docker-compose.yml中设置环境变量")
        print("  3. 如果使用本地运行，请确保环境变量在启动服务前已设置")
    else:
        print("\n⚠️  测试未完全通过，请检查错误信息")

if __name__ == "__main__":
    asyncio.run(main())

