#!/usr/bin/env python3
"""
检查SAP MM文档导入和向量化状态
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8004/api/documents"

def check_documents():
    """检查文档状态"""
    try:
        response = requests.get(f"{BASE_URL}?limit=100", timeout=30)
        response.raise_for_status()
        data = response.json()
        documents = data.get('documents', [])
        
        # 筛选SAP MM相关文档
        sap_docs = []
        for doc in documents:
            filename = str(doc.get('filename', ''))
            title = str(doc.get('title', ''))
            if 'SAP' in filename or 'MM' in filename or 'SAP' in title or 'MM' in title:
                sap_docs.append(doc)
        
        print("=" * 60)
        print("SAP MM文档导入状态检查")
        print("=" * 60)
        print(f"\n总文档数: {len(documents)}")
        print(f"SAP MM文档数: {len(sap_docs)}")
        print()
        
        if sap_docs:
            print("SAP MM文档详情:")
            print("-" * 60)
            processed = 0
            processing = 0
            failed = 0
            total_chunks = 0
            
            for i, doc in enumerate(sap_docs, 1):
                filename = doc.get('filename', doc.get('title', '未知'))
                status = doc.get('status', 'unknown')
                chunks = doc.get('total_chunks', 0)
                
                print(f"{i}. {filename}")
                print(f"   状态: {status}")
                print(f"   Chunks: {chunks}")
                print()
                
                if status == 'processed':
                    processed += 1
                    total_chunks += chunks
                elif status == 'processing':
                    processing += 1
                elif status == 'failed':
                    failed += 1
            
            print("-" * 60)
            print(f"已处理完成: {processed} 个文档")
            print(f"处理中: {processing} 个文档")
            print(f"失败: {failed} 个文档")
            print(f"总Chunks数: {total_chunks}")
            print()
            
            if processed > 0 and total_chunks > 0:
                print("✅ SAP MM文档已成功导入并向量化！")
            elif processing > 0:
                print("⏳ 部分文档仍在处理中，请稍候...")
            else:
                print("⚠️  文档可能尚未开始处理")
        else:
            print("❌ 未找到SAP MM文档")
            print("\n建议:")
            print("1. 检查导入脚本是否成功运行")
            print("2. 检查文档是否已创建")
            print("3. 查看knowledge-base日志")
        
        return len(sap_docs), processed, total_chunks
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到knowledge-base服务")
        print("请确保服务正在运行: docker compose ps knowledge-base")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_documents()




