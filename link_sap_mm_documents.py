#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAP MM文档与实体关联脚本
"""
import requests
import json
import time
import sys
import io

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

METADATA_URL = "http://localhost:8005/api/business-entities"
DOCUMENT_URL = "http://localhost:8004/api/documents"
LINKER_URL = "http://localhost:8005/api/document-entity-linker/link"

# SAP表名到实体名称的映射
SAP_TABLE_TO_ENTITY = {
    'MARA': 'material',
    'LFA1': 'vendor',
    'EKKO': 'purchase_order',
    'EKPO': 'purchase_order',
    'EBAN': 'purchase_requisition',
    'T001L': 'storage_location',
    'MKPF': 'material_document',
    'MSEG': 'material_document',
    'EINA': 'info_record',
    'EORD': 'source_list',
    'T023T': 'material_type',
    'T023': 'material_group',
    'T156': 'movement_type',
    'T024E': 'purchase_organization',
    'T001W': 'plant',
    'RSEG': 'invoice_verification'
}

def get_entities_by_module(module="MM"):
    """获取指定模块的实体"""
    try:
        # 搜索SAP MM相关实体
        response = requests.get(METADATA_URL, params={"search": "MM", "limit": 100}, timeout=10)
        if response.status_code == 200:
            entities = response.json()
            # 确保entities是列表
            if isinstance(entities, dict):
                entities = entities.get("items", entities.get("data", []))
            if not isinstance(entities, list):
                entities = []
            
            # 过滤SAP MM模块的实体（通过description或metadata）
            mm_entities = []
            for e in entities:
                if isinstance(e, dict):
                    # 检查description中是否包含MM相关关键词
                    desc = e.get('description', '') or e.get('display_name', '')
                    metadata = e.get('metadata', {}) or e.get('extra_metadata', {})
                    if isinstance(metadata, str):
                        try:
                            import json
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    
                    if (module in desc or 
                        metadata.get('sap_module') == module or
                        '物料' in desc or '采购' in desc or 'MM' in desc):
                        mm_entities.append(e)
            
            return mm_entities
        return []
    except Exception as e:
        print(f"❌ 获取实体失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_documents_by_module(module="MM"):
    """获取指定模块的文档"""
    try:
        response = requests.get(DOCUMENT_URL, params={"limit": 100}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 处理不同的响应格式
            if isinstance(data, dict):
                documents = data.get("documents", data.get("items", data.get("data", [])))
            elif isinstance(data, list):
                documents = data
            else:
                documents = []
            
            # 过滤SAP MM模块的文档
            mm_docs = []
            for d in documents:
                if isinstance(d, dict):
                    # 检查标题或metadata中是否包含MM相关关键词
                    title = d.get('title', '') or d.get('filename', '')
                    metadata = d.get('metadata', {})
                    if isinstance(metadata, str):
                        try:
                            import json
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    
                    if (module in title or 
                        metadata.get('module') == module or
                        'SAP MM' in title or '物料' in title or '采购' in title):
                        mm_docs.append(d)
            
            return mm_docs
        return []
    except Exception as e:
        print(f"❌ 获取文档失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def link_document_to_entity(doc_id, entity_id, relationship_type="describes"):
    """关联文档到实体"""
    try:
        # 使用正确的API格式
        response = requests.post(
            LINKER_URL,
            json={
                "document_ids": [doc_id],
                "entity_ids": [entity_id]
            },
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                print(f"   ✅ Linked document to entity {entity_id}")
                return True
            else:
                print(f"   ⚠️  Link result: {result.get('message', 'Unknown')}")
                return False
        else:
            print(f"   ❌ Failed to link: HTTP {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("SAP MM文档与实体关联")
    print("=" * 50)
    print()
    
    # 获取实体和文档
    print("📋 获取SAP MM实体和文档...")
    entities = get_entities_by_module("MM")
    documents = get_documents_by_module("MM")
    
    print(f"   找到 {len(entities)} 个实体")
    print(f"   找到 {len(documents)} 个文档\n")
    
    if not entities or not documents:
        print("⚠️  实体或文档为空，请先导入实体和文档")
        return
    
    # 建立实体名称到ID的映射
    entity_map = {e['name']: e['id'] for e in entities}
    
    # 建立关联
    linked = 0
    failed = 0
    
    print("🔗 建立文档与实体关联...\n")
    
    # 建立文档标题到实体的映射（基于关键词匹配）
    doc_title_keywords = {
        '物料主数据': ['物料主数据', 'material master'],
        '采购订单': ['采购订单', 'purchase order', 'PO'],
        '采购申请': ['采购申请', 'purchase requisition', 'PR'],
        '库存管理': ['库存', 'inventory', 'stock'],
        '供应商': ['供应商', 'vendor', 'supplier'],
        '物料凭证': ['物料凭证', 'material document'],
        '物料管理': ['物料管理', 'material management', 'MM']
    }
    
    for doc in documents:
        doc_id = doc.get('id')
        doc_title = doc.get('title', '') or doc.get('filename', 'N/A')
        doc_metadata = doc.get('metadata', {})
        if isinstance(doc_metadata, str):
            try:
                import json
                doc_metadata = json.loads(doc_metadata)
            except:
                doc_metadata = {}
        
        print(f"处理文档: {doc_title}")
        
        # 方法1: 根据SAP表名关联
        sap_table = doc_metadata.get('sap_table')
        linked_this_doc = False
        
        if sap_table:
            entity_name = SAP_TABLE_TO_ENTITY.get(sap_table)
            if entity_name and entity_name in entity_map:
                entity_id = entity_map[entity_name]
                if link_document_to_entity(doc_id, entity_id):
                    linked += 1
                    linked_this_doc = True
                else:
                    failed += 1
        
        # 方法2: 根据文档标题关键词匹配实体
        if not linked_this_doc:
            for keyword, matches in doc_title_keywords.items():
                if any(m in doc_title for m in matches):
                    # 查找匹配的实体
                    for entity in entities:
                        entity_name = entity.get('name', '') or entity.get('display_name', '')
                        if keyword in entity_name or any(m in entity_name.lower() for m in matches):
                            entity_id = entity.get('id')
                            if entity_id and link_document_to_entity(doc_id, entity_id):
                                linked += 1
                                linked_this_doc = True
                                break
                    if linked_this_doc:
                        break
        
        # 方法3: 如果文档标题包含实体名称，直接匹配
        if not linked_this_doc:
            for entity in entities:
                entity_name = entity.get('name', '') or entity.get('display_name', '')
                if entity_name and entity_name in doc_title:
                    entity_id = entity.get('id')
                    if entity_id and link_document_to_entity(doc_id, entity_id):
                        linked += 1
                        linked_this_doc = True
                        break
        
        if not linked_this_doc:
            print(f"   ⚠️  无法自动关联文档")
        
        print()
        time.sleep(0.3)
    
    print("=" * 50)
    print("关联完成")
    print("=" * 50)
    print(f"✅ 成功: {linked}")
    print(f"❌ 失败: {failed}")
    print()
    
    if linked > 0:
        print(f"🎉 成功建立了 {linked} 个文档-实体关联！")

if __name__ == "__main__":
    main()

