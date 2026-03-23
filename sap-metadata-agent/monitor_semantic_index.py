"""
监控语义索引构建进度
"""
import requests
import time
from datetime import datetime

def check_knowledge_base():
    """检查知识库中的SAP相关文档数量"""
    try:
        response = requests.get(
            "http://localhost:8004/api/documents",
            params={"page": 1, "page_size": 1000},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            documents = data.get("documents", [])
            
            # 统计SAP相关文档
            sap_processed = 0
            sap_processing = 0
            sap_failed = 0
            
            for doc in documents:
                metadata = doc.get("metadata", {})
                category = doc.get("category", "")
                tags = doc.get("tags", [])
                status = doc.get("status", "")
                
                # 检查是否是SAP相关
                is_sap = (
                    "sap_metadata" in category.lower() or
                    any("sap" in str(tag).lower() for tag in tags) or
                    "data_asset" in str(metadata.get("type", "")).lower() or
                    "business_entity" in str(metadata.get("type", "")).lower()
                )
                
                if is_sap:
                    if status == "processed":
                        sap_processed += 1
                    elif status == "processing":
                        sap_processing += 1
                    elif status == "failed":
                        sap_failed += 1
            
            return {
                "total": total,
                "sap_processed": sap_processed,
                "sap_processing": sap_processing,
                "sap_failed": sap_failed
            }
        else:
            return None
    except Exception as e:
        print(f"检查知识库失败: {e}")
        return None


def main():
    """主监控循环"""
    print("=" * 80)
    print("语义索引构建进度监控")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 获取元数据总数
    try:
        response = requests.get(
            "http://localhost:8005/api/data-assets",
            params={"limit": 1, "source_system": "SAP"},
            timeout=10
        )
        # 估算总数（通过获取大量数据）
        response2 = requests.get(
            "http://localhost:8005/api/data-assets",
            params={"limit": 10000, "source_system": "SAP"},
            timeout=30
        )
        if response2.status_code == 200:
            data2 = response2.json()
            total_assets = len(data2) if isinstance(data2, list) else 0
        else:
            total_assets = 109022  # 使用之前检查到的数量
    except:
        total_assets = 109022
    
    print(f"元数据资产总数: {total_assets:,}")
    print(f"\n开始监控... (每30秒检查一次，按Ctrl+C停止)\n")
    
    last_processed = 0
    check_count = 0
    
    try:
        while True:
            check_count += 1
            kb_status = check_knowledge_base()
            
            if kb_status:
                current_processed = kb_status["sap_processed"]
                current_processing = kb_status["sap_processing"]
                current_failed = kb_status["sap_failed"]
                
                # 计算进度
                progress = (current_processed / total_assets * 100) if total_assets > 0 else 0
                
                # 计算速度
                if check_count > 1:
                    speed = current_processed - last_processed
                    speed_str = f"(+{speed} 个/30秒)"
                else:
                    speed_str = ""
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查 #{check_count}")
                print(f"  已处理: {current_processed:,} / {total_assets:,} ({progress:.2f}%) {speed_str}")
                print(f"  处理中: {current_processing}")
                print(f"  失败: {current_failed}")
                
                if current_processed > 0:
                    remaining = total_assets - current_processed
                    if speed > 0:
                        eta_seconds = (remaining / speed) * 30
                        eta_minutes = eta_seconds / 60
                        print(f"  预计剩余时间: {eta_minutes:.1f} 分钟")
                
                last_processed = current_processed
                
                # 如果处理完成
                if current_processed >= total_assets and current_processing == 0:
                    print(f"\n✅ 语义索引构建完成！")
                    break
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 无法连接到知识库服务")
            
            time.sleep(30)  # 每30秒检查一次
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️  监控已停止")
        if kb_status:
            print(f"当前状态:")
            print(f"  已处理: {kb_status['sap_processed']:,}")
            print(f"  处理中: {kb_status['sap_processing']}")
            print(f"  失败: {kb_status['sap_failed']}")


if __name__ == "__main__":
    main()

