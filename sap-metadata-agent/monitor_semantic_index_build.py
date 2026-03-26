"""
监控语义索引构建进度
"""
import requests
import time
import os
from datetime import datetime

KNOWLEDGE_BASE_URL = os.getenv("KNOWLEDGE_BASE_URL", "http://localhost:8004")
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://localhost:8005")

def get_indexed_count():
    """获取已索引的文档数量"""
    try:
        # 查询知识库中SAP元数据相关的文档
        response = requests.get(
            f"{KNOWLEDGE_BASE_URL}/api/documents",
            params={
                "category": "sap_metadata",
                "page": 1,
                "page_size": 1
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("total", 0)
        return None
    except:
        return None

def get_total_metadata_count():
    """获取元数据总数"""
    try:
        response = requests.get(
            f"{METADATA_SERVICE_URL}/api/data-assets",
            params={
                "limit": 1,
                "skip": 0,
                "include_total": "true",
                "source_system": "SAP"
            },
            timeout=10
        )
        if response.status_code == 200:
            return int(response.headers.get("X-Total-Count", 0))
        return None
    except:
        return None

def main():
    """主函数"""
    print("=" * 60)
    print("语义索引构建进度监控")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total_metadata = get_total_metadata_count()
    if total_metadata:
        print(f"总元数据数: {total_metadata:,}")
    else:
        print("无法获取总元数据数")
    
    print("\n监控进度（每30秒更新一次，按Ctrl+C停止）...")
    print("-" * 60)
    
    start_time = time.time()
    last_count = 0
    
    try:
        while True:
            indexed = get_indexed_count()
            if indexed is not None:
                elapsed = time.time() - start_time
                rate = (indexed - last_count) / 30 if elapsed > 30 else 0
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 已索引: {indexed:,}", end="")
                if total_metadata:
                    percentage = (indexed / total_metadata) * 100
                    print(f" / {total_metadata:,} ({percentage:.2f}%)", end="")
                if rate > 0:
                    remaining = (total_metadata - indexed) / rate if rate > 0 else 0
                    print(f" | 速度: {rate:.1f}/秒 | 预计剩余: {remaining/60:.1f}分钟", end="")
                print()
                
                last_count = indexed
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 无法获取进度...")
            
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\n监控已停止")

if __name__ == "__main__":
    main()


