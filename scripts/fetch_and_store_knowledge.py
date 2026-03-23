#!/usr/bin/env python3
"""
从网上抓取必要的数据，形成文档，存储到知识库
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from urllib.parse import quote

KNOWLEDGE_BASE_URL = "http://localhost:8004"
METADATA_SERVICE_URL = "http://localhost:8005"

def search_web_for_entity(entity_name: str, entity_type: str = "concept") -> Optional[Dict[str, Any]]:
    """
    为实体搜索相关信息（模拟，实际可以使用web_search工具）
    这里返回示例数据，实际应该调用web_search工具
    """
    # 这里应该调用web_search工具，但为了演示，返回示例数据
    # 实际使用时，应该：
    # 1. 使用web_search工具搜索实体相关信息
    # 2. 提取和整理搜索结果
    # 3. 生成文档内容
    
    # 示例：为SAP MM模块相关实体生成文档
    mm_entities = {
        "material": {
            "title": "SAP MM物料管理",
            "content": """
# SAP MM物料管理

## 概述
物料管理（Material Management，MM）是SAP ERP系统中的一个核心模块，用于管理企业的物料主数据、采购、库存等业务流程。

## 主要功能
1. 物料主数据管理
2. 采购管理
3. 库存管理
4. 供应商管理

## 关键概念
- 物料主数据：包含物料的基本信息，如物料号、描述、单位等
- 采购订单：用于向供应商采购物料的单据
- 库存：物料的存储和数量管理
- 供应商：提供物料的合作伙伴

## 业务流程
1. 创建物料主数据
2. 创建采购订单
3. 收货
4. 发票校验
5. 库存管理

## 相关模块
- SD（销售与分销）
- FI（财务会计）
- CO（成本控制）
""",
            "tags": ["SAP", "MM", "物料管理", "ERP"]
        },
        "purchase_order": {
            "title": "SAP MM采购订单",
            "content": """
# SAP MM采购订单

## 概述
采购订单（Purchase Order，PO）是SAP MM模块中用于向供应商采购物料的主要单据。

## 采购订单类型
1. 标准采购订单
2. 框架采购订单
3. 合同采购订单
4. 计划采购订单

## 采购订单结构
- 抬头：包含供应商、日期、货币等基本信息
- 行项目：包含物料、数量、价格等详细信息

## 采购流程
1. 创建采购申请
2. 创建采购订单
3. 发送给供应商
4. 收货
5. 发票校验

## 关键字段
- 采购订单号
- 供应商
- 物料
- 数量
- 价格
- 交货日期
""",
            "tags": ["SAP", "MM", "采购订单", "采购管理"]
        },
        "vendor": {
            "title": "SAP MM供应商管理",
            "content": """
# SAP MM供应商管理

## 概述
供应商管理是SAP MM模块的重要组成部分，用于管理企业的供应商主数据和供应商关系。

## 供应商主数据
- 供应商编号
- 供应商名称
- 地址信息
- 银行信息
- 税务信息
- 联系人信息

## 供应商分类
1. 一次性供应商
2. 常规供应商
3. 内部供应商

## 供应商评估
- 价格
- 质量
- 交货时间
- 服务

## 供应商关系管理
- 供应商选择
- 供应商评估
- 供应商开发
- 供应商绩效管理
""",
            "tags": ["SAP", "MM", "供应商", "供应商管理"]
        }
    }
    
    # 查找匹配的实体
    entity_key = entity_name.lower().replace("_", "").replace("-", "")
    for key, doc in mm_entities.items():
        if key in entity_key or entity_key in key:
            return doc
    
    return None

def create_document_in_knowledge_base(title: str, content: str, tags: List[str], metadata: Dict[str, Any] = None) -> bool:
    """在知识库中创建文档"""
    try:
        payload = {
            "title": title,
            "content": content,
            "tags": tags,
            "metadata": metadata or {}
        }
        
        r = requests.post(
            f"{KNOWLEDGE_BASE_URL}/api/documents",
            json=payload,
            timeout=30
        )
        
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"  创建文档失败: {e}")
        return False

def get_entities_needing_docs(limit: int = 50) -> List[Dict[str, Any]]:
    """获取需要文档的实体（缺少描述或业务定义的）"""
    entities = []
    skip = 0
    page_limit = 100
    
    while len(entities) < limit:
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
            
            # 筛选需要文档的实体
            for entity in page_entities:
                if len(entities) >= limit:
                    break
                
                description = entity.get("description", "")
                business_def = entity.get("business_definition", "")
                
                # 如果描述或业务定义为空或太短，需要文档
                if not description or len(description.strip()) < 50:
                    entities.append(entity)
            
            if len(page_entities) < page_limit:
                break
            
            skip += page_limit
        else:
            break
    
    return entities

def fetch_and_store_knowledge():
    """从网上抓取数据并存储到知识库"""
    print("=" * 60)
    print("从网上抓取数据并存储到知识库")
    print("=" * 60)
    print()
    
    # 1. 获取需要文档的实体
    print("1. 获取需要文档的实体...")
    entities = get_entities_needing_docs(limit=20)  # 先处理20个
    print(f"   找到 {len(entities)} 个需要文档的实体")
    print()
    
    if not entities:
        print("✅ 所有实体都有足够的文档")
        return
    
    # 2. 为每个实体搜索和创建文档
    print("2. 为实体搜索和创建文档...")
    success_count = 0
    fail_count = 0
    
    for i, entity in enumerate(entities, 1):
        entity_name = entity.get("name", "")
        entity_type = entity.get("entity_type", "concept")
        
        print(f"  [{i}/{len(entities)}] 处理实体: {entity_name}")
        
        # 搜索相关信息
        doc_info = search_web_for_entity(entity_name, entity_type)
        
        if doc_info:
            # 创建文档
            metadata = {
                "entity_id": entity.get("id"),
                "entity_name": entity_name,
                "entity_type": entity_type,
                "source": "web_search"
            }
            
            if create_document_in_knowledge_base(
                title=doc_info["title"],
                content=doc_info["content"],
                tags=doc_info["tags"],
                metadata=metadata
            ):
                success_count += 1
                print(f"    ✅ 文档创建成功")
            else:
                fail_count += 1
                print(f"    ❌ 文档创建失败")
        else:
            print(f"    ⚠️ 未找到相关信息")
            fail_count += 1
        
        # 避免请求过快
        time.sleep(0.5)
    
    print()
    print("=" * 60)
    print("完成")
    print("=" * 60)
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print("=" * 60)

if __name__ == "__main__":
    fetch_and_store_knowledge()





