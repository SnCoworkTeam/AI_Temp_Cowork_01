#!/usr/bin/env python3
"""
分析数据质量
检查实体数据的完整性和准确性
"""

import requests
import json
from typing import List, Dict, Any
from collections import defaultdict

METADATA_SERVICE_URL = "http://localhost:8005"
KNOWLEDGE_BASE_URL = "http://localhost:8004"

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

def analyze_data_quality(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析数据质量"""
    analysis = {
        "total_entities": len(entities),
        "completeness": {},
        "accuracy": {},
        "issues": []
    }
    
    # 完整性分析
    completeness = {
        "has_name": 0,
        "has_display_name": 0,
        "has_description": 0,
        "has_business_definition": 0,
        "has_module_info": 0,
        "has_parent_id": 0,
        "has_related_entities": 0,
        "has_tags": 0,
        "has_business_rules": 0,
        "has_data_dictionary": 0,
    }
    
    # 准确性分析
    accuracy_issues = []
    
    for entity in entities:
        # 检查完整性
        if entity.get("name"):
            completeness["has_name"] += 1
        if entity.get("display_name"):
            completeness["has_display_name"] += 1
        if entity.get("description"):
            completeness["has_description"] += 1
        if entity.get("business_definition"):
            completeness["has_business_definition"] += 1
        
        metadata = entity.get("extra_metadata") or entity.get("metadata")
        if metadata:
            if isinstance(metadata, dict) and metadata.get("sap_module"):
                completeness["has_module_info"] += 1
            elif isinstance(metadata, str):
                # 尝试解析JSON字符串
                try:
                    metadata_dict = json.loads(metadata)
                    if isinstance(metadata_dict, dict) and metadata_dict.get("sap_module"):
                        completeness["has_module_info"] += 1
                except:
                    pass
        
        if entity.get("parent_id"):
            completeness["has_parent_id"] += 1
        if entity.get("related_entities"):
            completeness["has_related_entities"] += 1
        if entity.get("tags"):
            completeness["has_tags"] += 1
        if entity.get("business_rules"):
            completeness["has_business_rules"] += 1
        if entity.get("data_dictionary"):
            completeness["has_data_dictionary"] += 1
        
        # 检查准确性
        name = entity.get("name", "")
        description = entity.get("description", "")
        business_def = entity.get("business_definition", "")
        
        # 检查描述是否为空或太短
        if not description or len(description.strip()) < 10:
            accuracy_issues.append({
                "entity_id": entity.get("id"),
                "entity_name": name,
                "issue": "description_too_short_or_empty",
                "severity": "medium"
            })
        
        # 检查业务定义是否为空
        if not business_def:
            accuracy_issues.append({
                "entity_id": entity.get("id"),
                "entity_name": name,
                "issue": "missing_business_definition",
                "severity": "high"
            })
        
        # 检查模块信息是否准确
        if isinstance(metadata, dict):
            module = metadata.get("sap_module")
            if module and module not in ["MM", "SD", "FI", "CO", "PP", "HR", "OTHER"]:
                accuracy_issues.append({
                    "entity_id": entity.get("id"),
                    "entity_name": name,
                    "issue": "invalid_module",
                    "severity": "medium",
                    "details": f"Module: {module}"
                })
    
    # 计算完整性百分比
    total = len(entities)
    completeness_pct = {}
    for key, count in completeness.items():
        completeness_pct[key] = {
            "count": count,
            "percentage": (count / total * 100) if total > 0 else 0
        }
    
    analysis["completeness"] = completeness_pct
    analysis["accuracy"]["issues"] = accuracy_issues
    analysis["accuracy"]["total_issues"] = len(accuracy_issues)
    
    return analysis

def get_knowledge_base_documents() -> List[Dict[str, Any]]:
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

def main():
    print("=" * 60)
    print("数据质量分析")
    print("=" * 60)
    print()
    
    # 1. 获取实体数据
    print("1. 获取实体数据...")
    entities = get_entities(limit=1000)
    print(f"   获取到 {len(entities)} 个实体")
    print()
    
    # 2. 分析数据质量
    print("2. 分析数据质量...")
    analysis = analyze_data_quality(entities)
    print()
    
    # 3. 显示完整性分析
    print("3. 数据完整性分析:")
    print("-" * 60)
    for key, info in analysis["completeness"].items():
        pct = info["percentage"]
        status = "✅" if pct >= 80 else "⚠️" if pct >= 50 else "❌"
        print(f"  {status} {key}: {info['count']} ({pct:.1f}%)")
    print()
    
    # 4. 显示准确性分析
    print("4. 数据准确性问题:")
    print("-" * 60)
    issues = analysis["accuracy"]["issues"]
    if issues:
        # 按严重程度分组
        high_issues = [i for i in issues if i["severity"] == "high"]
        medium_issues = [i for i in issues if i["severity"] == "medium"]
        low_issues = [i for i in issues if i["severity"] == "low"]
        
        print(f"  高严重度问题: {len(high_issues)}")
        for issue in high_issues[:5]:
            print(f"    - {issue['entity_name']}: {issue['issue']}")
        
        print(f"  中严重度问题: {len(medium_issues)}")
        for issue in medium_issues[:5]:
            print(f"    - {issue['entity_name']}: {issue['issue']}")
        
        if len(high_issues) > 5 or len(medium_issues) > 5:
            print(f"  ... 还有更多问题，总计 {len(issues)} 个")
    else:
        print("  ✅ 未发现准确性问题")
    print()
    
    # 5. 检查知识库文档
    print("5. 检查知识库文档...")
    documents = get_knowledge_base_documents()
    print(f"   知识库文档数: {len(documents)}")
    print()
    
    # 6. 总结和建议
    print("=" * 60)
    print("数据质量总结")
    print("=" * 60)
    
    # 计算总体完整性
    key_fields = ["has_name", "has_description", "has_business_definition", "has_module_info"]
    avg_completeness = sum(analysis["completeness"][k]["percentage"] for k in key_fields) / len(key_fields)
    
    print(f"总体完整性: {avg_completeness:.1f}%")
    print(f"准确性问题: {analysis['accuracy']['total_issues']} 个")
    print()
    
    print("改进建议:")
    if avg_completeness < 80:
        print("  1. 补充缺失的描述和业务定义")
        print("  2. 补充模块信息")
        print("  3. 建立数据质量检查机制")
    
    if analysis["accuracy"]["total_issues"] > 0:
        print("  4. 修复准确性问题")
        print("  5. 建立数据验证规则")
    
    if len(documents) < 100:
        print("  6. 补充知识库文档（可以从网上抓取相关数据）")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()

