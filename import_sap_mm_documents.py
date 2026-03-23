#!/usr/bin/env python3
"""
SAP MM文档批量导入脚本
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8004/api/documents/create"

def load_documents(file_path):
    """加载文档定义"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('documents', [])
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        sys.exit(1)

def create_document(doc):
    """创建单个文档"""
    try:
        # 构建请求数据 - 确保所有必需字段都存在
        request_data = {
            "title": str(doc.get('title', '')),
            "content": str(doc.get('content', '')),
            "category": str(doc.get('metadata', {}).get('category', '')),
            "tags": list(doc.get('metadata', {}).get('tags', [])),
            "metadata": dict(doc.get('metadata', {})),
            "process_async": True  # 异步处理，避免超时
        }
        
        # 确保title不为空
        if not request_data['title']:
            request_data['title'] = f"Document {doc.get('title', 'Untitled')}"
        
        print(f"   发送数据: title={request_data['title'][:50]}..., content长度={len(request_data['content'])}")
        response = requests.post(BASE_URL, json=request_data, timeout=30)
        if response.status_code in [200, 201]:
            result = response.json()
            doc_id = result.get('document_id') or result.get('id', 'N/A')
            print(f"✅ Created: {doc['title']} (ID: {doc_id})")
            return result
        elif response.status_code == 409:
            print(f"⚠️  Already exists: {doc['title']}")
            return None
        else:
            print(f"❌ Failed: {doc['title']} - HTTP {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务，请确保knowledge-base正在运行")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error creating {doc['title']}: {e}")
        return None

def main():
    """主函数"""
    print("=" * 50)
    print("SAP MM文档批量导入")
    print("=" * 50)
    print()
    
    # 加载文档定义
    documents = load_documents('sap_mm_documents.json')
    print(f"📋 加载了 {len(documents)} 个文档定义\n")
    
    # 批量创建
    created = 0
    failed = 0
    skipped = 0
    
    for i, doc in enumerate(documents, 1):
        print(f"[{i}/{len(documents)}] 处理: {doc['title']}...")
        result = create_document(doc)
        if result:
            created += 1
        elif result is None and "Already exists" in str(result):
            skipped += 1
        else:
            failed += 1
        time.sleep(1)  # 文档处理需要更多时间
        print()
    
    print("=" * 50)
    print("导入完成")
    print("=" * 50)
    print(f"✅ 成功: {created}")
    print(f"⚠️  跳过: {skipped}")
    print(f"❌ 失败: {failed}")
    print()
    
    if created > 0:
        print(f"🎉 成功导入了 {created} 个SAP MM文档！")
        print()
        print("注意:")
        print("- 文档会自动向量化，可能需要几分钟时间")
        print("- 文档向量化完成后，可以通过统一搜索进行语义搜索")
        print()
        print("下一步:")
        print("1. 等待文档向量化完成（约5-10分钟）")
        print("2. 建立文档与实体关联")
        print("3. 测试搜索功能: POST /api/unified/search")

if __name__ == "__main__":
    main()





