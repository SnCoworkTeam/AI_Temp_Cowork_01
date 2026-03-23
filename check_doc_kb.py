#!/usr/bin/env python3
"""
检查文档的knowledge_base_id关联
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8004/api"

def check_documents():
    """检查文档的knowledge_base_id"""
    try:
        # 获取文档列表
        response = requests.get(f"{BASE_URL}/documents?limit=50", timeout=30)
        response.raise_for_status()
        data = response.json()
        documents = data.get('documents', [])
        
        # 获取知识库列表
        kb_response = requests.get(f"{BASE_URL}/knowledge-bases", timeout=30)
        kb_response.raise_for_status()
        kb_data = kb_response.json()
        knowledge_bases = kb_data.get('knowledge_bases', [])
        
        print("=" * 60)
        print("文档与知识库关联检查")
        print("=" * 60)
        
        # 找到SAP MM知识库
        SAP_MM_KB_ID = None
        for kb in knowledge_bases:
            if 'SAP' in kb.get('name', '') and 'MM' in kb.get('name', ''):
                SAP_MM_KB_ID = kb.get('id')
                break
        
        print(f"\n知识库列表 ({len(knowledge_bases)}个):")
        for kb in knowledge_bases:
            print(f"  - {kb.get('name')} (ID: {kb.get('id')})")
            print(f"    文档数: {kb.get('document_count', 0)}")
            if kb.get('id') == SAP_MM_KB_ID:
                print(f"    ⭐ SAP MM知识库")
        
        # 筛选SAP MM文档
        sap_docs = []
        for doc in documents:
            filename = str(doc.get('filename', ''))
            title = str(doc.get('title', ''))
            kb_id = doc.get('knowledge_base_id')
            # 检查是否是SAP MM文档
            if ('SAP' in filename or 'MM' in filename or 
                'SAP' in title or 'MM' in title or
                'sap_mm' in filename.lower()):
                sap_docs.append(doc)
            # 或者检查是否关联到SAP MM知识库
            elif kb_id == SAP_MM_KB_ID:
                sap_docs.append(doc)
        
        print(f"\nSAP MM文档 ({len(sap_docs)}个):")
        print("-" * 60)
        
        no_kb = []
        has_kb = []
        
        for doc in sap_docs:
            filename = doc.get('filename', doc.get('title', '未知'))
            kb_id = doc.get('knowledge_base_id')
            status = doc.get('status', 'unknown')
            chunks = doc.get('total_chunks', 0)
            
            if kb_id:
                kb_name = next((kb.get('name') for kb in knowledge_bases if kb.get('id') == kb_id), '未知知识库')
                is_sap_kb = (kb_id == SAP_MM_KB_ID) if SAP_MM_KB_ID else False
                marker = "⭐" if is_sap_kb else "✅"
                print(f"{marker} {filename}")
                print(f"   知识库: {kb_name} ({kb_id})")
                print(f"   状态: {status}, Chunks: {chunks}")
                has_kb.append(doc)
            else:
                print(f"❌ {filename}")
                print(f"   知识库: 未关联")
                print(f"   状态: {status}, Chunks: {chunks}")
                no_kb.append(doc)
            print()
        
        print("-" * 60)
        print(f"已关联知识库: {len(has_kb)} 个")
        print(f"未关联知识库: {len(no_kb)} 个")
        
        if no_kb:
            print("\n⚠️  发现未关联知识库的文档！")
            print("建议:")
            print("1. 创建SAP MM知识库")
            print("2. 将文档关联到该知识库")
        
        return no_kb, knowledge_bases
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_documents()

