"""
测试agent-service的config_client和LLM配置读取
"""
import asyncio
import os
import sys

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_agent_service():
    """测试agent-service的配置读取"""
    print("="*80)
    print("测试agent-service的config_client和LLM配置读取")
    print("="*80)
    
    # 设置环境变量
    os.environ["CONFIG_CENTER_URL"] = "http://localhost:8090"
    os.environ["MCP_GATEWAY_URL"] = "http://localhost:8001"
    
    # 测试agent-service的LLM集成
    print("\n[测试] 测试agent-service的LLM集成")
    try:
        sys.path.insert(0, "agent-service")
        from src.core.llm_integration import deepseek_llm
        
        print(f"\n  初始状态:")
        print(f"  config_client: {deepseek_llm.config_client}")
        if deepseek_llm.config_client:
            print(f"  config_center_url: {deepseek_llm.config_client.config_center_url}")
        print(f"  api_key: {'已设置' if deepseek_llm.api_key else '未设置'} (长度: {len(deepseek_llm.api_key) if deepseek_llm.api_key else 0})")
        print(f"  base_url: {deepseek_llm.base_url or 'N/A'}")
        print(f"  model: {deepseek_llm.model or 'N/A'}")
        
        # 异步加载配置
        print(f"\n  执行异步加载配置...")
        await deepseek_llm._load_config_async()
        
        print(f"\n  加载后状态:")
        print(f"  config_client: {deepseek_llm.config_client}")
        if deepseek_llm.config_client:
            print(f"  config_center_url: {deepseek_llm.config_client.config_center_url}")
        print(f"  api_key: {'已设置' if deepseek_llm.api_key else '未设置'} (长度: {len(deepseek_llm.api_key) if deepseek_llm.api_key else 0})")
        print(f"  base_url: {deepseek_llm.base_url or 'N/A'}")
        print(f"  model: {deepseek_llm.model or 'N/A'}")
        print(f"  llm: {'已初始化' if deepseek_llm.llm else '未初始化'}")
        
        if deepseek_llm.api_key:
            print("\n  ✅ API key已从配置中心读取")
            
            # 如果LLM未初始化，尝试初始化（可能是langchain未安装）
            if not deepseek_llm.llm:
                print("  ⚠️  LLM未初始化（可能是langchain未安装，但不影响配置读取）")
            
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
    result = asyncio.run(test_agent_service())
    if result:
        print("\n" + "="*80)
        print("✅ config_client修复成功！可以正常从配置中心读取API key")
        print("="*80)
        print("\n注意: 如果LLM未初始化，可能是因为langchain未安装。")
        print("      但配置读取功能已正常工作。")
    else:
        print("\n" + "="*80)
        print("⚠️  部分测试未通过，请检查错误信息")
        print("="*80)

