#!/usr/bin/env python3
"""
分析现有数据是否具备演示条件
评估数据质量、完整性，设计演示场景
"""

import requests
import json
from typing import List, Dict, Any
from collections import defaultdict

METADATA_SERVICE_URL = "http://localhost:8005"
KNOWLEDGE_BASE_URL = "http://localhost:8004"

def get_kg_stats() -> Dict[str, Any]:
    """获取知识图谱统计"""
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/knowledge-graph/stats", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get('statistics', {})
        return {}
    except:
        return {}

def get_entities_sample(limit: int = 100) -> List[Dict[str, Any]]:
    """获取实体样本"""
    try:
        r = requests.get(f"{METADATA_SERVICE_URL}/api/business-entities?limit={limit}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get('entities', []) or data.get('data', [])
        return []
    except:
        return []

def get_knowledge_base_docs() -> List[Dict[str, Any]]:
    """获取知识库文档"""
    try:
        r = requests.get(f"{KNOWLEDGE_BASE_URL}/api/documents?limit=100", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                return data.get('documents', []) or data.get('data', [])
            elif isinstance(data, list):
                return data
        return []
    except:
        return []

def analyze_demo_readiness():
    """分析演示就绪度"""
    print("=" * 60)
    print("演示就绪度分析")
    print("=" * 60)
    print()
    
    # 1. 知识图谱数据
    print("1. 知识图谱数据评估")
    print("-" * 60)
    kg_stats = get_kg_stats()
    edges = kg_stats.get('total_edges', 0)
    nodes = kg_stats.get('total_nodes', 0)
    edges_by_type = kg_stats.get('edges_by_type', {})
    
    print(f"节点数: {nodes}")
    print(f"边数: {edges}")
    print(f"边类型分布: {edges_by_type}")
    
    # 评估
    kg_score = 0
    if edges >= 200:
        kg_score += 30
        print("  ✅ 边数达标（30分）")
    elif edges >= 150:
        kg_score += 20
        print("  ⚠️ 边数接近达标（20分）")
    else:
        print("  ❌ 边数不足（0分）")
    
    if nodes >= 500:
        kg_score += 20
        print("  ✅ 节点数充足（20分）")
    else:
        print("  ⚠️ 节点数一般（10分）")
        kg_score += 10
    
    if edges_by_type.get('related_to', 0) >= 100:
        kg_score += 20
        print("  ✅ 关联关系充足（20分）")
    else:
        print("  ⚠️ 关联关系一般（10分）")
        kg_score += 10
    
    if edges_by_type.get('parent_of', 0) >= 5:
        kg_score += 15
        print("  ✅ 层次关系存在（15分）")
    else:
        print("  ⚠️ 层次关系较少（5分）")
        kg_score += 5
    
    if kg_stats.get('edges_by_type', {}).get('mentions', 0) > 0:
        kg_score += 15
        print("  ✅ 文档关联存在（15分）")
    else:
        print("  ⚠️ 文档关联缺失（0分）")
    
    print(f"知识图谱得分: {kg_score}/100")
    print()
    
    # 2. 实体数据质量
    print("2. 实体数据质量评估")
    print("-" * 60)
    entities = get_entities_sample(limit=100)
    
    if not entities:
        print("  ❌ 无法获取实体数据")
        entity_score = 0
    else:
        entity_score = 0
        
        # 检查关键字段
        has_desc = sum(1 for e in entities if e.get("description") and len(e.get("description", "")) > 50)
        has_business_def = sum(1 for e in entities if e.get("business_definition"))
        
        # 检查模块信息（需要处理多种格式）
        has_module = 0
        for e in entities:
            metadata = e.get("extra_metadata") or e.get("metadata")
            if metadata:
                if isinstance(metadata, dict) and metadata.get("sap_module"):
                    has_module += 1
                elif isinstance(metadata, str):
                    try:
                        metadata_dict = json.loads(metadata)
                        if isinstance(metadata_dict, dict) and metadata_dict.get("sap_module"):
                            has_module += 1
                    except:
                        pass
        
        has_parent = sum(1 for e in entities if e.get("parent_id"))
        has_related = sum(1 for e in entities if e.get("related_entities"))
        
        desc_pct = has_desc / len(entities) * 100
        business_def_pct = has_business_def / len(entities) * 100
        module_pct = has_module / len(entities) * 100
        parent_pct = has_parent / len(entities) * 100
        related_pct = has_related / len(entities) * 100
        
        print(f"样本实体数: {len(entities)}")
        print(f"有描述（>50字符）: {has_desc} ({desc_pct:.1f}%)")
        print(f"有业务定义: {has_business_def} ({business_def_pct:.1f}%)")
        print(f"有模块信息: {has_module} ({module_pct:.1f}%)")
        print(f"有parent_id: {has_parent} ({parent_pct:.1f}%)")
        print(f"有related_entities: {has_related} ({related_pct:.1f}%)")
        
        # 评分
        if desc_pct >= 80:
            entity_score += 20
            print("  ✅ 描述完整性高（20分）")
        elif desc_pct >= 50:
            entity_score += 10
            print("  ⚠️ 描述完整性一般（10分）")
        
        if business_def_pct >= 80:
            entity_score += 20
            print("  ✅ 业务定义完整性高（20分）")
        elif business_def_pct >= 50:
            entity_score += 10
            print("  ⚠️ 业务定义完整性一般（10分）")
        
        if module_pct >= 50:
            entity_score += 20
            print("  ✅ 模块信息充足（20分）")
        elif module_pct >= 30:
            entity_score += 10
            print("  ⚠️ 模块信息一般（10分）")
        
        if parent_pct >= 5:
            entity_score += 20
            print("  ✅ 层次关系充足（20分）")
        elif parent_pct >= 2:
            entity_score += 10
            print("  ⚠️ 层次关系较少（10分）")
        
        if related_pct >= 10:
            entity_score += 20
            print("  ✅ 关联关系充足（20分）")
        elif related_pct >= 5:
            entity_score += 10
            print("  ⚠️ 关联关系较少（10分）")
    
    print(f"实体数据得分: {entity_score}/100")
    print()
    
    # 3. 知识库文档
    print("3. 知识库文档评估")
    print("-" * 60)
    docs = get_knowledge_base_docs()
    doc_count = len(docs)
    
    print(f"文档数: {doc_count}")
    
    doc_score = 0
    if doc_count >= 50:
        doc_score = 100
        print("  ✅ 文档充足（100分）")
    elif doc_count >= 20:
        doc_score = 70
        print("  ⚠️ 文档一般（70分）")
    elif doc_count >= 10:
        doc_score = 40
        print("  ⚠️ 文档较少（40分）")
    else:
        print("  ❌ 文档不足（0分）")
    
    print(f"知识库文档得分: {doc_score}/100")
    print()
    
    # 4. 业务场景数据
    print("4. 业务场景数据评估")
    print("-" * 60)
    
    # 检查是否有SAP MM相关实体
    mm_entities = []
    for entity in entities:
        metadata = entity.get("extra_metadata") or entity.get("metadata")
        if metadata:
            if isinstance(metadata, dict) and metadata.get("sap_module") == "MM":
                mm_entities.append(entity)
            elif isinstance(metadata, str):
                try:
                    metadata_dict = json.loads(metadata)
                    if isinstance(metadata_dict, dict) and metadata_dict.get("sap_module") == "MM":
                        mm_entities.append(entity)
                except:
                    pass
    
    # 检查关键业务实体
    key_entities = ["material", "purchase_order", "vendor", "inventory", "warehouse"]
    found_key_entities = []
    for entity in entities:
        name = entity.get("name", "").lower()
        for key in key_entities:
            if key in name:
                found_key_entities.append(entity.get("name"))
                break
    
    print(f"SAP MM相关实体: {len(mm_entities)}")
    print(f"关键业务实体: {len(found_key_entities)}")
    for name in found_key_entities[:5]:
        print(f"  - {name}")
    
    scenario_score = 0
    if len(mm_entities) >= 50:
        scenario_score += 30
        print("  ✅ MM实体充足（30分）")
    elif len(mm_entities) >= 20:
        scenario_score += 15
        print("  ⚠️ MM实体一般（15分）")
    
    if len(found_key_entities) >= 5:
        scenario_score += 30
        print("  ✅ 关键实体齐全（30分）")
    elif len(found_key_entities) >= 3:
        scenario_score += 15
        print("  ⚠️ 关键实体部分（15分）")
    
    # 检查是否有完整的业务流程数据
    if edges >= 200 and len(mm_entities) >= 20:
        scenario_score += 40
        print("  ✅ 业务流程数据完整（40分）")
    elif edges >= 150:
        scenario_score += 20
        print("  ⚠️ 业务流程数据一般（20分）")
    
    print(f"业务场景得分: {scenario_score}/100")
    print()
    
    # 5. 综合评估
    print("=" * 60)
    print("综合评估")
    print("=" * 60)
    
    total_score = (kg_score * 0.3 + entity_score * 0.3 + doc_score * 0.2 + scenario_score * 0.2)
    
    print(f"知识图谱: {kg_score}/100 (权重30%)")
    print(f"实体数据: {entity_score}/100 (权重30%)")
    print(f"知识库文档: {doc_score}/100 (权重20%)")
    print(f"业务场景: {scenario_score}/100 (权重20%)")
    print()
    print(f"总分: {total_score:.1f}/100")
    print()
    
    # 演示就绪度判断
    if total_score >= 80:
        readiness = "✅ 完全就绪"
        recommendation = "可以进行完整演示"
    elif total_score >= 60:
        readiness = "⚠️ 基本就绪"
        recommendation = "可以进行基本演示，但建议补充数据"
    elif total_score >= 40:
        readiness = "⚠️ 部分就绪"
        recommendation = "可以进行简单演示，需要补充关键数据"
    else:
        readiness = "❌ 未就绪"
        recommendation = "需要大量补充数据后才能演示"
    
    print(f"演示就绪度: {readiness}")
    print(f"建议: {recommendation}")
    print()
    
    # 6. 演示场景设计
    print("=" * 60)
    print("演示场景设计")
    print("=" * 60)
    print()
    
    scenarios = []
    
    # 场景1: 知识图谱查询
    if edges >= 200 and nodes >= 500:
        scenarios.append({
            "name": "知识图谱查询和可视化",
            "description": "展示知识图谱的结构、关系和查询能力",
            "features": [
                "知识图谱统计展示",
                "实体关系查询",
                "知识图谱可视化",
                "关系路径查询"
            ],
            "readiness": "✅ 就绪" if total_score >= 60 else "⚠️ 部分就绪"
        })
    
    # 场景2: 业务实体查询
    if len(mm_entities) >= 20:
        scenarios.append({
            "name": "SAP MM业务实体查询",
            "description": "查询SAP MM模块的业务实体及其关系",
            "features": [
                "物料主数据查询",
                "采购订单查询",
                "供应商信息查询",
                "实体关系展示"
            ],
            "readiness": "✅ 就绪" if len(mm_entities) >= 50 else "⚠️ 部分就绪"
        })
    
    # 场景3: 统一搜索
    if doc_count >= 10:
        scenarios.append({
            "name": "统一搜索演示",
            "description": "展示跨服务的统一搜索能力",
            "features": [
                "关键词搜索",
                "向量搜索",
                "结果融合和排序",
                "答案溯源"
            ],
            "readiness": "✅ 就绪" if doc_count >= 20 else "⚠️ 部分就绪"
        })
    
    # 场景4: 业务场景端到端
    if len(found_key_entities) >= 5 and edges >= 200:
        scenarios.append({
            "name": "采购订单状态追踪（端到端）",
            "description": "完整的业务场景：从查询采购订单到获取关联信息",
            "features": [
                "采购订单基本信息",
                "供应商信息",
                "物料信息",
                "收货状态",
                "发票状态",
                "相关文档"
            ],
            "readiness": "✅ 就绪" if total_score >= 70 else "⚠️ 部分就绪"
        })
    
    # 场景5: 智能推荐
    if edges >= 200 and len(mm_entities) >= 20:
        scenarios.append({
            "name": "智能实体推荐",
            "description": "基于知识图谱的智能推荐",
            "features": [
                "相关实体推荐",
                "基于关系的推荐",
                "业务场景推荐"
            ],
            "readiness": "✅ 就绪" if total_score >= 60 else "⚠️ 部分就绪"
        })
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']} - {scenario['readiness']}")
        print(f"   描述: {scenario['description']}")
        print(f"   功能点:")
        for feature in scenario['features']:
            print(f"     - {feature}")
        print()
    
    if not scenarios:
        print("⚠️ 当前数据不足以支持演示场景")
        print("建议:")
        print("  1. 补充更多业务实体数据")
        print("  2. 补充知识库文档")
        print("  3. 建立更多实体关系")
    
    print("=" * 60)
    
    return {
        "total_score": total_score,
        "readiness": readiness,
        "recommendation": recommendation,
        "scenarios": scenarios
    }

if __name__ == "__main__":
    analyze_demo_readiness()

