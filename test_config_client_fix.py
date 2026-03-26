"""
测试config_client修复
"""
import asyncio
import os
import sys

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_config_client():
    """测试config_client"""
    print("="*80)
    print("测试config_client修复")
    print("="*80)
    
    # 设置环境变量
    os.environ["CONFIG_CENTER_URL"] = "http://localhost:8090"
    os.environ["MCP_GATEWAY_URL"] = "http://localhost:8001"
    
    # 测试1: 测试ConfigClient初始化
    print("\n[测试1] 测试ConfigClient初始化")
    try:
        sys.path.insert(0, "shared_libs")
        from luminaos_common.clients.config_client import ConfigClient, get_config_client
        
        # 测试直接初始化
        client1 = ConfigClient()
        print(f"  ✅ ConfigClient直接初始化成功")
        print(f"     base_url: {client1.config_center_url}")
        
        # 测试get_config_client
        client2 = get_config_client()
        print(f"  ✅ get_config_client()成功")
        print(f"     base_url: {client2.config_center_url}")
        
        # 测试读取配置
        api_key = await client2.get_config("llm.api_key", "default")
        if api_key:
            print(f"  ✅ 成功读取llm.api_key (长度: {len(api_key)})")
        else:
            print("  ⚠️  llm.api_key为空或不存在")
        
        await client2.close()
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试2: 测试agent-service的LLM集成
    print("\n[测试2] 测试agent-service的LLM集成")
    try:
        sys.path.insert(0, "agent-service")
        from src.core.llm_integration import deepseek_llm
        
        print(f"  config_client: {deepseek_llm.config_client}")
        print(f"  config_center_url: {deepseek_llm.config_client.config_center_url if deepseek_llm.config_client else 'N/A'}")
        
        # 重新初始化（强制重新创建）
        if deepseek_llm.config_client:
            print("  ✅ config_client已初始化")
        else:
            print("  ⚠️  config_client未初始化，将使用HTTP fallback")
        
        # 异步加载配置
        await deepseek_llm._load_config_async()
        
        print(f"\n  加载后状态:")
        print(f"  api_key: {'已设置' if deepseek_llm.api_key else '未设置'} (长度: {len(deepseek_llm.api_key) if deepseek_llm.api_key else 0})")
        print(f"  base_url: {deepseek_llm.base_url or 'N/A'}")
        print(f"  model: {deepseek_llm.model or 'N/A'}")
        print(f"  llm: {'已初始化' if deepseek_llm.llm else '未初始化'}")
        
        if deepseek_llm.api_key:
            print("  ✅ API key已从配置中心读取")
            return True
        else:
            print("  ❌ API key未读取")
            return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_config_client())
    if result:
        print("\n" + "="*80)
        print("✅ config_client修复成功！")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("⚠️  部分测试未通过，请检查错误信息")
        print("="*80)

