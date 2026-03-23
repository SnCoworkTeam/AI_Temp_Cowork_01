"""
直接测试config_client，不依赖luminaos_common的其他模块
"""
import asyncio
import os
import sys

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_direct_import():
    """直接导入config_client，不通过luminaos_common"""
    print("="*80)
    print("直接测试config_client（绕过luminaos_common导入问题）")
    print("="*80)
    
    # 设置环境变量
    os.environ["CONFIG_CENTER_URL"] = "http://localhost:8090"
    
    # 方法1: 直接导入config_client模块（不通过__init__.py）
    print("\n[方法1] 直接导入config_client模块")
    try:
        import importlib.util
        config_client_path = "shared_libs/luminaos_common/clients/config_client.py"
        spec = importlib.util.spec_from_file_location("config_client", config_client_path)
        config_client_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_client_module)
        
        ConfigClient = config_client_module.ConfigClient
        get_config_client = config_client_module.get_config_client
        
        print("  ✅ 直接导入成功")
        
        # 测试初始化
        client = ConfigClient()
        print(f"  ✅ ConfigClient初始化成功")
        print(f"     base_url: {client.config_center_url}")
        
        # 测试读取配置
        api_key = await client.get_config("llm.api_key", "default")
        if api_key:
            print(f"  ✅ 成功读取llm.api_key (长度: {len(api_key)})")
        else:
            print("  ⚠️  llm.api_key为空或不存在")
        
        await client.close()
        return True
    except Exception as e:
        print(f"  ❌ 直接导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_service_with_direct_import():
    """修改agent-service使用直接导入的config_client"""
    print("\n" + "="*80)
    print("测试agent-service使用直接导入的config_client")
    print("="*80)
    
    # 设置环境变量
    os.environ["CONFIG_CENTER_URL"] = "http://localhost:8090"
    os.environ["MCP_GATEWAY_URL"] = "http://localhost:8001"
    
    try:
        sys.path.insert(0, "agent-service")
        
        # 在导入llm_integration之前，先直接导入config_client并注入
        import importlib.util
        config_client_path = "shared_libs/luminaos_common/clients/config_client.py"
        spec = importlib.util.spec_from_file_location("config_client", config_client_path)
        config_client_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_client_module)
        
        # 将get_config_client注入到sys.modules，让llm_integration可以导入
        sys.modules['luminaos_common.clients.config_client'] = config_client_module
        
        from src.core.llm_integration import deepseek_llm
        
        print(f"\n  初始状态:")
        print(f"  config_client: {deepseek_llm.config_client}")
        if deepseek_llm.config_client:
            print(f"  config_center_url: {deepseek_llm.config_client.config_center_url}")
        
        # 异步加载配置
        await deepseek_llm._load_config_async()
        
        print(f"\n  加载后状态:")
        print(f"  config_client: {deepseek_llm.config_client}")
        if deepseek_llm.config_client:
            print(f"  config_center_url: {deepseek_llm.config_client.config_center_url}")
        print(f"  api_key: {'已设置' if deepseek_llm.api_key else '未设置'} (长度: {len(deepseek_llm.api_key) if deepseek_llm.api_key else 0})")
        print(f"  base_url: {deepseek_llm.base_url or 'N/A'}")
        print(f"  model: {deepseek_llm.model or 'N/A'}")
        
        if deepseek_llm.api_key:
            print("\n  ✅ API key已从配置中心读取（通过config_client）")
            return True
        else:
            print("\n  ❌ API key未读取")
            return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result1 = asyncio.run(test_direct_import())
    result2 = asyncio.run(test_agent_service_with_direct_import())
    
    if result1 and result2:
        print("\n" + "="*80)
        print("✅ config_client可以正常使用！")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("⚠️  部分测试未通过")
        print("="*80)

