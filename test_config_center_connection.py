"""
测试配置中心连接和API key读取
"""
import asyncio
import httpx
import os
import sys

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_config_center():
    """测试配置中心"""
    print("="*80)
    print("测试配置中心连接和API key读取")
    print("="*80)
    
    config_center_url = os.getenv("CONFIG_CENTER_URL", "http://localhost:8090")
    
    # 测试1: 检查配置中心是否可用
    print(f"\n[测试1] 检查配置中心是否可用: {config_center_url}")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config_center_url}/api/health")
            if response.status_code == 200:
                print("  ✅ 配置中心可用")
            else:
                print(f"  ❌ 配置中心返回错误: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"  ❌ 无法连接到配置中心: {e}")
        return False
    
    # 测试2: 读取llm.api_key配置
    print(f"\n[测试2] 读取llm.api_key配置")
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
                    print(f"  ✅ 成功读取API key (长度: {len(api_key)})")
                    print(f"     前10个字符: {api_key[:10]}...")
                else:
                    print("  ⚠️  API key为空")
                    return False
            else:
                print(f"  ❌ 读取失败: HTTP {response.status_code}")
                print(f"     响应: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"  ❌ 读取配置失败: {e}")
        return False
    
    # 测试3: 读取所有LLM配置
    print(f"\n[测试3] 读取所有LLM配置")
    configs = ["llm.api_key", "llm.base_url", "llm.model", "llm.temperature", "llm.max_tokens"]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for config_key in configs:
                response = await client.get(
                    f"{config_center_url}/api/config/{config_key}",
                    params={"environment": "default"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    value = data.get("value", "")
                    print(f"  ✅ {config_key}: {str(value)[:50]}")
                else:
                    print(f"  ⚠️  {config_key}: 读取失败 (HTTP {response.status_code})")
    except Exception as e:
        print(f"  ❌ 读取配置失败: {e}")
        return False
    
    # 测试4: 测试config_client
    print(f"\n[测试4] 测试config_client")
    try:
        sys.path.insert(0, "shared_libs")
        from luminaos_common.clients.config_client import get_config_client
        
        config_client = get_config_client()
        if config_client:
            print(f"  ✅ config_client初始化成功")
            print(f"     base_url: {config_client.base_url}")
            
            # 测试读取LLM配置
            llm_config = await config_client.get_llm_config()
            if llm_config:
                print(f"  ✅ 成功读取LLM配置")
                print(f"     api_key: {'已设置' if llm_config.get('api_key') else '未设置'} (长度: {len(llm_config.get('api_key', ''))})")
                print(f"     base_url: {llm_config.get('base_url', 'N/A')}")
                print(f"     model: {llm_config.get('model', 'N/A')}")
            else:
                print("  ⚠️  LLM配置为空")
        else:
            print("  ❌ config_client初始化失败，返回None")
            return False
    except Exception as e:
        print(f"  ❌ config_client测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试5: 测试agent-service的LLM集成
    print(f"\n[测试5] 测试agent-service的LLM集成")
    try:
        sys.path.insert(0, "agent-service")
        from src.core.llm_integration import deepseek_llm
        
        print(f"  config_client: {deepseek_llm.config_client}")
        print(f"  api_key: {'已设置' if deepseek_llm.api_key else '未设置'} (长度: {len(deepseek_llm.api_key) if deepseek_llm.api_key else 0})")
        print(f"  base_url: {deepseek_llm.base_url or 'N/A'}")
        print(f"  model: {deepseek_llm.model or 'N/A'}")
        print(f"  llm: {'已初始化' if deepseek_llm.llm else '未初始化'}")
        
        # 尝试异步加载配置
        await deepseek_llm._load_config_async()
        
        print(f"\n  重新加载后:")
        print(f"  api_key: {'已设置' if deepseek_llm.api_key else '未设置'} (长度: {len(deepseek_llm.api_key) if deepseek_llm.api_key else 0})")
        print(f"  base_url: {deepseek_llm.base_url or 'N/A'}")
        print(f"  model: {deepseek_llm.model or 'N/A'}")
        print(f"  llm: {'已初始化' if deepseek_llm.llm else '未初始化'}")
        
        if deepseek_llm.llm:
            print("  ✅ LLM初始化成功")
            return True
        else:
            print("  ❌ LLM未初始化")
            return False
    except Exception as e:
        print(f"  ❌ LLM集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_config_center())
    if result:
        print("\n" + "="*80)
        print("✅ 所有测试通过！")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ 测试失败，请检查错误信息")
        print("="*80)

