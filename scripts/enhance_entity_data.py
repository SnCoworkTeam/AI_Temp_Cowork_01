#!/usr/bin/env python3
"""
完善实体数据脚本
为实体补充parent_id、related_entities、sap_module等关系字段
"""

import requests
import json
from typing import List, Dict, Any, Optional

METADATA_SERVICE_URL = "http://localhost:8005"

def get_entities(limit: int = 1000) -> List[Dict[str, Any]]:
    """获取所有实体"""
    all_entities = []
    skip = 0
    page_limit = 100
    
    while len(all_entities) < limit:
        url = f"{METADATA_SERVICE_URL}/api/business-entities?skip={skip}&limit={page_limit}"
        r = requests.get(url, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                page_entities = data
            elif isinstance(data, dict):
                page_entities = data.get('entities', []) or data.get('data', [])
            else:
                page_entities = []
            
            if not page_entities:
                break
            
            all_entities.extend(page_entities)
            
            if len(page_entities) < page_limit:
                break
            
            skip += page_limit
        else:
            break
    
    return all_entities[:limit]

def update_entity(entity_id: int, update_data: Dict[str, Any]) -> bool:
    """更新实体"""
    try:
        url = f"{METADATA_SERVICE_URL}/api/business-entities/{entity_id}"
        r = requests.put(url, json=update_data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"  更新实体 {entity_id} 失败: {e}")
        return False

def analyze_entities_for_enhancement(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析实体，识别可以补充的关系"""
    analysis = {
        "entities_with_description": 0,
        "entities_with_business_definition": 0,
        "entities_with_name_pattern": 0,
        "potential_parent_child": [],
        "potential_module_mapping": {}
    }
    
    # 分析实体名称模式
    parent_entities = {}  # 可能的父实体
    child_entities = []   # 可能的子实体
    
    for entity in entities:
        name = entity.get("name", "")
        description = entity.get("description", "")
        business_def = entity.get("business_definition", "")
        
        if description:
            analysis["entities_with_description"] += 1
        if business_def:
            analysis["entities_with_business_definition"] += 1
        
        # 检查命名模式（如：XXX_主数据、XXX_明细）
        import re
        pattern = r"(.+)_(主数据|明细|抬头|行项目|主表|从表)"
        match = re.match(pattern, name)
        if match:
            analysis["entities_with_name_pattern"] += 1
            parent_name = match.group(1)
            child_entities.append({
                "entity": entity,
                "parent_name": parent_name
            })
        else:
            # 可能是父实体
            parent_entities[name] = entity
        
        # 从描述中提取模块信息
        text = (description or business_def or "").lower()
        if "mm" in text or "物料" in text or "采购" in text:
            analysis["potential_module_mapping"][entity.get("id")] = {
                "module": "MM",
                "sub_module": "采购管理" if "采购" in text else "物料管理"
            }
        elif "sd" in text or "销售" in text:
            analysis["potential_module_mapping"][entity.get("id")] = {
                "module": "SD",
                "sub_module": "销售管理"
            }
        elif "fi" in text or "财务" in text:
            analysis["potential_module_mapping"][entity.get("id")] = {
                "module": "FI",
                "sub_module": "财务管理"
            }
    
    # 匹配父子关系
    for child_info in child_entities:
        parent_name = child_info["parent_name"]
        child_entity = child_info["entity"]
        
        # 查找父实体
        for parent_name_key, parent_entity in parent_entities.items():
            if parent_name_key == parent_name or parent_name in parent_name_key:
                analysis["potential_parent_child"].append({
                    "child_id": child_entity.get("id"),
                    "child_name": child_entity.get("name"),
                    "parent_id": parent_entity.get("id"),
                    "parent_name": parent_entity.get("name")
                })
                break
    
    return analysis

def enhance_entities(entities: List[Dict[str, Any]], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """完善实体数据"""
    results = {
        "updated_parent_id": 0,
        "updated_module": 0,
        "updated_related_entities": 0,
        "errors": []
    }
    
    # 1. 更新父子关系
    print("\n1. 更新父子关系...")
    for rel in analysis["potential_parent_child"]:
        child_id = rel["child_id"]
        parent_id = rel["parent_id"]
        
        entity = next((e for e in entities if e.get("id") == child_id), None)
        if entity:
            update_data = {
                "parent_id": parent_id
            }
            if update_entity(child_id, update_data):
                results["updated_parent_id"] += 1
                print(f"  ✅ {rel['child_name']} -> {rel['parent_name']}")
            else:
                results["errors"].append(f"更新父子关系失败: {rel['child_name']}")
    
    # 2. 更新模块信息
    print("\n2. 更新模块信息...")
    for entity_id, module_info in analysis["potential_module_mapping"].items():
        entity = next((e for e in entities if e.get("id") == entity_id), None)
        if entity:
            metadata = entity.get("extra_metadata") or entity.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}
            
            metadata.update({
                "sap_module": module_info["module"],
                "sap_sub_module": module_info["sub_module"]
            })
            
            update_data = {
                "extra_metadata": metadata
            }
            if update_entity(entity_id, update_data):
                results["updated_module"] += 1
                print(f"  ✅ {entity.get('name')} -> {module_info['module']}/{module_info['sub_module']}")
            else:
                results["errors"].append(f"更新模块信息失败: {entity.get('name')}")
    
    # 3. 基于描述发现关联关系（简化版，实际应该用LLM）
    print("\n3. 发现关联关系（基于关键词）...")
    # 这里可以扩展，使用LLM或更复杂的逻辑
    # 暂时跳过，因为需要更复杂的分析
    
    return results

def main():
    print("=" * 60)
    print("完善实体数据脚本")
    print("=" * 60)
    print()
    
    # 1. 获取所有实体
    print("1. 获取实体数据...")
    entities = get_entities(limit=1000)
    print(f"   获取到 {len(entities)} 个实体")
    print()
    
    if not entities:
        print("❌ 无法获取实体数据")
        return
    
    # 2. 分析实体
    print("2. 分析实体数据...")
    analysis = analyze_entities_for_enhancement(entities)
    print(f"   有描述的实体: {analysis['entities_with_description']}")
    print(f"   有业务定义的实体: {analysis['entities_with_business_definition']}")
    print(f"   符合命名模式的实体: {analysis['entities_with_name_pattern']}")
    print(f"   潜在的父子关系: {len(analysis['potential_parent_child'])}")
    print(f"   潜在的模块映射: {len(analysis['potential_module_mapping'])}")
    print()
    
    # 3. 完善实体数据
    print("3. 开始完善实体数据...")
    results = enhance_entities(entities, analysis)
    print()
    
    # 4. 显示结果
    print("=" * 60)
    print("完善结果")
    print("=" * 60)
    print(f"更新parent_id: {results['updated_parent_id']}")
    print(f"更新模块信息: {results['updated_module']}")
    print(f"更新关联关系: {results['updated_related_entities']}")
    if results['errors']:
        print(f"错误数: {len(results['errors'])}")
        for error in results['errors'][:5]:
            print(f"  - {error}")
    print()
    
    print("=" * 60)
    print("完成")
    print("=" * 60)

if __name__ == "__main__":
    main()




