"""
快速检查语义索引进度
"""
import requests
import time
from datetime import datetime

def check_progress():
    """检查当前进度"""
    try:
        # 检查知识库中的SAP相关文档
        response = requests.get(
            "http://localhost:8004/api/documents",
            params={"page": 1, "page_size": 1000},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            
            # 统计SAP相关文档
            sap_processed = 0
            sap_processing = 0
            sap_failed = 0
            
            for doc in documents:
                metadata = doc.get("metadata", {})
                category = doc.get("category", "")
                tags = doc.get("tags", [])
                doc_type = metadata.get("type", "")
                
                is_sap = (
                    "sap_metadata" in category.lower() or
                    any("sap" in str(tag).lower() for tag in tags) or
                    "data_asset" in str(doc_type).lower() or
                    "business_entity" in str(doc_type).lower()
                )
                
                if is_sap:
                    status = doc.get("status", "")
                    if status == "processed":
                        sap_processed += 1
                    elif status == "processing":
                        sap_processing += 1
                    elif status == "failed":
                        sap_failed += 1
            
            total_assets = 109022
            progress = (sap_processed / total_assets * 100) if total_assets > 0 else 0
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 进度检查:")
            print(f"  已处理: {sap_processed:,} / {total_assets:,} ({progress:.2f}%)")
            print(f"  处理中: {sap_processing}")
            print(f"  失败: {sap_failed}")
            
            return sap_processed, sap_processing, sap_failed
        else:
            print(f"无法获取文档列表: HTTP {response.status_code}")
            return 0, 0, 0
    except Exception as e:
        print(f"检查失败: {e}")
        return 0, 0, 0

if __name__ == "__main__":
    print("=" * 60)
    print("语义索引进度监控")
    print("=" * 60)
    print("按Ctrl+C停止监控\n")
    
    last_processed = 0
    check_count = 0
    
    try:
        while True:
            check_count += 1
            processed, processing, failed = check_progress()
            
            if check_count > 1 and processed > last_processed:
                speed = processed - last_processed
                print(f"  速度: +{speed} 个/30秒")
            
            last_processed = processed
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n\n监控已停止")
        print(f"最终状态: 已处理 {last_processed:,} 个文档")

