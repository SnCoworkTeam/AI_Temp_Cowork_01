"""
详细检查语义索引状态
"""
import requests
import json
import time
from datetime import datetime

def get_all_metadata_assets():
    """获取所有SAP元数据资产"""
    print("获取所有SAP元数据资产...")
    all_assets = []
    offset = 0
    page_size = 100
    
    while True:
        try:
            response = requests.get(
                "http://localhost:8005/api/data-assets",
                params={
                    "limit": page_size,
                    "skip": offset,
                    "source_system": "SAP"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                break
            
            data = response.json()
            if isinstance(data, list):
                assets = data
            elif isinstance(data, dict):
                assets = data.get("items", data.get("data", []))
            else:
                assets = []
            
            if not assets:
                break
            
            all_assets.extend(assets)
            print(f"  已获取 {len(all_assets)} 个资产...")
            
            if len(assets) < page_size:
                break
            
            offset += page_size
            time.sleep(0.5)  # 避免过快请求
            
        except Exception as e:
            print(f"  获取资产时出错: {e}")
            break
    
    return all_assets


def check_knowledge_base_documents():
    """详细检查知识库文档"""
    print("\n检查知识库文档详情...")
    
    try:
        # 获取所有文档
        all_docs = []
        page = 1
        page_size = 100
        
        while True:
            response = requests.get(
                "http://localhost:8004/api/documents",
                params={"page": page, "page_size": page_size},
                timeout=10
            )
            
            if response.status_code != 200:
                break
            
            data = response.json()
            docs = data.get("documents", [])
            if not docs:
                break
            
            all_docs.extend(docs)
            
            if len(docs) < page_size:
                break
            
            page += 1
        
        print(f"  总文档数: {len(all_docs)}")
        
        # 分析文档
        processing = []
        processed = []
        failed = []
        sap_related = []
        
        for doc in all_docs:
            status = doc.get("status", "unknown")
            metadata = doc.get("metadata", {})
            category = doc.get("category", "")
            tags = doc.get("tags", [])
            
            # 检查是否是SAP相关
            is_sap = (
                "sap" in category.lower() or
                any("sap" in str(tag).lower() for tag in tags) or
                "sap" in str(metadata).lower() or
                "data_asset" in str(metadata.get("type", "")).lower()
            )
            
            if is_sap:
                sap_related.append(doc)
            
            if status == "processing":
                processing.append(doc)
            elif status == "processed":
                processed.append(doc)
            elif status == "failed":
                failed.append(doc)
        
        print(f"\n  文档状态统计:")
        print(f"    处理中 (processing): {len(processing)}")
        print(f"    已处理 (processed): {len(processed)}")
        print(f"    失败 (failed): {len(failed)}")
        print(f"    SAP相关: {len(sap_related)}")
        
        # 显示处理中的文档详情
        if processing:
            print(f"\n  处理中的文档:")
            for i, doc in enumerate(processing[:10], 1):
                title = doc.get("filename", doc.get("metadata", {}).get("title", "N/A"))
                doc_id = doc.get("id", "N/A")
                print(f"    {i}. {title} (ID: {doc_id})")
        
        # 显示失败的文档
        if failed:
            print(f"\n  失败的文档:")
            for i, doc in enumerate(failed[:10], 1):
                title = doc.get("filename", doc.get("metadata", {}).get("title", "N/A"))
                doc_id = doc.get("id", "N/A")
                print(f"    {i}. {title} (ID: {doc_id})")
        
        # 显示SAP相关文档
        if sap_related:
            print(f"\n  SAP相关文档:")
            for i, doc in enumerate(sap_related[:10], 1):
                title = doc.get("filename", doc.get("metadata", {}).get("title", "N/A"))
                status = doc.get("status", "unknown")
                print(f"    {i}. {title} (状态: {status})")
        
        return {
            "total": len(all_docs),
            "processing": len(processing),
            "processed": len(processed),
            "failed": len(failed),
            "sap_related": len(sap_related)
        }
        
    except Exception as e:
        print(f"  检查失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("详细语义索引状态检查")
    print("=" * 80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 获取所有元数据资产
    assets = get_all_metadata_assets()
    print(f"\n✓ 总共找到 {len(assets)} 个SAP元数据资产")
    
    # 2. 检查知识库文档
    kb_status = check_knowledge_base_documents()
    
    # 总结
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    print(f"元数据资产总数: {len(assets)}")
    
    if kb_status:
        print(f"知识库文档总数: {kb_status['total']}")
        print(f"  处理中: {kb_status['processing']}")
        print(f"  已处理: {kb_status['processed']}")
        print(f"  失败: {kb_status['failed']}")
        print(f"  SAP相关: {kb_status['sap_related']}")
        
        if len(assets) > 0:
            progress = (kb_status['processed'] / len(assets)) * 100
            print(f"\n处理进度: {kb_status['processed']}/{len(assets)} ({progress:.1f}%)")
    
    print("\n" + "=" * 80)
    
    # 建议
    if kb_status and kb_status['processing'] > 0:
        print("\n提示: 有文档正在处理中，请稍后再次检查状态")
    if kb_status and kb_status['failed'] > 0:
        print("\n警告: 有文档处理失败，请检查知识库服务日志")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断检查")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

