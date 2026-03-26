"""
测试LLM节点是否真的调用DeepSeek API
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared_libs"))

# 设置环境变量（从Docker容器中读取）
os.environ.setdefault("OPENAI_API_KEY", "sk-979b8f776fdb4626abde191e049c1918")
os.environ.setdefault("LLM_BASE_URL", "https://api.deepseek.com/v1")
os.environ.setdefault("LLM_MODEL", "deepseek-chat")

async def test_llm_node():
    """测试LLM节点"""
    print("=" * 60)
    print("测试LLM节点 - DeepSeek API")
    print("=" * 60)
    
    # 导入LLM节点
    sys.path.insert(0, "/app")
    from src.nodes.llm_node import LLMNode
    
    # 创建LLM节点实例
    node = LLMNode(
        name="test_llm_node",
        description="测试LLM节点",
        config={
            "model": "deepseek-chat",
            "temperature": 0.7,
            "prompt_template": "你好，请用一句话介绍你自己。",
            "base_url": "https://api.deepseek.com"
        }
    )
    
    print(f"\n节点配置:")
    print(f"  模型: {node.model}")
    print(f"  Base URL: {node.base_url}")
    print(f"  API Key: {'已设置' if node.api_key else '未设置'}")
    
    # 准备测试状态
    test_state = {
        "input": "测试输入"
    }
    
    print(f"\n开始执行LLM节点...")
    try:
        result = await node.execute(test_state)
        
        print(f"\n✅ LLM节点执行成功！")
        print(f"\n执行结果:")
        if "test_llm_node_output" in result:
            output = result["test_llm_node_output"]
            print(f"  内容: {output.get('content', 'N/A')[:200]}...")
            print(f"  模型: {output.get('model', 'N/A')}")
        elif "test_llm_node_result" in result:
            print(f"  结果: {result['test_llm_node_result'][:200]}...")
        else:
            print(f"  完整结果: {result}")
        
        return True
    except Exception as e:
        print(f"\n❌ LLM节点执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_llm_node())
    sys.exit(0 if result else 1)

