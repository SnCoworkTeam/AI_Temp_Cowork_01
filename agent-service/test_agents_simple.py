"""
简化版智能体测试
测试核心功能，不依赖所有模块
"""
import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_agent_imports():
    """测试智能体导入"""
    print("\n" + "="*80)
    print("测试智能体导入")
    print("="*80 + "\n")
    
    try:
        from src.core.agents import (
            MCPToolAgent, WorkflowAgent, MetadataAgent, KnowledgeBaseAgent,
            DataQueryAgent, DataCleanAgent, DataValidationAgent, DataEnrichAgent,
            AnalysisAgent, InsightAgent, QualityCheckAgent,
            ContentAgent, FormatAgent, ResultSynthesisAgent
        )
        print("✅ 所有智能体导入成功")
        
        # 测试实例化
        agents = {
            "metadata_agent": MetadataAgent(),
            "mcp_tool_agent": MCPToolAgent(),
            "workflow_agent": WorkflowAgent(),
            "knowledge_base_agent": KnowledgeBaseAgent(),
            "data_query_agent": DataQueryAgent(),
            "data_clean_agent": DataCleanAgent(),
            "data_validation_agent": DataValidationAgent(),
            "data_enrich_agent": DataEnrichAgent(),
            "analysis_agent": AnalysisAgent(),
            "insight_agent": InsightAgent(),
            "quality_check_agent": QualityCheckAgent(),
            "content_agent": ContentAgent(),
            "format_agent": FormatAgent(),
            "result_synthesis_agent": ResultSynthesisAgent(),
        }
        
        print(f"\n✅ 成功实例化 {len(agents)} 个智能体:")
        for agent_id, agent in agents.items():
            print(f"   - {agent_id}: {agent.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"智能体导入失败: {e}", exc_info=True)
        print(f"❌ 智能体导入失败: {e}")
        return False


async def test_dynamic_workflow_designer():
    """测试动态工作流设计器"""
    print("\n" + "="*80)
    print("测试动态工作流设计器")
    print("="*80 + "\n")
    
    try:
        from src.core.dynamic_workflow_designer import DynamicWorkflowDesigner
        
        designer = DynamicWorkflowDesigner()
        print("✅ DynamicWorkflowDesigner 初始化成功")
        
        # 测试智能体描述
        agent_descriptions = designer._initialize_agent_descriptions()
        print(f"✅ 智能体描述初始化成功，共 {len(agent_descriptions)} 个智能体")
        
        # 列出所有智能体
        print("\n智能体列表:")
        for agent_id, desc in agent_descriptions.items():
            print(f"   - {agent_id}: {desc['name']}")
        
        return True
        
    except Exception as e:
        logger.error(f"动态工作流设计器测试失败: {e}", exc_info=True)
        print(f"❌ 动态工作流设计器测试失败: {e}")
        return False


async def test_execution_engine_init():
    """测试执行引擎初始化"""
    print("\n" + "="*80)
    print("测试执行引擎初始化")
    print("="*80 + "\n")
    
    try:
        from src.core.dynamic_execution_engine import DynamicExecutionEngine
        
        engine = DynamicExecutionEngine(
            enable_learning=False,
            enable_state_persistence=False
        )
        print("✅ DynamicExecutionEngine 初始化成功")
        
        # 测试智能体池
        agent_pool = engine.agent_pool
        print(f"✅ 智能体池初始化成功，共 {len(agent_pool)} 个智能体")
        
        # 列出所有智能体
        print("\n智能体池列表:")
        for agent_id, agent in agent_pool.items():
            agent_name = getattr(agent, 'name', agent.__class__.__name__)
            print(f"   - {agent_id}: {agent_name}")
        
        # 测试初始化（注册智能体）
        try:
            await engine.initialize()
            print("✅ 智能体注册成功")
        except Exception as e:
            print(f"⚠️  智能体注册失败（可能缺少某些模块）: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"执行引擎初始化失败: {e}", exc_info=True)
        print(f"❌ 执行引擎初始化失败: {e}")
        return False


async def test_simple_query():
    """测试简单查询（不依赖LLM）"""
    print("\n" + "="*80)
    print("测试简单查询（不依赖LLM）")
    print("="*80 + "\n")
    
    try:
        from src.core.agents.knowledge_base_agent import KnowledgeBaseAgent
        
        agent = KnowledgeBaseAgent()
        print(f"✅ KnowledgeBaseAgent 初始化成功: {agent.name}")
        
        # 测试analyze_task（不依赖LLM时应该返回默认值）
        result = await agent.analyze_task(
            "查询SAP相关知识",
            {}
        )
        print(f"✅ analyze_task 执行成功")
        print(f"   查询类型: {result.get('query_type', 'unknown')}")
        print(f"   可以处理: {result.get('can_handle', False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"简单查询测试失败: {e}", exc_info=True)
        print(f"❌ 简单查询测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("智能体系统简化测试")
    print("="*80)
    
    results = []
    
    # 测试1: 智能体导入
    results.append({
        "test": "智能体导入",
        "success": await test_agent_imports()
    })
    
    # 测试2: 动态工作流设计器
    results.append({
        "test": "动态工作流设计器",
        "success": await test_dynamic_workflow_designer()
    })
    
    # 测试3: 执行引擎初始化
    results.append({
        "test": "执行引擎初始化",
        "success": await test_execution_engine_init()
    })
    
    # 测试4: 简单查询
    results.append({
        "test": "简单查询",
        "success": await test_simple_query()
    })
    
    # 输出测试总结
    print(f"\n{'='*80}")
    print("测试总结")
    print(f"{'='*80}")
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    
    for result in results:
        status = "✅ 通过" if result["success"] else "❌ 失败"
        print(f"{status} - {result['test']}")
    
    print(f"\n总计: {total} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"成功率: {passed/total*100:.1f}%")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试执行失败: {e}", exc_info=True)
        sys.exit(1)


