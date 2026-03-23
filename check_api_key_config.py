"""
检查API Key配置情况
验证配置中心、环境变量和各服务的API key配置
"""
import asyncio
import httpx
import os
import sys

async def check_config_center():
    """检查配置中心的API key配置"""
    print("="*80)
    print("检查配置中心的LLM配置")
    print("="*80)
    
    config_center_url = os.getenv("CONFIG_CENTER_URL", "http://localhost:8090")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 获取所有配置
            response = await client.get(
                f"{config_center_url}/api/configs/all",
                params={"environment": "default"}
            )
            
            if response.status_code == 200:
                configs = response.json()
                
                llm_config = {
                    "api_key": configs.get("llm.api_key", "NOT SET"),
                    "base_url": configs.get("llm.base_url", "NOT SET"),
                    "model": configs.get("llm.model", "NOT SET"),
                    "temperature": configs.get("llm.temperature", "NOT SET"),
                    "max_tokens": configs.get("llm.max_tokens", "NOT SET"),
                }
                
                print(f"\n配置中心URL: {config_center_url}")
                print(f"LLM配置:")
                print(f"  API Key: {'已设置' if llm_config['api_key'] != 'NOT SET' and llm_config['api_key'] else '未设置'}")
                if llm_config['api_key'] and llm_config['api_key'] != 'NOT SET':
                    print(f"    (长度: {len(str(llm_config['api_key']))} 字符)")
                print(f"  Base URL: {llm_config['base_url']}")
                print(f"  Model: {llm_config['model']}")
                print(f"  Temperature: {llm_config['temperature']}")
                print(f"  Max Tokens: {llm_config['max_tokens']}")
                
                return llm_config
            else:
                print(f"❌ 无法连接到配置中心: HTTP {response.status_code}")
                print(f"响应: {response.text}")
                return None
                
    except httpx.ConnectError:
        print(f"❌ 无法连接到配置中心 ({config_center_url})")
        print("   请确保配置中心服务正在运行")
        return None
    except Exception as e:
        print(f"❌ 检查配置中心时发生错误: {e}")
        return None

def check_environment_variables():
    """检查环境变量中的API key"""
    print("\n" + "="*80)
    print("检查环境变量中的LLM配置")
    print("="*80)
    
    env_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "LLM_BASE_URL": os.getenv("LLM_BASE_URL"),
        "LLM_MODEL": os.getenv("LLM_MODEL"),
        "LLM_TEMPERATURE": os.getenv("LLM_TEMPERATURE"),
        "LLM_MAX_TOKENS": os.getenv("LLM_MAX_TOKENS"),
    }
    
    print("\n环境变量:")
    for key, value in env_vars.items():
        if key == "OPENAI_API_KEY":
            if value:
                print(f"  {key}: 已设置 (长度: {len(value)} 字符)")
            else:
                print(f"  {key}: ❌ 未设置")
        else:
            print(f"  {key}: {value or '未设置'}")
    
    return env_vars

async def check_agent_service():
    """检查agent-service的LLM配置"""
    print("\n" + "="*80)
    print("检查Agent Service的LLM配置")
    print("="*80)
    
    try:
        # 尝试导入并检查
        sys.path.insert(0, "agent-service")
        from src.core.llm_integration import deepseek_llm
        
        print(f"\nAgent Service LLM状态:")
        print(f"  API Key: {'已设置' if deepseek_llm.api_key else '❌ 未设置'}")
        if deepseek_llm.api_key:
            print(f"    (长度: {len(deepseek_llm.api_key)} 字符)")
        print(f"  Base URL: {deepseek_llm.base_url or '未设置'}")
        print(f"  Model: {deepseek_llm.model or '未设置'}")
        print(f"  LLM实例: {'已初始化' if deepseek_llm.llm else '❌ 未初始化'}")
        
        return {
            "api_key": deepseek_llm.api_key,
            "base_url": deepseek_llm.base_url,
            "model": deepseek_llm.model,
            "llm_initialized": deepseek_llm.llm is not None
        }
    except Exception as e:
        print(f"❌ 检查Agent Service时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """主函数"""
    print("\n" + "="*80)
    print("API Key配置检查工具")
    print("="*80)
    
    # 检查环境变量
    env_config = check_environment_variables()
    
    # 检查配置中心
    config_center_config = await check_config_center()
    
    # 检查agent-service
    agent_service_config = await check_agent_service()
    
    # 总结
    print("\n" + "="*80)
    print("配置检查总结")
    print("="*80)
    
    issues = []
    
    # 检查API key是否设置
    api_key_set = False
    api_key_source = None
    
    if config_center_config and config_center_config.get("api_key") and config_center_config["api_key"] != "NOT SET":
        api_key_set = True
        api_key_source = "配置中心"
    elif env_config.get("OPENAI_API_KEY"):
        api_key_set = True
        api_key_source = "环境变量"
    
    if not api_key_set:
        issues.append("❌ API Key未设置（配置中心和环境变量都没有）")
    else:
        print(f"✅ API Key已设置（来源: {api_key_source}）")
    
    if agent_service_config and not agent_service_config.get("llm_initialized"):
        issues.append("❌ Agent Service的LLM未初始化")
    elif agent_service_config:
        print(f"✅ Agent Service的LLM已初始化")
    
    if issues:
        print("\n⚠️  发现的问题:")
        for issue in issues:
            print(f"  {issue}")
        
        print("\n💡 建议:")
        if not api_key_set:
            print("  1. 设置环境变量 OPENAI_API_KEY")
            print("  2. 或者通过配置中心API设置 llm.api_key")
            print("  3. 重启所有服务")
    else:
        print("\n✅ 所有配置检查通过！")
    
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())

