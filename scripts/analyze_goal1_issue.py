#!/usr/bin/env python3
"""
目标1未达成原因详细分析脚本
分析知识图谱边数不足200的原因：数据不完整 vs 技术问题
"""

import requests
import json
from collections import defaultdict
from typing import Dict, List, Any

# 配置
METADATA_SERVICE_URL = "http://localhost:8005"

def get_knowledge_graph_stats() -> Dict[str, Any]:
    """获取知识图谱统计信息"""
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get('statistics', {})
        else:
            print(f"❌ 获取知识图谱统计失败: {r.status_code}")
            return {}
    except Exception as e:
        print(f"❌ 获取知识图谱统计异常: {e}")
        return {}

def get_business_entities(max_entities: int = 1000) -> List[Dict[str, Any]]:
    """获取业务实体列表（分页获取）"""
    try:
        all_entities = []
        skip = 0
        page_limit = 100  # API限制最大100
        
        while len(all_entities) < max_entities:
            url = f"{METADATA_SERVICE_URL}/api/business-entities?skip={skip}&limit={page_limit}"
            r = requests.get(url, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    page_entities = data
                elif isinstance(data, dict):
                    # 尝试多种可能的字段名
                    page_entities = data.get('entities', []) or data.get('data', []) or data.get('items', [])
                else:
                    page_entities = []
                
                if not page_entities:
                    break  # 没有更多数据
                
                all_entities.extend(page_entities)
                
                if len(page_entities) < page_limit:
                    break  # 最后一页
                
                skip += page_limit
            else:
                print(f"⚠️ 获取实体失败 (skip={skip}): {r.status_code}")
                break
        
        if all_entities:
            return all_entities[:max_entities]
        
        # 如果都失败，尝试从知识图谱节点中提取
        print("⚠️ 无法通过API获取实体，尝试从知识图谱节点提取...")
        try:
            r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/nodes?node_type=concept&limit=100", timeout=10)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict):
                    nodes = data.get('nodes', []) or data.get('data', [])
                    if nodes:
                        return nodes
        except:
            pass
        
        print(f"❌ 获取业务实体失败")
        return []
    except Exception as e:
        print(f"❌ 获取业务实体异常: {e}")
        return []

def analyze_entity_data(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析实体数据完整性"""
    analysis = {
        "total_entities": len(entities),
        "entities_with_parent_id": 0,
        "entities_with_related_entities": 0,
        "entities_with_module": 0,
        "entities_with_submodule": 0,
        "parent_relationships": 0,
        "related_relationships": 0,
        "module_distribution": defaultdict(int),
        "submodule_distribution": defaultdict(int),
        "module_entity_map": defaultdict(list)
    }
    
    for entity in entities:
        # 检查parent_id（尝试多种可能的字段名）
        parent_id = entity.get("parent_id") or entity.get("parentId") or entity.get("parent_entity_id")
        if parent_id:
            analysis["entities_with_parent_id"] += 1
            analysis["parent_relationships"] += 1
        
        # 检查related_entities（尝试多种可能的字段名）
        related_entities = (
            entity.get("related_entities") or 
            entity.get("relatedEntities") or 
            entity.get("related_entity_ids") or
            entity.get("related_entity_list") or
            []
        )
        if related_entities and isinstance(related_entities, list) and len(related_entities) > 0:
            analysis["entities_with_related_entities"] += 1
            analysis["related_relationships"] += len(related_entities)
        
        # 检查模块信息（尝试多种可能的字段名和位置）
        metadata = entity.get("extra_metadata") or entity.get("metadata") or {}
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        
        # 尝试从metadata中获取
        module = metadata.get("sap_module") or metadata.get("sapModule") or metadata.get("module")
        sub_module = metadata.get("sap_sub_module") or metadata.get("sapSubModule") or metadata.get("sub_module")
        
        # 如果metadata中没有，尝试直接从entity中获取
        if not module:
            module = entity.get("sap_module") or entity.get("sapModule") or entity.get("module")
        if not sub_module:
            sub_module = entity.get("sap_sub_module") or entity.get("sapSubModule") or entity.get("sub_module")
        
        if module:
            analysis["entities_with_module"] += 1
            analysis["module_distribution"][module] += 1
            module_key = f"{module}/{sub_module or 'General'}"
            analysis["module_entity_map"][module_key].append(entity)
        
        if sub_module:
            analysis["submodule_distribution"][sub_module] += 1
    
    return analysis

def calculate_potential_relationships(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """计算潜在关系数"""
    potential = {
        "parent_relationships": analysis["parent_relationships"],
        "related_relationships": analysis["related_relationships"],
        "same_module_relationships": {},
        "total_potential": 0
    }
    
    # 计算同模块关系（考虑限制为5）
    same_module_total = 0
    for module_key, entities in analysis["module_entity_map"].items():
        entity_count = len(entities)
        # 全连接关系数
        full_connections = entity_count * (entity_count - 1) // 2
        # 实际创建数（每个实体最多5个）
        actual_connections = min(entity_count * 5, full_connections)
        potential["same_module_relationships"][module_key] = {
            "entity_count": entity_count,
            "full_connections": full_connections,
            "actual_connections": actual_connections
        }
        same_module_total += actual_connections
    
    potential["same_module_total"] = same_module_total
    potential["total_potential"] = (
        potential["parent_relationships"] +
        potential["related_relationships"] +
        same_module_total
    )
    
    return potential

def analyze_relationship_engine_limits() -> Dict[str, Any]:
    """分析关系发现引擎的限制"""
    limits = {
        "same_module_max_per_entity": 5,
        "description": "每个实体最多5个同模块关系（在relationship_rule_engine.py中定义）"
    }
    return limits

def main():
    print("=" * 60)
    print("目标1未达成原因详细分析")
    print("=" * 60)
    print()
    
    # 1. 获取知识图谱统计
    print("📊 1. 知识图谱当前状态")
    print("-" * 60)
    stats = get_knowledge_graph_stats()
    if stats:
        print(f"节点数: {stats.get('total_nodes', 0)}")
        print(f"边数: {stats.get('total_edges', 0)} ❌ (目标: >200)")
        print(f"节点类型分布: {stats.get('nodes_by_type', {})}")
        print(f"边类型分布: {stats.get('edges_by_type', {})}")
    else:
        print("❌ 无法获取知识图谱统计")
    print()
    
    # 2. 获取业务实体数据
    print("📋 2. 业务实体数据检查")
    print("-" * 60)
    entities = get_business_entities(max_entities=1000)
    print(f"实体总数: {len(entities)}")
    print()
    
    if not entities:
        print("❌ 无法获取业务实体数据，无法继续分析")
        return
    
    # 3. 分析实体数据完整性
    print("🔍 3. 实体数据完整性分析")
    print("-" * 60)
    entity_analysis = analyze_entity_data(entities)
    print(f"总实体数: {entity_analysis['total_entities']}")
    print(f"有parent_id的实体: {entity_analysis['entities_with_parent_id']} ({entity_analysis['entities_with_parent_id']/entity_analysis['total_entities']*100:.1f}%)")
    print(f"有related_entities的实体: {entity_analysis['entities_with_related_entities']} ({entity_analysis['entities_with_related_entities']/entity_analysis['total_entities']*100:.1f}%)")
    print(f"有sap_module的实体: {entity_analysis['entities_with_module']} ({entity_analysis['entities_with_module']/entity_analysis['total_entities']*100:.1f}%)")
    print()
    
    # 4. 计算潜在关系数
    print("📈 4. 潜在关系数计算")
    print("-" * 60)
    potential = calculate_potential_relationships(entity_analysis)
    print(f"潜在父子关系数: {potential['parent_relationships']}")
    print(f"潜在关联关系数: {potential['related_relationships']}")
    print(f"潜在同模块关系数: {potential['same_module_total']} (考虑限制为5)")
    print(f"潜在总关系数: {potential['total_potential']}")
    print()
    
    # 5. 模块分布分析
    print("📦 5. 模块分布分析")
    print("-" * 60)
    if entity_analysis['module_entity_map']:
        print("模块/子模块分布（前10个）:")
        for i, (module_key, ents) in enumerate(list(entity_analysis['module_entity_map'].items())[:10]):
            entity_count = len(ents)
            full_conn = entity_count * (entity_count - 1) // 2
            actual_conn = min(entity_count * 5, full_conn)
            print(f"  {i+1}. {module_key}: {entity_count}个实体, 潜在关系: {full_conn} (实际: {actual_conn})")
    else:
        print("❌ 没有找到模块信息")
    print()
    
    # 6. 关系发现引擎限制分析
    print("⚙️ 6. 关系发现引擎限制分析")
    print("-" * 60)
    limits = analyze_relationship_engine_limits()
    print(f"同模块关系限制: 每个实体最多{limits['same_module_max_per_entity']}个")
    print(f"说明: {limits['description']}")
    print()
    
    # 7. 问题诊断
    print("🔬 7. 问题诊断")
    print("-" * 60)
    current_edges = stats.get('total_edges', 0)
    potential_edges = potential['total_potential']
    gap = potential_edges - current_edges
    
    print(f"当前边数: {current_edges}")
    print(f"潜在边数: {potential_edges}")
    if potential_edges > 0:
        print(f"差距: {gap} ({gap/potential_edges*100:.1f}%)")
    else:
        print(f"差距: {gap} (潜在边数为0，无法计算百分比)")
    print()
    
    # 诊断结果
    print("诊断结果:")
    if entity_analysis['entities_with_parent_id'] == 0 and entity_analysis['entities_with_related_entities'] == 0 and entity_analysis['entities_with_module'] == 0:
        print("❌ 数据问题: 实体数据严重不完整")
        print("   - 缺少parent_id字段: 0个实体有parent_id")
        print("   - 缺少related_entities字段: 0个实体有related_entities")
        print("   - 缺少sap_module信息: 0个实体有sap_module")
        print("   说明: 当前124条边是通过其他方式创建的（可能是从描述中提取或LLM发现）")
        print("   建议: 补充实体关系数据（parent_id, related_entities, sap_module）")
    elif entity_analysis['entities_with_module'] == 0:
        print("❌ 数据问题: 实体缺少模块信息（sap_module）")
        print("   建议: 补充实体模块信息")
    elif potential_edges < 200:
        print("❌ 数据问题: 潜在关系数不足200")
        print(f"   当前潜在关系数: {potential_edges}")
        print("   建议: 增加实体数量或补充关系数据")
    elif potential_edges > 0 and gap > potential_edges * 0.3:
        print("⚠️ 技术问题: 关系创建率过低")
        print(f"   关系创建率: {(current_edges/potential_edges*100):.1f}%")
        print("   建议: 检查关系发现服务、构建日志、错误信息")
    else:
        print("✅ 数据和技术基本正常，可能需要优化关系发现算法")
    print()
    
    # 8. 建议
    print("💡 8. 改进建议")
    print("-" * 60)
    if potential_edges < 200:
        print("1. 数据补充:")
        print("   - 增加实体数量（目标: 100+）")
        print("   - 补充parent_id字段")
        print("   - 补充related_entities字段")
        print("   - 补充sap_module和sap_sub_module信息")
    else:
        print("1. 技术优化:")
        print("   - 检查关系发现服务是否正常工作")
        print("   - 检查构建日志中的错误信息")
        print("   - 考虑调整同模块关系限制（从5增加到10-20）")
        print("   - 启用LLM增强关系发现")
        print("   - 检查节点查找和边创建逻辑")
    
    print("2. 关系发现优化:")
    print("   - 考虑提高同模块关系限制（当前: 5）")
    print("   - 启用LLM增强关系发现（use_llm=true）")
    print("   - 优化关系验证逻辑，避免过度严格")
    
    print("3. 数据质量:")
    print("   - 确保实体数据完整（parent_id, related_entities, sap_module）")
    print("   - 确保实体数量足够（建议: 100+）")
    print()
    
    print("=" * 60)
    print("分析完成")
    print("=" * 60)

if __name__ == "__main__":
    main()

