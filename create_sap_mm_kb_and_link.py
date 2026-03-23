#!/usr/bin/env python3
"""
创建SAP MM知识库并关联文档
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8004/api"

def create_knowledge_base():
    """创建SAP MM知识库"""
    kb_data = {
        "name": "SAP MM知识库",
        "description": "SAP MM模块相关文档，包括采购流程、数据字典、库存管理等",
        "status": "active",
        "embedding_model": "default",
        "chunk_strategy": "semantic",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "settings": {
            "auto_index": True,
            "enable_search": True
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/knowledge-bases", json=kb_data, timeout=30)
        if response.status_code in [200, 201]:
            result = response.json()
            kb_id = result.get('id')
            print(f"✅ 知识库创建成功: {kb_data['name']} (ID: {kb_id})")
            return kb_id
        elif response.status_code == 409:
            # 知识库已存在，查找现有知识库
            print("⚠️  知识库可能已存在，查找现有知识库...")
            kb_list = requests.get(f"{BASE_URL}/knowledge-bases", timeout=30).json()
            for kb in kb_list.get('knowledge_bases', []):
                if 'SAP' in kb.get('name', '') and 'MM' in kb.get('name', ''):
                    print(f"✅ 找到现有知识库: {kb.get('name')} (ID: {kb.get('id')})")
                    return kb.get('id')
            return None
        else:
            print(f"❌ 创建知识库失败: HTTP {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ 创建知识库错误: {e}")
        return None

def get_sap_mm_documents():
    """获取所有SAP MM文档"""
    try:
        response = requests.get(f"{BASE_URL}/documents?limit=100", timeout=30)
        response.raise_for_status()
        data = response.json()
        documents = data.get('documents', [])
        
        sap_docs = []
        for doc in documents:
            filename = str(doc.get('filename', ''))
            title = str(doc.get('title', ''))
            if ('SAP' in filename or 'MM' in filename or 
                'SAP' in title or 'MM' in title or
                'sap_mm' in filename.lower()):
                sap_docs.append(doc)
        
        return sap_docs
    except Exception as e:
        print(f"❌ 获取文档列表错误: {e}")
        return []

def link_document_to_kb(document_id, kb_id):
    """将文档关联到知识库"""
    try:
        # 获取文档详情
        doc_response = requests.get(f"{BASE_URL}/documents/{document_id}", timeout=30)
        if doc_response.status_code != 200:
            print(f"   ⚠️  无法获取文档详情: {document_id}")
            return False
        
        doc_data = doc_response.json()
        
        # 更新文档的knowledge_base_id
        # 注意：这里需要检查API是否支持更新knowledge_base_id
        # 如果不支持，可能需要通过PATCH或PUT方法更新
        
        # 尝试通过PATCH更新
        update_data = {
            "knowledge_base_id": kb_id
        }
        
        patch_response = requests.patch(
            f"{BASE_URL}/documents/{document_id}",
            json=update_data,
            timeout=30
        )
        
        if patch_response.status_code in [200, 204]:
            return True
        else:
            # 如果PATCH不支持，尝试直接更新数据库
            print(f"   ⚠️  PATCH更新失败，可能需要直接更新数据库")
            return False
            
    except Exception as e:
        print(f"   ❌ 关联文档错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("创建SAP MM知识库并关联文档")
    print("=" * 60)
    print()
    
    # 1. 创建或查找知识库
    print("步骤1: 创建/查找SAP MM知识库...")
    kb_id = create_knowledge_base()
    if not kb_id:
        print("❌ 无法创建或找到知识库")
        sys.exit(1)
    print()
    
    # 2. 获取SAP MM文档
    print("步骤2: 获取SAP MM文档列表...")
    sap_docs = get_sap_mm_documents()
    print(f"找到 {len(sap_docs)} 个SAP MM文档")
    print()
    
    # 3. 关联文档到知识库
    print("步骤3: 关联文档到知识库...")
    linked = 0
    failed = 0
    already_linked = 0
    
    for doc in sap_docs:
        doc_id = doc.get('id')
        filename = doc.get('filename', doc.get('title', '未知'))
        current_kb_id = doc.get('knowledge_base_id')
        
        if current_kb_id == kb_id:
            print(f"✅ {filename} - 已关联")
            already_linked += 1
        elif current_kb_id:
            print(f"⚠️  {filename} - 已关联到其他知识库 ({current_kb_id})")
            already_linked += 1
        else:
            print(f"处理: {filename}...")
            if link_document_to_kb(doc_id, kb_id):
                print(f"✅ {filename} - 关联成功")
                linked += 1
            else:
                print(f"❌ {filename} - 关联失败")
                failed += 1
        print()
    
    print("=" * 60)
    print("关联完成")
    print("=" * 60)
    print(f"✅ 新关联: {linked}")
    print(f"⚠️  已关联: {already_linked}")
    print(f"❌ 失败: {failed}")
    print()
    
    if linked > 0:
        print(f"🎉 成功将 {linked} 个文档关联到SAP MM知识库！")
        print()
        print("注意:")
        print("- 文档已关联到知识库")
        print("- 前端现在应该可以看到这些文档了")
        print("- 可以通过知识库ID筛选文档")

if __name__ == "__main__":
    main()




