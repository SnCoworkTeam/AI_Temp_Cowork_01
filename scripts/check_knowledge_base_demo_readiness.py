#!/usr/bin/env python3
"""
检查知识库是否满足演示条件
"""

import requests
import json

KNOWLEDGE_BASE_URL = "http://localhost:8004"

def check_knowledge_base():
    """检查知识库状态"""
    print("=" * 60)
    print("知识库演示条件检查")
    print("=" * 60)
    print()
    
    # 1. 检查服务状态
    print("1. 检查服务状态")
    print("-" * 60)
    try:
        r = requests.get(f"{KNOWLEDGE_BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            print("  ✅ 知识库服务运行正常")
        else:
            print(f"  ⚠️ 知识库服务状态异常: {r.status_code}")
    except Exception as e:
        print(f"  ❌ 知识库服务不可用: {e}")
        return False
    
    # 2. 检查文档数量
    print()
    print("2. 检查文档数量")
    print("-" * 60)
    try:
        r = requests.get(f"{KNOWLEDGE_BASE_URL}/api/documents?limit=1000", timeout=10)
        if r.status_code == 200:
            docs = r.json()
            if isinstance(docs, dict):
                docs = docs.get('documents', []) or docs.get('data', [])
            elif not isinstance(docs, list):
                docs = []
            
            doc_count = len(docs)
            processed_count = sum(1 for d in docs if d.get('status') == 'processed')
            
            print(f"  总文档数: {doc_count}")
            print(f"  已处理文档数: {processed_count}")
            
            # 评估
            if doc_count >= 50:
                print("  ✅ 文档数量充足（50+）")
                doc_score = 100
            elif doc_count >= 20:
                print("  ⚠️ 文档数量一般（20-49）")
                doc_score = 70
            elif doc_count >= 10:
                print("  ⚠️ 文档数量较少（10-19）")
                doc_score = 40
            else:
                print("  ❌ 文档数量不足（<10）")
                doc_score = 0
            
            # 检查文档类型
            print()
            print("  文档类型分布:")
            doc_types = {}
            for doc in docs:
                doc_type = doc.get('file_type', 'unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            for doc_type, count in doc_types.items():
                print(f"    - {doc_type}: {count}")
            
            # 检查SAP MM相关文档
            print()
            print("  SAP MM相关文档:")
            sap_mm_docs = []
            for doc in docs:
                filename = doc.get('filename', '').lower()
                title = doc.get('title', '').lower()
                if 'sap' in filename or 'mm' in filename or 'sap' in title or 'mm' in title:
                    sap_mm_docs.append(doc)
            print(f"    - SAP MM文档数: {len(sap_mm_docs)}")
            for doc in sap_mm_docs[:5]:
                print(f"      * {doc.get('filename', doc.get('title', '未知'))}")
            
            return {
                'doc_count': doc_count,
                'processed_count': processed_count,
                'doc_score': doc_score,
                'sap_mm_count': len(sap_mm_docs),
                'docs': docs
            }
        else:
            print(f"  ❌ 无法获取文档列表: {r.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ 检查文档失败: {e}")
        return None

def check_demo_readiness(result):
    """评估演示就绪度"""
    print()
    print("=" * 60)
    print("演示就绪度评估")
    print("=" * 60)
    print()
    
    if not result:
        print("  ❌ 无法评估（服务不可用）")
        return False
    
    doc_count = result['doc_count']
    doc_score = result['doc_score']
    sap_mm_count = result['sap_mm_count']
    
    print(f"文档数量得分: {doc_score}/100")
    print(f"SAP MM文档数: {sap_mm_count}")
    print()
    
    # 综合评估
    if doc_score >= 70 and sap_mm_count >= 5:
        readiness = "✅ 完全就绪"
        recommendation = "可以进行完整演示"
    elif doc_score >= 40 and sap_mm_count >= 3:
        readiness = "⚠️ 基本就绪"
        recommendation = "可以进行基本演示，建议补充文档"
    elif doc_score >= 40:
        readiness = "⚠️ 部分就绪"
        recommendation = "可以进行简单演示，需要补充SAP MM文档"
    else:
        readiness = "❌ 未就绪"
        recommendation = "需要补充文档后才能演示"
    
    print(f"演示就绪度: {readiness}")
    print(f"建议: {recommendation}")
    print()
    
    # 改进建议
    if doc_score < 70 or sap_mm_count < 5:
        print("改进建议:")
        if doc_score < 70:
            print(f"  - 需要补充文档（当前{doc_count}个，目标50+）")
        if sap_mm_count < 5:
            print(f"  - 需要补充SAP MM文档（当前{sap_mm_count}个，目标5+）")
        print("  - 可以从网上搜索SAP MM相关知识生成文档")
        print("  - 文档主题建议：")
        print("    * SAP MM物料管理")
        print("    * SAP MM采购订单")
        print("    * SAP MM供应商管理")
        print("    * SAP MM库存管理")
        print("    * SAP MM发票校验")
    
    return readiness.startswith("✅")

if __name__ == "__main__":
    result = check_knowledge_base()
    is_ready = check_demo_readiness(result)
    
    print("=" * 60)
    if is_ready:
        print("✅ 知识库满足演示条件")
    else:
        print("⚠️ 知识库需要补充文档")
    print("=" * 60)





