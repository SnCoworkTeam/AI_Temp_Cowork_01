"""
综合技术验证脚本
运行所有验证测试并生成综合报告
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
agent_path = Path(__file__).parent
sys.path.insert(0, str(agent_path))

from test_tech_validation_offline import main as test_offline
from test_sap_annotations_validation import main as test_annotations
from test_relationship_discovery import main as test_relationships
from test_knowledge_graph_integration import main as test_kg_integration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_all_validations():
    """运行所有验证测试"""
    logger.info("=" * 80)
    logger.info("SAP知识图谱建模增强 - 综合技术验证")
    logger.info("=" * 80)
    logger.info(f"开始时间: {datetime.now().isoformat()}\n")
    
    all_results = {}
    
    try:
        # 测试1: 基础架构验证
        logger.info("\n" + "=" * 80)
        logger.info("测试1: 基础架构验证（离线模式）")
        logger.info("=" * 80)
        all_results["basic"] = await test_offline()
        
        # 测试2: SAP注解解析验证
        logger.info("\n" + "=" * 80)
        logger.info("测试2: SAP注解解析准确性验证")
        logger.info("=" * 80)
        all_results["annotations"] = await test_annotations()
        
        # 测试3: 关系发现验证
        logger.info("\n" + "=" * 80)
        logger.info("测试3: 关系发现质量验证")
        logger.info("=" * 80)
        all_results["relationships"] = await test_relationships()
        
        # 测试4: 知识图谱集成验证
        logger.info("\n" + "=" * 80)
        logger.info("测试4: 知识图谱集成验证")
        logger.info("=" * 80)
        all_results["kg_integration"] = await test_kg_integration()
        
    except Exception as e:
        logger.error(f"验证执行失败: {e}", exc_info=True)
        all_results["error"] = str(e)
    
    # 生成综合报告
    logger.info("\n" + "=" * 80)
    logger.info("综合验证报告")
    logger.info("=" * 80)
    logger.info(f"完成时间: {datetime.now().isoformat()}\n")
    
    # 汇总结果
    basic_results = all_results.get("basic", {})
    basic_parsing = basic_results.get("metadata_parsing", {})
    basic_inference = basic_results.get("module_inference", {})
    # 计算解析成功率
    parsing_success_rate = (
        (basic_parsing.get("successful_parses", 0) / basic_parsing.get("total_services", 1)) * 100
        if basic_parsing.get("total_services", 0) > 0 else 0
    )
    # 计算模块推断准确率
    module_accuracy = (
        (basic_inference.get("correct_module", 0) / basic_inference.get("total_cases", 1)) * 100
        if basic_inference.get("total_cases", 0) > 0 else 0
    )
    basic_success = parsing_success_rate >= 85 and module_accuracy >= 80
    
    annotations_results = all_results.get("annotations", {})
    annotations_success = (
        annotations_results.get("entity_label_accuracy", 0) >= 90 and
        annotations_results.get("property_label_accuracy", 0) >= 85 and
        annotations_results.get("property_semantics_accuracy", 0) >= 80
    ) if annotations_results else False
    
    relationships_results = all_results.get("relationships", {})
    # relationships_results可能是metrics字典本身，或者包含metrics键
    if isinstance(relationships_results, dict):
        if "metrics" in relationships_results:
            relationships_metrics = relationships_results.get("metrics", {})
        elif "f1_score" in relationships_results or "precision" in relationships_results:
            relationships_metrics = relationships_results
        else:
            relationships_metrics = {}
    else:
        relationships_metrics = {}
    relationships_f1 = relationships_metrics.get("f1_score", 0) if isinstance(relationships_metrics, dict) else 0
    # f1_score是小数（0-1），需要乘以100转换为百分比，然后比较
    relationships_success = (relationships_f1 * 100) >= 80
    
    kg_results = all_results.get("kg_integration", {})
    kg_concept_storage = kg_results.get("concept_storage", {}) if isinstance(kg_results, dict) else {}
    kg_concept_rate = kg_concept_storage.get("success_rate", 0) if isinstance(kg_concept_storage, dict) else 0
    kg_success = kg_concept_rate >= 95
    
    summary = {
        "基础架构": {
            "状态": "✅ 通过" if basic_success else "❌ 未通过",
            "解析成功率": parsing_success_rate,
            "模块推断": module_accuracy
        },
        "SAP注解解析": {
            "状态": "✅ 通过" if annotations_success else "❌ 未通过",
            "实体标签": annotations_results.get("entity_label_accuracy", 0),
            "属性标签": annotations_results.get("property_label_accuracy", 0),
            "属性语义": annotations_results.get("property_semantics_accuracy", 0)
        },
        "关系发现": {
            "状态": "✅ 通过" if relationships_success else "❌ 未通过",
            "F1分数": (relationships_metrics.get("f1_score", 0) * 100) if isinstance(relationships_metrics, dict) else 0,
            "精确率": (relationships_metrics.get("precision", 0) * 100) if isinstance(relationships_metrics, dict) else 0,
            "召回率": (relationships_metrics.get("recall", 0) * 100) if isinstance(relationships_metrics, dict) else 0
        },
        "知识图谱集成": {
            "状态": "✅ 通过" if kg_success else "❌ 未通过",
            "概念存储": kg_concept_rate,
            "关系存储": kg_results.get("relationship_storage", {}).get("success_rate", 0) if isinstance(kg_results, dict) and "relationship_storage" in kg_results else 0,
            "查询P95": kg_results.get("query_performance", {}).get("p95_time_ms", 0) if isinstance(kg_results, dict) and "query_performance" in kg_results else 0
        }
    }
    
    logger.info("\n验证结果汇总:")
    for category, metrics in summary.items():
        logger.info(f"\n{category}:")
        for key, value in metrics.items():
            if isinstance(value, float):
                if "率" in key or "分数" in key:
                    logger.info(f"  {key}: {value:.1f}%")
                elif "时间" in key:
                    logger.info(f"  {key}: {value:.2f}ms")
                else:
                    logger.info(f"  {key}: {value:.2f}")
            else:
                logger.info(f"  {key}: {value}")
    
    # 总体评估
    passed_count = sum(1 for m in summary.values() if "✅" in m.get("状态", ""))
    total_count = len(summary)
    
    logger.info("\n" + "=" * 80)
    logger.info(f"总体评估: {passed_count}/{total_count} 项通过")
    logger.info("=" * 80)
    
    return {
        "summary": summary,
        "passed_count": passed_count,
        "total_count": total_count,
        "all_results": all_results
    }


if __name__ == "__main__":
    asyncio.run(run_all_validations())

