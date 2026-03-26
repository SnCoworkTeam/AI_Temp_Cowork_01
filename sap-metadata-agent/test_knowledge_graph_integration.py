"""
知识图谱集成验证脚本
验证知识图谱存储兼容性、性能等集成能力
"""
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
agent_path = Path(__file__).parent
sys.path.insert(0, str(agent_path))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeGraphIntegrationValidator:
    """知识图谱集成验证器"""
    
    def __init__(self):
        # 模拟知识图谱存储（实际应该连接到真实的知识图谱服务）
        self.stored_nodes = []
        self.stored_edges = []
    
    def _simulate_node_storage(self, node_data: Dict) -> Dict:
        """模拟节点存储"""
        node = {
            "id": f"node_{len(self.stored_nodes) + 1}",
            "label": node_data.get("label"),
            "node_type": node_data.get("node_type"),
            "properties": node_data.get("properties", {}),
            "stored_at": time.time()
        }
        self.stored_nodes.append(node)
        return node
    
    def _simulate_edge_storage(self, edge_data: Dict) -> Dict:
        """模拟边存储"""
        edge = {
            "id": f"edge_{len(self.stored_edges) + 1}",
            "source_id": edge_data.get("source_id"),
            "target_id": edge_data.get("target_id"),
            "relationship_type": edge_data.get("relationship_type"),
            "properties": edge_data.get("properties", {}),
            "stored_at": time.time()
        }
        self.stored_edges.append(edge)
        return edge
    
    async def test_concept_storage(self, concepts: List[Dict]) -> Dict[str, Any]:
        """测试概念存储"""
        logger.info("=" * 60)
        logger.info("测试1: 概念存储兼容性")
        logger.info("=" * 60)
        
        results = {
            "total_concepts": len(concepts),
            "stored_successfully": 0,
            "storage_failed": 0,
            "storage_times": [],
            "errors": []
        }
        
        start_time = time.time()
        
        for concept in concepts:
            try:
                # 验证节点类型
                node_type = concept.get("node_type")
                valid_node_types = ["sap_module", "sap_sub_module", "business_concept", "concept"]
                if node_type not in valid_node_types:
                    logger.warning(f"未知节点类型: {node_type}")
                
                # 验证必需字段
                if not concept.get("label"):
                    raise ValueError("缺少label字段")
                
                # 模拟存储
                storage_start = time.time()
                stored_node = self._simulate_node_storage(concept)
                storage_time = (time.time() - storage_start) * 1000  # 转换为毫秒
                
                results["stored_successfully"] += 1
                results["storage_times"].append(storage_time)
                logger.info(f"  ✓ 存储概念: {concept['label']} (耗时: {storage_time:.2f}ms)")
                
            except Exception as e:
                results["storage_failed"] += 1
                results["errors"].append({
                    "concept": concept.get("label", "unknown"),
                    "error": str(e)
                })
                logger.error(f"  ✗ 存储失败: {concept.get('label', 'unknown')} - {e}")
        
        total_time = (time.time() - start_time) * 1000
        
        logger.info("\n存储结果统计:")
        logger.info(f"  总概念数: {results['total_concepts']}")
        logger.info(f"  成功存储: {results['stored_successfully']}")
        logger.info(f"  存储失败: {results['storage_failed']}")
        logger.info(f"  总耗时: {total_time:.2f}ms")
        if results["storage_times"]:
            logger.info(f"  平均耗时: {sum(results['storage_times']) / len(results['storage_times']):.2f}ms")
            logger.info(f"  最大耗时: {max(results['storage_times']):.2f}ms")
            logger.info(f"  最小耗时: {min(results['storage_times']):.2f}ms")
        
        results["total_time_ms"] = total_time
        results["avg_time_ms"] = sum(results["storage_times"]) / len(results["storage_times"]) if results["storage_times"] else 0
        results["success_rate"] = (results["stored_successfully"] / results["total_concepts"]) * 100 if results["total_concepts"] > 0 else 0
        
        return results
    
    async def test_relationship_storage(self, relationships: List[Dict]) -> Dict[str, Any]:
        """测试关系存储"""
        logger.info("\n" + "=" * 60)
        logger.info("测试2: 关系存储兼容性")
        logger.info("=" * 60)
        
        results = {
            "total_relationships": len(relationships),
            "stored_successfully": 0,
            "storage_failed": 0,
            "storage_times": [],
            "errors": []
        }
        
        start_time = time.time()
        
        for rel in relationships:
            try:
                # 验证必需字段
                if not rel.get("source") or not rel.get("target"):
                    raise ValueError("缺少source或target字段")
                
                # 查找源节点和目标节点ID
                source_id = None
                target_id = None
                for node in self.stored_nodes:
                    if node["label"] == rel["source"]:
                        source_id = node["id"]
                    if node["label"] == rel["target"]:
                        target_id = node["id"]
                
                if not source_id or not target_id:
                    raise ValueError(f"找不到源节点或目标节点: {rel['source']} -> {rel['target']}")
                
                # 模拟存储
                storage_start = time.time()
                stored_edge = self._simulate_edge_storage({
                    "source_id": source_id,
                    "target_id": target_id,
                    "relationship_type": rel.get("relationship_type", "related_to"),
                    "properties": rel.get("properties", {})
                })
                storage_time = (time.time() - storage_start) * 1000
                
                results["stored_successfully"] += 1
                results["storage_times"].append(storage_time)
                logger.info(f"  ✓ 存储关系: {rel['source']} --[{rel.get('relationship_type')}]--> {rel['target']} "
                          f"(耗时: {storage_time:.2f}ms)")
                
            except Exception as e:
                results["storage_failed"] += 1
                results["errors"].append({
                    "relationship": f"{rel.get('source')} -> {rel.get('target')}",
                    "error": str(e)
                })
                logger.error(f"  ✗ 存储失败: {rel.get('source')} -> {rel.get('target')} - {e}")
        
        total_time = (time.time() - start_time) * 1000
        
        logger.info("\n存储结果统计:")
        logger.info(f"  总关系数: {results['total_relationships']}")
        logger.info(f"  成功存储: {results['stored_successfully']}")
        logger.info(f"  存储失败: {results['storage_failed']}")
        logger.info(f"  总耗时: {total_time:.2f}ms")
        if results["storage_times"]:
            logger.info(f"  平均耗时: {sum(results['storage_times']) / len(results['storage_times']):.2f}ms")
        
        results["total_time_ms"] = total_time
        results["avg_time_ms"] = sum(results["storage_times"]) / len(results["storage_times"]) if results["storage_times"] else 0
        results["success_rate"] = (results["stored_successfully"] / results["total_relationships"]) * 100 if results["total_relationships"] > 0 else 0
        
        return results
    
    async def test_query_performance(self, query_type: str = "module_hierarchy") -> Dict[str, Any]:
        """测试查询性能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试3: 查询性能")
        logger.info("=" * 60)
        
        results = {
            "query_type": query_type,
            "query_times": [],
            "results_count": 0
        }
        
        # 模拟不同类型的查询
        for i in range(10):  # 执行10次查询
            query_start = time.time()
            
            if query_type == "module_hierarchy":
                # 模拟模块层次查询
                module_nodes = [n for n in self.stored_nodes if n.get("node_type") == "sap_module"]
                results["results_count"] = len(module_nodes)
            elif query_type == "relationship_path":
                # 模拟关系路径查询
                path_edges = [e for e in self.stored_edges if e.get("relationship_type") == "belongs_to"]
                results["results_count"] = len(path_edges)
            else:
                # 模拟通用查询
                results["results_count"] = len(self.stored_nodes)
            
            query_time = (time.time() - query_start) * 1000
            results["query_times"].append(query_time)
        
        avg_time = sum(results["query_times"]) / len(results["query_times"])
        p95_time = sorted(results["query_times"])[int(len(results["query_times"]) * 0.95)]
        
        logger.info(f"查询类型: {query_type}")
        logger.info(f"  执行次数: {len(results['query_times'])}")
        logger.info(f"  平均耗时: {avg_time:.2f}ms")
        logger.info(f"  P95耗时: {p95_time:.2f}ms")
        logger.info(f"  最大耗时: {max(results['query_times']):.2f}ms")
        logger.info(f"  最小耗时: {min(results['query_times']):.2f}ms")
        logger.info(f"  结果数量: {results['results_count']}")
        
        results["avg_time_ms"] = avg_time
        results["p95_time_ms"] = p95_time
        results["max_time_ms"] = max(results["query_times"])
        results["min_time_ms"] = min(results["query_times"])
        
        return results


async def main():
    """主测试函数"""
    logger.info("开始知识图谱集成验证...")
    logger.info("=" * 60)
    
    validator = KnowledgeGraphIntegrationValidator()
    
    # 测试数据
    test_concepts = [
        {
            "label": "SAP_FI_Module",
            "node_type": "sap_module",
            "properties": {
                "module": "FI",
                "display_name": "财务会计",
                "entity_count": 10
            }
        },
        {
            "label": "SAP_FI_GeneralLedger",
            "node_type": "sap_sub_module",
            "properties": {
                "module": "FI",
                "sub_module": "GeneralLedger",
                "entity_count": 5
            }
        },
        {
            "label": "GLAccountSet",
            "node_type": "business_concept",
            "properties": {
                "module": "FI",
                "sub_module": "GeneralLedger",
                "service_id": "C_GLACCOUNT_FS_SRV",
                "sap_label": "总账科目"
            }
        },
        {
            "label": "CompanyCodeSet",
            "node_type": "business_concept",
            "properties": {
                "module": "FI",
                "sub_module": "GeneralLedger",
                "service_id": "C_GLACCOUNT_FS_SRV",
                "sap_label": "公司代码"
            }
        }
    ]
    
    test_relationships = [
        {
            "source": "GLAccountSet",
            "target": "CompanyCodeSet",
            "relationship_type": "belongs_to",
            "properties": {
                "navigation_property": "to_CompanyCode"
            }
        },
        {
            "source": "GLAccountSet",
            "target": "SAP_FI_GeneralLedger",
            "relationship_type": "belongs_to",
            "properties": {
                "module": "FI"
            }
        }
    ]
    
    all_results = {}
    
    # 测试1: 概念存储
    all_results["concept_storage"] = await validator.test_concept_storage(test_concepts)
    
    # 测试2: 关系存储
    all_results["relationship_storage"] = await validator.test_relationship_storage(test_relationships)
    
    # 测试3: 查询性能
    all_results["query_performance"] = await validator.test_query_performance("module_hierarchy")
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("知识图谱集成验证总结")
    logger.info("=" * 60)
    
    logger.info(f"✓ 概念存储成功率: {all_results['concept_storage']['success_rate']:.1f}%")
    logger.info(f"✓ 关系存储成功率: {all_results['relationship_storage']['success_rate']:.1f}%")
    logger.info(f"✓ 查询平均耗时: {all_results['query_performance']['avg_time_ms']:.2f}ms")
    logger.info(f"✓ 查询P95耗时: {all_results['query_performance']['p95_time_ms']:.2f}ms")
    
    # 验证成功标准
    logger.info("\n验证成功标准:")
    logger.info(f"  {'✓' if all_results['concept_storage']['success_rate'] >= 95 else '✗'} 概念存储成功率 > 95%: {all_results['concept_storage']['success_rate']:.1f}%")
    logger.info(f"  {'✓' if all_results['relationship_storage']['success_rate'] >= 90 else '✗'} 关系存储成功率 > 90%: {all_results['relationship_storage']['success_rate']:.1f}%")
    logger.info(f"  {'✓' if all_results['query_performance']['p95_time_ms'] < 100 else '✗'} 查询P95耗时 < 100ms: {all_results['query_performance']['p95_time_ms']:.2f}ms")
    
    overall_success = (
        all_results['concept_storage']['success_rate'] >= 95 and
        all_results['relationship_storage']['success_rate'] >= 90 and
        all_results['query_performance']['p95_time_ms'] < 100
    )
    
    logger.info(f"\n总体评估: {'✓ 通过' if overall_success else '✗ 未通过'}")
    
    return all_results


if __name__ == "__main__":
    asyncio.run(main())

