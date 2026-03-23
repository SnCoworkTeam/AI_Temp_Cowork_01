#!/bin/bash
# SAP MM文档批量导入脚本（使用curl直接调用API）

BASE_URL="http://localhost:8004/api/documents/create"
JSON_FILE="sap_mm_documents.json"

echo "=================================================="
echo "SAP MM文档批量导入"
echo "=================================================="
echo ""

# 检查文件是否存在
if [ ! -f "$JSON_FILE" ]; then
    echo "❌ 文件不存在: $JSON_FILE"
    exit 1
fi

# 使用Python解析JSON并逐个导入
python3 << 'PYTHON_SCRIPT'
import json
import requests
import time
import sys

BASE_URL = "http://localhost:8004/api/documents/create"
JSON_FILE = "sap_mm_documents.json"

try:
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    documents = data.get('documents', [])
    print(f"📋 加载了 {len(documents)} 个文档定义\n")
    
    created = 0
    failed = 0
    skipped = 0
    
    for i, doc in enumerate(documents, 1):
        print(f"[{i}/{len(documents)}] 处理: {doc['title']}...")
        
        # 构建请求数据
        request_data = {
            "title": doc['title'],
            "content": doc['content'],
            "category": doc.get('metadata', {}).get('category', ''),
            "tags": doc.get('metadata', {}).get('tags', []),
            "metadata": doc.get('metadata', {}),
            "process_async": True
        }
        
        try:
            response = requests.post(BASE_URL, json=request_data, timeout=30)
            if response.status_code in [200, 201]:
                result = response.json()
                doc_id = result.get('document_id') or result.get('id', 'N/A')
                print(f"✅ Created: {doc['title']} (ID: {doc_id})")
                created += 1
            elif response.status_code == 409:
                print(f"⚠️  Already exists: {doc['title']}")
                skipped += 1
            else:
                print(f"❌ Failed: {doc['title']} - HTTP {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                failed += 1
        except Exception as e:
            print(f"❌ Error creating {doc['title']}: {e}")
            failed += 1
        
        time.sleep(0.5)  # 避免请求过快
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
    
except FileNotFoundError:
    print(f"❌ 文件不存在: {JSON_FILE}")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ JSON解析错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)
PYTHON_SCRIPT




