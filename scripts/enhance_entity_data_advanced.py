#!/usr/bin/env python3
"""
高级实体数据完善脚本
使用更智能的方法补充实体数据
"""

import requests
import json
import re
from typing import List, Dict, Any, Optional
from collections import defaultdict

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

def extract_module_from_text(text: str) -> Optional[Dict[str, str]]:
    """从文本中提取模块信息"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    # MM模块关键词
    mm_keywords = ["mm", "物料", "采购", "库存", "仓库", "供应商", "采购订单", "物料主数据"]
    # SD模块关键词
    sd_keywords = ["sd", "销售", "订单", "客户", "发货", "发票"]
    # FI模块关键词
    fi_keywords = ["fi", "财务", "会计", "总账", "应收", "应付", "成本"]
    # CO模块关键词
    co_keywords = ["co", "成本", "成本中心", "利润中心", "内部订单"]
    
    module_info = None
    
    if any(kw in text_lower for kw in mm_keywords):
        if "采购" in text_lower or "purchase" in text_lower:
            module_info = {"module": "MM", "sub_module": "采购管理"}
        elif "库存" in text_lower or "库存" in text_lower or "warehouse" in text_lower:
            module_info = {"module": "MM", "sub_module": "库存管理"}
        elif "供应商" in text_lower or "vendor" in text_lower:
            module_info = {"module": "MM", "sub_module": "供应商管理"}
        else:
            module_info = {"module": "MM", "sub_module": "物料管理"}
    elif any(kw in text_lower for kw in sd_keywords):
        module_info = {"module": "SD", "sub_module": "销售管理"}
    elif any(kw in text_lower for kw in fi_keywords):
        module_info = {"module": "FI", "sub_module": "财务管理"}
    elif any(kw in text_lower for kw in co_keywords):
        module_info = {"module": "CO", "sub_module": "成本管理"}
    
    return module_info

def find_parent_child_relationships(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """发现父子关系"""
    relationships = []
    
    # 方法1: 基于命名模式
    parent_map = {}
    child_entities = []
    
    for entity in entities:
        name = entity.get("name", "")
        
        # 匹配模式：XXX_主数据、XXX_明细、XXX_抬头、XXX_行项目等
        pattern = r"(.+?)_(主数据|明细|抬头|行项目|主表|从表|header|item|detail)"
        match = re.match(pattern, name, re.IGNORECASE)
        if match:
            parent_name = match.group(1)
            child_entities.append({
                "entity": entity,
                "parent_name": parent_name
            })
        else:
            # 可能是父实体
            parent_map[name.lower()] = entity
    
    # 匹配父子关系
    for child_info in child_entities:
        parent_name = child_info["parent_name"].lower()
        child_entity = child_info["entity"]
        
        # 精确匹配
        if parent_name in parent_map:
            relationships.append({
                "child_id": child_entity.get("id"),
                "child_name": child_entity.get("name"),
                "parent_id": parent_map[parent_name].get("id"),
                "parent_name": parent_map[parent_name].get("name"),
                "method": "naming_pattern"
            })
        else:
            # 模糊匹配
            for parent_name_key, parent_entity in parent_map.items():
                if parent_name in parent_name_key or parent_name_key in parent_name:
                    relationships.append({
                        "child_id": child_entity.get("id"),
                        "child_name": child_entity.get("name"),
                        "parent_id": parent_entity.get("id"),
                        "parent_name": parent_entity.get("name"),
                        "method": "fuzzy_match"
                    })
                    break
    
    return relationships

def find_related_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """发现关联关系（基于关键词）"""
    relationships = []
    
    # 定义关联关键词对
    related_keywords = [
        ("物料", "供应商", "related_to"),
        ("采购订单", "供应商", "related_to"),
        ("采购订单", "物料", "related_to"),
        ("库存", "物料", "related_to"),
        ("仓库", "物料", "related_to"),
    ]
    
    entity_map = {e.get("id"): e for e in entities}
    
    for entity in entities:
        name = entity.get("name", "").lower()
        description = (entity.get("description", "") or entity.get("business_definition", "")).lower()
        text = f"{name} {description}"
        
        for kw1, kw2, rel_type in related_keywords:
            if kw1 in text:
                # 查找包含kw2的实体
                for other_entity in entities:
                    if other_entity.get("id") == entity.get("id"):
                        continue
                    
                    other_name = other_entity.get("name", "").lower()
                    other_description = (other_entity.get("description", "") or other_entity.get("business_definition", "")).lower()
                    other_text = f"{other_name} {other_description}"
                    
                    if kw2 in other_text:
                        relationships.append({
                            "source_id": entity.get("id"),
                            "source_name": entity.get("name"),
                            "target_id": other_entity.get("id"),
                            "target_name": other_entity.get("name"),
                            "relationship_type": rel_type,
                            "method": "keyword_match"
                        })
    
    return relationships

def enhance_entities_advanced(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """高级实体数据完善"""
    results = {
        "updated_module": 0,
        "updated_parent_id": 0,
        "updated_related_entities": 0,
        "errors": []
    }
    
    print("\n1. 补充模块信息...")
    for entity in entities:
        entity_id = entity.get("id")
        name = entity.get("name", "")
        
        # 检查是否已有模块信息
        metadata = entity.get("extra_metadata") or entity.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        
        if metadata.get("sap_module"):
            continue  # 已有模块信息，跳过
        
        # 从描述和业务定义中提取模块信息
        description = entity.get("description", "")
        business_def = entity.get("business_definition", "")
        text = f"{name} {description} {business_def}"
        
        module_info = extract_module_from_text(text)
        if module_info:
            metadata.update(module_info)
            update_data = {"extra_metadata": metadata}
            if update_entity(entity_id, update_data):
                results["updated_module"] += 1
                if results["updated_module"] % 10 == 0:
                    print(f"  已更新 {results['updated_module']} 个实体的模块信息...")
    
    print(f"  ✅ 共更新 {results['updated_module']} 个实体的模块信息")
    
    print("\n2. 补充parent_id...")
    parent_child_rels = find_parent_child_relationships(entities)
    print(f"  发现 {len(parent_child_rels)} 个潜在的父子关系")
    
    for rel in parent_child_rels:
        update_data = {"parent_id": rel["parent_id"]}
        if update_entity(rel["child_id"], update_data):
            results["updated_parent_id"] += 1
            if results["updated_parent_id"] % 5 == 0:
                print(f"  已更新 {results['updated_parent_id']} 个实体的parent_id...")
    
    print(f"  ✅ 共更新 {results['updated_parent_id']} 个实体的parent_id")
    
    print("\n3. 补充related_entities...")
    related_rels = find_related_entities(entities)
    print(f"  发现 {len(related_rels)} 个潜在的关联关系")
    
    # 按source_id分组
    related_by_source = defaultdict(list)
    for rel in related_rels:
        related_by_source[rel["source_id"]].append(rel["target_id"])
    
    for source_id, target_ids in related_by_source.items():
        entity = next((e for e in entities if e.get("id") == source_id), None)
        if entity:
            # 获取现有的related_entities
            existing_related = entity.get("related_entities") or []
            if not isinstance(existing_related, list):
                existing_related = []
            
            # 合并新的关联
            new_related = list(set(existing_related + target_ids))
            
            update_data = {"related_entities": new_related}
            if update_entity(source_id, update_data):
                results["updated_related_entities"] += 1
                if results["updated_related_entities"] % 5 == 0:
                    print(f"  已更新 {results['updated_related_entities']} 个实体的related_entities...")
    
    print(f"  ✅ 共更新 {results['updated_related_entities']} 个实体的related_entities")
    
    return results

def main():
    print("=" * 60)
    print("高级实体数据完善脚本")
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
    
    # 2. 完善实体数据
    print("2. 开始完善实体数据...")
    results = enhance_entities_advanced(entities)
    print()
    
    # 3. 显示结果
    print("=" * 60)
    print("完善结果")
    print("=" * 60)
    print(f"更新模块信息: {results['updated_module']}")
    print(f"更新parent_id: {results['updated_parent_id']}")
    print(f"更新related_entities: {results['updated_related_entities']}")
    if results['errors']:
        print(f"错误数: {len(results['errors'])}")
    print()
    
    print("=" * 60)
    print("完成")
    print("=" * 60)

if __name__ == "__main__":
    main()





