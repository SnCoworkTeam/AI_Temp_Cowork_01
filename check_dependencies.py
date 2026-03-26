"""
检查依赖是否安装
"""
import sys

print("="*80)
print("依赖检查")
print("="*80)

dependencies = {
    "httpx": "HTTP客户端（config_client需要）",
    "langchain": "LangChain核心库（LLM集成需要）",
    "langchain_openai": "LangChain OpenAI集成（LLM初始化需要）",
    "pydantic": "数据验证库（luminaos_common需要）",
}

results = {}
for dep_name, description in dependencies.items():
    try:
        __import__(dep_name)
        results[dep_name] = True
        print(f"✅ {dep_name:20s} - 已安装 - {description}")
    except ImportError:
        results[dep_name] = False
        print(f"❌ {dep_name:20s} - 未安装 - {description}")

print("\n" + "="*80)
if all(results.values()):
    print("✅ 所有依赖已安装")
else:
    print("⚠️  部分依赖未安装")
    print("\n安装命令:")
    print("  cd agent-service")
    print("  pip install -r requirements.txt")
    print("="*80)

