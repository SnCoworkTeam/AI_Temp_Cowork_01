"""
分批构建语义索引
避免一次性处理所有109,022个资产导致超时
"""
import requests
import time
import json
from datetime import datetime
from typing import Optional

API_URL = "http://localhost:8015/api/sap-metadata/discover"
BATCH_SIZE = 50  # 每批处理的资产数量
MAX_RETRIES = 3
RETRY_DELAY = 2

def get_total_assets() -> int:
    """获取SAP资产总数"""
    try:
        # 尝试获取总数（通过获取大量数据来估算）
        response = requests.get(
            "http://localhost:8005/api/data-assets",
            params={"limit": 10000, "source_system": "SAP"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 0
            # 如果返回了10000个，说明可能还有更多
            if count == 10000:
                return 109022  # 使用之前检查到的数量
            return count
        return 109022
    except:
        return 109022


def build_batch(offset: int, limit: int, batch_num: int, total_batches: int) -> Optional[dict]:
    """构建一批语义索引"""
    print(f"\n[{batch_num + 1}/{total_batches}] 处理批次 (offset={offset}, limit={limit})...")
    
    for attempt in range(MAX_RETRIES):
        try:
            start_time = time.time()
            
            response = requests.post(
                API_URL,
                json={
                    "include_database": False,
                    "include_odata": False,
                    "include_bapi": False,
                    "build_semantic_index": True,
                    "sync_to_metadata_service": False,
                    "limit": limit,
                    "offset": offset
                },
                timeout=300  # 5分钟超时
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                semantic_index = result.get("metadata", {}).get("semantic_index", {})
                data_assets = result.get("data_assets", [])
                
                indexed = semantic_index.get("indexed", 0)
                failed = semantic_index.get("failed", 0)
                
                print(f"  [OK] 完成 (耗时: {duration:.1f}秒)")
                print(f"    加载资产: {len(data_assets)}")
                print(f"    索引成功: {indexed}")
                print(f"    索引失败: {failed}")
                
                return {
                    "indexed": indexed,
                    "failed": failed,
                    "assets_loaded": len(data_assets),
                    "duration": duration
                }
            else:
                print(f"  [ERROR] HTTP {response.status_code}: {response.text[:200]}")
                if attempt < MAX_RETRIES - 1:
                    print(f"    重试 {attempt + 1}/{MAX_RETRIES}...")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    return None
                    
        except requests.exceptions.Timeout:
            print(f"  [TIMEOUT] 请求超时")
            if attempt < MAX_RETRIES - 1:
                print(f"    重试 {attempt + 1}/{MAX_RETRIES}...")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return None
        except Exception as e:
            print(f"  [ERROR] 错误: {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"    重试 {attempt + 1}/{MAX_RETRIES}...")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return None
    
    return None


def main():
    """主函数"""
    print("=" * 80)
    print("分批构建语义索引")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 获取总数
    print("正在获取SAP资产总数...")
    total_assets = get_total_assets()
    print(f"找到 {total_assets:,} 个SAP资产\n")
    
    # 计算批次数
    total_batches = (total_assets + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"批次大小: {BATCH_SIZE}")
    print(f"总批次数: {total_batches}")
    print(f"预计总时间: 约 {total_batches * 5 / 60:.1f} 分钟\n")
    
    # 统计信息
    total_indexed = 0
    total_failed = 0
    total_assets_loaded = 0
    completed_batches = 0
    failed_batches = 0
    start_time = time.time()
    
    # 处理所有批次
    for batch in range(total_batches):
        offset = batch * BATCH_SIZE
        limit = min(BATCH_SIZE, total_assets - offset)
        
        if limit <= 0:
            break
        
        result = build_batch(offset, limit, batch, total_batches)
        
        if result:
            total_indexed += result["indexed"]
            total_failed += result["failed"]
            total_assets_loaded += result["assets_loaded"]
            completed_batches += 1
        else:
            failed_batches += 1
        
        # 批次间延迟
        if batch < total_batches - 1:
            time.sleep(1)
        
        # 每10个批次显示一次进度
        if (batch + 1) % 10 == 0:
            elapsed = time.time() - start_time
            progress = ((batch + 1) / total_batches) * 100
            avg_time_per_batch = elapsed / (batch + 1)
            remaining_batches = total_batches - (batch + 1)
            eta = remaining_batches * avg_time_per_batch
            
            print(f"\n进度: {batch + 1}/{total_batches} ({progress:.1f}%)")
            print(f"已索引: {total_indexed:,} | 失败: {total_failed:,}")
            print(f"预计剩余时间: {eta / 60:.1f} 分钟\n")
    
    # 最终报告
    total_duration = time.time() - start_time
    print("\n" + "=" * 80)
    print("构建完成")
    print("=" * 80)
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {total_duration / 60:.1f} 分钟")
    print(f"\n统计:")
    print(f"  完成批次: {completed_batches}/{total_batches}")
    print(f"  失败批次: {failed_batches}")
    print(f"  加载资产: {total_assets_loaded:,}")
    print(f"  索引成功: {total_indexed:,}")
    print(f"  索引失败: {total_failed:,}")
    
    if total_indexed > 0:
        success_rate = (total_indexed / (total_indexed + total_failed)) * 100 if (total_indexed + total_failed) > 0 else 0
        print(f"  成功率: {success_rate:.1f}%")
        print(f"\n[SUCCESS] 语义索引构建完成！")
    else:
        print(f"\n[WARNING] 没有文档被成功索引")
    
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] 构建已中断")
        print("   可以使用断点续传功能继续构建")
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()

