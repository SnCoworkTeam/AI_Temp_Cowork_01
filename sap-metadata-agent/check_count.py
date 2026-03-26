"""快速查询语义索引数量"""
import requests

try:
    # 查询知识库文档
    response = requests.get("http://localhost:8004/api/documents", params={"page": 1, "page_size": 1000}, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        docs = data.get("documents", [])
        total = data.get("total", len(docs))
        
        # 统计SAP相关
        sap_count = 0
        sap_processed = 0
        
        for doc in docs:
            metadata = doc.get("metadata", {})
            category = doc.get("category", "")
            tags = doc.get("tags", [])
            doc_type = str(metadata.get("type", ""))
            
            is_sap = (
                "sap" in category.lower() or
                any("sap" in str(tag).lower() for tag in tags) or
                "data_asset" in doc_type.lower() or
                "business_entity" in doc_type.lower()
            )
            
            if is_sap:
                sap_count += 1
                if doc.get("status") == "processed":
                    sap_processed += 1
        
        print(f"知识库总文档数: {total}")
        print(f"SAP相关文档总数: {sap_count}")
        print(f"已处理的SAP文档: {sap_processed}")
        print(f"处理进度: {sap_processed}/109022 ({sap_processed/109022*100:.2f}%)" if sap_processed > 0 else "处理进度: 0/109022 (0.00%)")
    else:
        print(f"查询失败: HTTP {response.status_code}")
except Exception as e:
    print(f"错误: {e}")

