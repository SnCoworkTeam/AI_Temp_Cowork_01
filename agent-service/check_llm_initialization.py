"""
检查所有智能体的 LLM 初始化状态和实际使用情况
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_llm_initialization():
    """检查 LLM 初始化状态"""
    
    print("=" * 80)
    print("LLM 初始化状态检查")
    print("=" * 80)
    
    try:
        # 检查 LLM 集成
        from src.core.llm_integration import deepseek_llm
        
        print(f"\n1. DeepSeek LLM 全局实例检查:")
        print(f"   LLM 对象: {deepseek_llm}")
        print(f"   LLM 是否初始化: {deepseek_llm.llm is not None}")
        print(f"   LLM 类型: {type(deepseek_llm.llm).__name__ if deepseek_llm.llm else 'None'}")
        print(f"   API Key: {'已设置' if deepseek_llm.api_key else '未设置'}")
        print(f"   Base URL: {deepseek_llm.base_url or '未设置'}")
        print(f"   Model: {deepseek_llm.model or '未设置'}")
        
        # 检查智能体池
        from src.core.dynamic_execution_engine import DynamicExecutionEngine
        
        engine = DynamicExecutionEngine()
        await engine.initialize()
        
        print(f"\n2. 智能体 LLM 状态检查:")
        print(f"   找到 {len(engine.agent_pool)} 个智能体\n")
        
        llm_status_report = []
        
        for agent_id, agent in engine.agent_pool.items():
            # 获取原始智能体（如果是适配器）
            original_agent = agent
            if hasattr(agent, 'legacy_agent'):
                original_agent = agent.legacy_agent
            
            agent_info = {
                "agent_id": agent_id,
                "agent_name": getattr(agent, 'name', 'Unknown'),
                "agent_type": type(original_agent).__name__,
                "is_adapter": hasattr(agent, 'legacy_agent'),
                "has_llm_attr": hasattr(original_agent, 'llm'),
                "llm_value": None,
                "llm_is_none": False,
                "llm_is_deepseek": False,
                "llm_initialized": False
            }
            
            # 检查原始智能体的 llm 属性
            if hasattr(original_agent, 'llm'):
                llm_obj = getattr(original_agent, 'llm')
                agent_info["llm_value"] = llm_obj
                agent_info["llm_is_none"] = llm_obj is None
                
                if llm_obj is not None:
                    agent_info["llm_is_deepseek"] = llm_obj is deepseek_llm
                    # 检查 LLM 是否真正初始化
                    if hasattr(llm_obj, 'llm'):
                        agent_info["llm_initialized"] = llm_obj.llm is not None
            
            llm_status_report.append(agent_info)
        
        # 打印报告
        print("\n" + "=" * 80)
        print("智能体 LLM 状态报告")
        print("=" * 80)
        
        for info in llm_status_report:
            status_icon = "✅" if info["llm_initialized"] else "⚠️" if info["has_llm_attr"] else "❌"
            
            print(f"\n{status_icon} {info['agent_name']} ({info['agent_id']})")
            print(f"   类型: {info['agent_type']}")
            print(f"   是否适配器: {info['is_adapter']}")
            print(f"   有 llm 属性: {info['has_llm_attr']}")
            if info['has_llm_attr']:
                print(f"   LLM 对象: {info['llm_value']}")
                print(f"   LLM 是 None: {info['llm_is_none']}")
                if not info['llm_is_none']:
                    print(f"   是 deepseek_llm: {info['llm_is_deepseek']}")
                    print(f"   LLM 已初始化: {info['llm_initialized']}")
        
        # 统计
        total = len(llm_status_report)
        has_llm_attr = sum(1 for info in llm_status_report if info["has_llm_attr"])
        llm_initialized = sum(1 for info in llm_status_report if info["llm_initialized"])
        llm_is_none = sum(1 for info in llm_status_report if info["llm_is_none"])
        
        print("\n" + "=" * 80)
        print("统计摘要")
        print("=" * 80)
        print(f"总智能体数: {total}")
        print(f"✅ 有 llm 属性且已初始化: {llm_initialized}")
        print(f"⚠️  有 llm 属性但未初始化: {has_llm_attr - llm_initialized}")
        print(f"❌ LLM 是 None: {llm_is_none}")
        print(f"❌ 没有 llm 属性: {total - has_llm_attr}")
        
        # 列出有问题的智能体
        problematic = [info for info in llm_status_report 
                       if not info["llm_initialized"]]
        
        if problematic:
            print("\n" + "=" * 80)
            print("⚠️  LLM 未正确初始化的智能体")
            print("=" * 80)
            for info in problematic:
                issues = []
                if not info["has_llm_attr"]:
                    issues.append("没有 llm 属性")
                elif info["llm_is_none"]:
                    issues.append("llm 是 None")
                elif not info["llm_initialized"]:
                    issues.append("LLM 对象未初始化")
                print(f"  - {info['agent_name']}: {', '.join(issues)}")
        
        # 测试 LLM 调用
        print("\n" + "=" * 80)
        print("测试 LLM 调用")
        print("=" * 80)
        
        try:
            test_response = await deepseek_llm.chat([
                {"role": "user", "content": "测试"}
            ])
            print(f"✅ LLM 调用成功，响应长度: {len(test_response)} 字符")
        except Exception as e:
            print(f"❌ LLM 调用失败: {e}")
        
        return llm_status_report
        
    except Exception as e:
        logger.error(f"检查失败: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    asyncio.run(check_llm_initialization())

