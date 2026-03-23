"""
设置API Key到配置中心
确保API key统一管理
"""
import asyncio
import httpx
import os
import sys

async def setup_api_key():
    """设置API key到配置中心"""
    config_center_url = os.getenv("CONFIG_CENTER_URL", "http://localhost:8090")
    
    # 从环境变量读取API key
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    temperature = os.getenv("LLM_TEMPERATURE", "0.7")
    max_tokens = os.getenv("LLM_MAX_TOKENS", "4096")
    
    if not api_key:
        print("❌ 环境变量 OPENAI_API_KEY 未设置")
        print("   请先设置环境变量：")
        print("   export OPENAI_API_KEY=your-api-key-here")
        print("   或者在 .env 文件中设置")
        return False
    
    print("="*80)
    print("设置API Key到配置中心")
    print("="*80)
    print(f"配置中心URL: {config_center_url}")
    print(f"API Key: {'已设置' if api_key else '未设置'} (长度: {len(api_key)} 字符)")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print()
    
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
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            success_count = 0
            for config in configs:
                try:
                    response = await client.post(
                        f"{config_center_url}/api/config",
                        json=config
                    )
                    
                    if response.status_code in [200, 201]:
                        print(f"✅ 设置成功: {config['key']} = {str(config['value'])[:50]}...")
                        success_count += 1
                    else:
                        print(f"❌ 设置失败: {config['key']} - HTTP {response.status_code}")
                        print(f"   响应: {response.text[:200]}")
                except Exception as e:
                    print(f"❌ 设置失败: {config['key']} - {e}")
            
            print("\n" + "="*80)
            if success_count == len(configs):
                print(f"✅ 所有配置设置成功 ({success_count}/{len(configs)})")
                return True
            else:
                print(f"⚠️  部分配置设置失败 ({success_count}/{len(configs)})")
                return False
                
    except httpx.ConnectError:
        print(f"❌ 无法连接到配置中心 ({config_center_url})")
        print("   请确保配置中心服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 设置配置时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_api_key())
    sys.exit(0 if success else 1)

