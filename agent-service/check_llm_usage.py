"""
检查所有智能体是否真正使用了 DeepSeek LLM
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

async def check_agent_llm_usage():
    """检查所有智能体的 LLM 使用情况"""
    
    print("=" * 80)
    print("智能体 LLM 使用情况检查")
    print("=" * 80)
    
    try:
        from src.core.dynamic_execution_engine import DynamicExecutionEngine
        
        engine = DynamicExecutionEngine()
        await engine.initialize()
        
        print(f"\n找到 {len(engine.agent_pool)} 个智能体\n")
        
        llm_usage_report = []
        
        for agent_id, agent in engine.agent_pool.items():
            agent_info = {
                "agent_id": agent_id,
                "agent_name": getattr(agent, 'name', 'Unknown'),
                "agent_type": type(agent).__name__,
                "has_llm_attribute": hasattr(agent, 'llm'),
                "llm_is_none": False,
                "llm_type": None,
                "uses_llm_chat": False,
                "llm_imports": [],
                "file_path": None
            }
            
            # 检查是否有 llm 属性
            if hasattr(agent, 'llm'):
                llm_obj = getattr(agent, 'llm')
                agent_info["llm_is_none"] = llm_obj is None
                if llm_obj is not None:
                    agent_info["llm_type"] = type(llm_obj).__name__
            
            # 检查源代码中是否使用了 LLM
            agent_file = None
            agent_class_name = type(agent).__name__
            
            # 查找智能体文件
            agents_dir = project_root / "src" / "core" / "agents"
            for py_file in agents_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if f"class {agent_class_name}" in content:
                            agent_file = py_file
                            agent_info["file_path"] = str(py_file.relative_to(project_root))
                            
                            # 检查是否导入了 deepseek_llm
                            if "from ..llm_integration import deepseek_llm" in content or \
                               "from .llm_integration import deepseek_llm" in content:
                                agent_info["llm_imports"].append("deepseek_llm")
                            
                            # 检查是否使用了 llm.chat
                            if "llm.chat" in content or "self.llm.chat" in content:
                                agent_info["uses_llm_chat"] = True
                            
                            # 检查是否有 fallback 逻辑（不使用 LLM）
                            if "if not self.llm" in content or "if self.llm is None" in content:
                                agent_info["has_fallback"] = True
                            else:
                                agent_info["has_fallback"] = False
                            
                            break
                except Exception as e:
                    logger.warning(f"Failed to read {py_file}: {e}")
            
            llm_usage_report.append(agent_info)
        
        # 打印报告
        print("\n" + "=" * 80)
        print("LLM 使用情况报告")
        print("=" * 80)
        
        for info in llm_usage_report:
            status_icon = "✅" if info["uses_llm_chat"] and not info.get("has_fallback", False) else "⚠️" if info.get("has_fallback", False) else "❌"
            
            print(f"\n{status_icon} {info['agent_name']} ({info['agent_id']})")
            print(f"   类型: {info['agent_type']}")
            print(f"   文件: {info['file_path'] or '未找到'}")
            print(f"   有 llm 属性: {info['has_llm_attribute']}")
            if info['has_llm_attribute']:
                print(f"   LLM 对象: {info['llm_type'] or 'None'}")
            print(f"   导入 deepseek_llm: {len(info['llm_imports']) > 0}")
            print(f"   使用 llm.chat: {info['uses_llm_chat']}")
            if info.get("has_fallback"):
                print(f"   ⚠️  有 fallback 逻辑（可能不使用 LLM）")
        
        # 统计
        total = len(llm_usage_report)
        using_llm = sum(1 for info in llm_usage_report if info["uses_llm_chat"])
        has_fallback = sum(1 for info in llm_usage_report if info.get("has_fallback", False))
        no_llm = total - using_llm
        
        print("\n" + "=" * 80)
        print("统计摘要")
        print("=" * 80)
        print(f"总智能体数: {total}")
        print(f"✅ 使用 LLM: {using_llm}")
        print(f"⚠️  有 fallback: {has_fallback}")
        print(f"❌ 未使用 LLM: {no_llm}")
        
        # 列出有问题的智能体
        problematic = [info for info in llm_usage_report 
                       if not info["uses_llm_chat"] or info.get("has_fallback", False)]
        
        if problematic:
            print("\n" + "=" * 80)
            print("⚠️  需要关注的智能体")
            print("=" * 80)
            for info in problematic:
                issues = []
                if not info["uses_llm_chat"]:
                    issues.append("未使用 llm.chat")
                if info.get("has_fallback", False):
                    issues.append("有 fallback 逻辑")
                print(f"  - {info['agent_name']}: {', '.join(issues)}")
        
        return llm_usage_report
        
    except Exception as e:
        logger.error(f"检查失败: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    asyncio.run(check_agent_llm_usage())

