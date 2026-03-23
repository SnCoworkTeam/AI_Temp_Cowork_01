#!/usr/bin/env python3
"""
上传文档到知识库
"""

import requests
import os
import json

KNOWLEDGE_BASE_URL = "http://localhost:8004"
DOCS_DIR = "docs"

def upload_document(file_path: str) -> bool:
    """上传单个文档到知识库"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取标题（第一行的# 标题）
        lines = content.split('\n')
        title = lines[0].replace('# ', '').strip() if lines else os.path.basename(file_path)
        
        # 尝试多种API格式
        # 格式1: JSON格式
        payload = {
            "title": title,
            "content": content,
            "tags": ["SAP", "MM", "知识库", "文档"],
            "metadata": {
                "source": "web_search",
                "file": os.path.basename(file_path),
                "category": "SAP_MM"
            }
        }
        
        # 尝试JSON格式
        r = requests.post(
            f"{KNOWLEDGE_BASE_URL}/api/documents",
            json=payload,
            timeout=30
        )
        
        if r.status_code in [200, 201]:
            return True
        
        # 如果JSON格式失败，尝试multipart格式
        print(f"    JSON格式失败 ({r.status_code}), 尝试multipart格式...")
        files = {
            'file': (os.path.basename(file_path), content, 'text/markdown')
        }
        data = {
            'title': title,
            'tags': 'SAP,MM,知识库,文档'
        }
        
        r = requests.post(
            f"{KNOWLEDGE_BASE_URL}/api/documents/upload",
            files=files,
            data=data,
            timeout=30
        )
        
        if r.status_code in [200, 201]:
            return True
        
        print(f"    所有格式都失败: {r.status_code} - {r.text[:200]}")
        return False
    except Exception as e:
        print(f"  上传失败: {e}")
        return False

def main():
    print("=" * 60)
    print("上传文档到知识库")
    print("=" * 60)
    print()
    
    # 查找SAP MM相关文档
    sap_mm_files = [
        "sap_mm_material_management.md",
        "sap_mm_purchase_order.md",
        "sap_mm_vendor_management.md"
    ]
    
    success = 0
    fail = 0
    
    for filename in sap_mm_files:
        file_path = os.path.join(DOCS_DIR, filename)
        if os.path.exists(file_path):
            print(f"上传: {filename}")
            if upload_document(file_path):
                print(f"  ✅ 成功")
                success += 1
            else:
                print(f"  ❌ 失败")
                fail += 1
        else:
            print(f"文件不存在: {file_path}")
            fail += 1
    
    print()
    print("=" * 60)
    print(f"完成: 成功 {success}, 失败 {fail}")
    print("=" * 60)

if __name__ == "__main__":
    main()

