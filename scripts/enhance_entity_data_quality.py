#!/usr/bin/env python3
"""
高质量实体数据完善脚本
确保数据质量，补充parent_id、related_entities、sap_module等关系字段
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

def extract_module_info(entity: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """从实体中提取模块信息（高质量）"""
    name = entity.get("name", "").lower()
    description = (entity.get("description") or "").lower()
    business_def = (entity.get("business_definition") or "").lower()
    text = f"{name} {description} {business_def}"
    
    # MM模块关键词（更精确）
    mm_patterns = [
        (r"\b(mm|material|purchase|procurement|vendor|supplier|inventory|warehouse|stock)\b", "MM"),
        (r"物料|采购|供应商|库存|仓库|仓储", "MM"),
    ]
    
    # SD模块关键词
    sd_patterns = [
        (r"\b(sd|sales|order|customer|delivery|invoice|billing)\b", "SD"),
        (r"销售|订单|客户|发货|发票|开票", "SD"),
    ]
    
    # FI模块关键词
    fi_patterns = [
        (r"\b(fi|finance|accounting|gl|general.ledger|ar|ap|receivable|payable)\b", "FI"),
        (r"财务|会计|总账|应收|应付", "FI"),
    ]
    
    # CO模块关键词
    co_patterns = [
        (r"\b(co|controlling|cost|profit.center|cost.center)\b", "CO"),
        (r"成本|利润中心|成本中心", "CO"),
    ]
    
    module_info = None
    
    # 检查MM模块
    for pattern, module in mm_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            if "采购" in text or "purchase" in text or "procurement" in text:
                module_info = {"module": "MM", "sub_module": "采购管理"}
            elif "库存" in text or "inventory" in text or "warehouse" in text or "stock" in text:
                module_info = {"module": "MM", "sub_module": "库存管理"}
            elif "供应商" in text or "vendor" in text or "supplier" in text:
                module_info = {"module": "MM", "sub_module": "供应商管理"}
            else:
                module_info = {"module": "MM", "sub_module": "物料管理"}
            break
    
    # 检查SD模块
    if not module_info:
        for pattern, module in sd_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                module_info = {"module": "SD", "sub_module": "销售管理"}
                break
    
    # 检查FI模块
    if not module_info:
        for pattern, module in fi_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                module_info = {"module": "FI", "sub_module": "财务管理"}
                break
    
    # 检查CO模块
    if not module_info:
        for pattern, module in co_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                module_info = {"module": "CO", "sub_module": "成本管理"}
                break
    
    return module_info

def find_parent_child_relationships_quality(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """高质量发现父子关系"""
    relationships = []
    
    # 构建实体映射
    entity_map = {e.get("id"): e for e in entities}
    name_to_entity = {e.get("name", "").lower(): e for e in entities}
    
    # 方法1: 基于命名模式（精确匹配）
    patterns = [
        (r"(.+?)_(主数据|master.data)", "parent"),
        (r"(.+?)_(明细|detail|item)", "child"),
        (r"(.+?)_(抬头|header)", "parent"),
        (r"(.+?)_(行项目|line.item)", "child"),
        (r"(.+?)_(主表|master.table)", "parent"),
        (r"(.+?)_(从表|detail.table)", "child"),
    ]
    
    for entity in entities:
        name = entity.get("name", "")
        
        for pattern, rel_type in patterns:
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                parent_name = match.group(1).lower()
                child_entity = entity
                
                # 查找父实体（精确匹配优先）
                if parent_name in name_to_entity:
                    parent_entity = name_to_entity[parent_name]
                    relationships.append({
                        "child_id": child_entity.get("id"),
                        "child_name": child_entity.get("name"),
                        "parent_id": parent_entity.get("id"),
                        "parent_name": parent_entity.get("name"),
                        "confidence": 0.95,
                        "method": "naming_pattern_exact"
                    })
                else:
                    # 模糊匹配
                    for other_name, other_entity in name_to_entity.items():
                        if parent_name in other_name or other_name in parent_name:
                            relationships.append({
                                "child_id": child_entity.get("id"),
                                "child_name": child_entity.get("name"),
                                "parent_id": other_entity.get("id"),
                                "parent_name": other_entity.get("name"),
                                "confidence": 0.8,
                                "method": "naming_pattern_fuzzy"
                            })
                            break
    
    # 方法2: 基于业务定义中的层次关系
    for entity in entities:
        business_def = (entity.get("business_definition") or "").lower()
        description = (entity.get("description") or "").lower()
        text = f"{business_def} {description}"
        
        # 查找"属于"、"包含"等关键词
        if "属于" in text or "belongs to" in text or "part of" in text:
            # 尝试提取父实体名称
            for other_entity in entities:
                if other_entity.get("id") == entity.get("id"):
                    continue
                
                other_name = other_entity.get("name", "").lower()
                if other_name in text:
                    relationships.append({
                        "child_id": entity.get("id"),
                        "child_name": entity.get("name"),
                        "parent_id": other_entity.get("id"),
                        "parent_name": other_entity.get("name"),
                        "confidence": 0.7,
                        "method": "business_definition"
                    })
                    break
    
    # 去重（保留置信度最高的）
    unique_rels = {}
    for rel in relationships:
        key = (rel["child_id"], rel["parent_id"])
        if key not in unique_rels or rel["confidence"] > unique_rels[key]["confidence"]:
            unique_rels[key] = rel
    
    return list(unique_rels.values())

def find_related_entities_quality(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """高质量发现关联关系"""
    relationships = []
    
    # 定义高质量关联关键词对
    related_patterns = [
        # MM模块关联
        (r"\b(material|物料)\b", r"\b(vendor|supplier|供应商)\b", "related_to", 0.9),
        (r"\b(purchase.order|采购订单)\b", r"\b(vendor|supplier|供应商)\b", "related_to", 0.95),
        (r"\b(purchase.order|采购订单)\b", r"\b(material|物料)\b", "related_to", 0.9),
        (r"\b(inventory|库存)\b", r"\b(material|物料)\b", "related_to", 0.9),
        (r"\b(warehouse|仓库)\b", r"\b(material|物料)\b", "related_to", 0.9),
        (r"\b(material.document|物料凭证)\b", r"\b(material|物料)\b", "related_to", 0.9),
        # SD模块关联
        (r"\b(sales.order|销售订单)\b", r"\b(customer|客户)\b", "related_to", 0.95),
        (r"\b(sales.order|销售订单)\b", r"\b(material|物料)\b", "related_to", 0.9),
        (r"\b(delivery|发货)\b", r"\b(sales.order|销售订单)\b", "related_to", 0.9),
        # FI模块关联
        (r"\b(invoice|发票)\b", r"\b(sales.order|销售订单)\b", "related_to", 0.9),
        (r"\b(payment|付款)\b", r"\b(invoice|发票)\b", "related_to", 0.9),
    ]
    
    for entity in entities:
        name = entity.get("name", "").lower()
        description = (entity.get("description", "") or entity.get("business_definition", "")).lower()
        text = f"{name} {description}"
        
        for pattern1, pattern2, rel_type, confidence in related_patterns:
            if re.search(pattern1, text, re.IGNORECASE):
                # 查找匹配pattern2的实体
                for other_entity in entities:
                    if other_entity.get("id") == entity.get("id"):
                        continue
                    
                    other_name = other_entity.get("name", "").lower()
                    other_description = (other_entity.get("description", "") or other_entity.get("business_definition", "")).lower()
                    other_text = f"{other_name} {other_description}"
                    
                    if re.search(pattern2, other_text, re.IGNORECASE):
                        relationships.append({
                            "source_id": entity.get("id"),
                            "source_name": entity.get("name"),
                            "target_id": other_entity.get("id"),
                            "target_name": other_entity.get("name"),
                            "relationship_type": rel_type,
                            "confidence": confidence,
                            "method": "pattern_match"
                        })
    
    return relationships

def enhance_entities_quality(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """高质量完善实体数据"""
    results = {
        "updated_module": 0,
        "updated_parent_id": 0,
        "updated_related_entities": 0,
        "skipped_existing": 0,
        "errors": []
    }
    
    print("\n1. 补充模块信息（高质量）...")
    for entity in entities:
        entity_id = entity.get("id")
        name = entity.get("name", "")
        
        # 检查是否已有模块信息
        metadata = entity.get("extra_metadata") or entity.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        
        if metadata.get("sap_module"):
            results["skipped_existing"] += 1
            continue  # 已有模块信息，跳过
        
        # 提取模块信息
        module_info = extract_module_info(entity)
        if module_info:
            metadata.update(module_info)
            update_data = {"extra_metadata": metadata}
            if update_entity(entity_id, update_data):
                results["updated_module"] += 1
                if results["updated_module"] % 50 == 0:
                    print(f"  已更新 {results['updated_module']} 个实体的模块信息...")
    
    print(f"  ✅ 共更新 {results['updated_module']} 个实体的模块信息（跳过 {results['skipped_existing']} 个已有模块信息的实体）")
    
    print("\n2. 补充parent_id（高质量）...")
    parent_child_rels = find_parent_child_relationships_quality(entities)
    print(f"  发现 {len(parent_child_rels)} 个高质量的父子关系")
    
    for rel in parent_child_rels:
        # 只更新高置信度的关系
        if rel["confidence"] >= 0.7:
            entity = next((e for e in entities if e.get("id") == rel["child_id"]), None)
            if entity and not entity.get("parent_id"):
                update_data = {"parent_id": rel["parent_id"]}
                if update_entity(rel["child_id"], update_data):
                    results["updated_parent_id"] += 1
                    if results["updated_parent_id"] % 5 == 0:
                        print(f"  已更新 {results['updated_parent_id']} 个实体的parent_id...")
    
    print(f"  ✅ 共更新 {results['updated_parent_id']} 个实体的parent_id")
    
    print("\n3. 补充related_entities（高质量）...")
    related_rels = find_related_entities_quality(entities)
    print(f"  发现 {len(related_rels)} 个高质量的关联关系")
    
    # 按source_id分组，只保留高置信度的
    related_by_source = defaultdict(list)
    for rel in related_rels:
        if rel["confidence"] >= 0.8:  # 只保留高置信度的
            related_by_source[rel["source_id"]].append(rel["target_id"])
    
    for source_id, target_ids in related_by_source.items():
        entity = next((e for e in entities if e.get("id") == source_id), None)
        if entity:
            # 获取现有的related_entities
            existing_related = entity.get("related_entities") or []
            if not isinstance(existing_related, list):
                existing_related = []
            
            # 合并新的关联（去重）
            new_related = list(set(existing_related + target_ids))
            
            # 限制关联数量（最多10个，保证质量）
            if len(new_related) > 10:
                new_related = new_related[:10]
            
            update_data = {"related_entities": new_related}
            if update_entity(source_id, update_data):
                results["updated_related_entities"] += 1
                if results["updated_related_entities"] % 5 == 0:
                    print(f"  已更新 {results['updated_related_entities']} 个实体的related_entities...")
    
    print(f"  ✅ 共更新 {results['updated_related_entities']} 个实体的related_entities")
    
    return results

def main():
    print("=" * 60)
    print("高质量实体数据完善脚本")
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
    print("2. 开始高质量完善实体数据...")
    results = enhance_entities_quality(entities)
    print()
    
    # 3. 显示结果
    print("=" * 60)
    print("完善结果")
    print("=" * 60)
    print(f"更新模块信息: {results['updated_module']}")
    print(f"更新parent_id: {results['updated_parent_id']}")
    print(f"更新related_entities: {results['updated_related_entities']}")
    print(f"跳过已有数据: {results['skipped_existing']}")
    if results['errors']:
        print(f"错误数: {len(results['errors'])}")
    print()
    
    print("=" * 60)
    print("完成")
    print("=" * 60)

if __name__ == "__main__":
    main()

