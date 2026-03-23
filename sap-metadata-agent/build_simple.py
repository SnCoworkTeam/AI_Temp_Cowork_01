#!/usr/bin/env python3
"""
SAP元数据构建脚本 - 简化版（使用内置库）
"""
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime

API_URL = "http://localhost:8015/api/sap-metadata/discover"
STATUS_FILE = "build_status.json"
BATCH_SIZE = 10
MAX_RETRIES = 3
RETRY_DELAY = 5


def make_request(url, data=None, timeout=600):
    """发送HTTP请求"""
    if data:
        data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    else:
        req = urllib.request.Request(url)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        raise Exception(f"Request failed: {e}")


def get_total_services():
    """获取总服务数"""
    print("\n正在检测SAP OData服务总数...")
    try:
        test_body = {
            "include_database": False,
            "include_odata": True,
            "build_semantic_index": False,
            "sync_to_metadata_service": False,
            "limit": 1,
            "offset": 0
        }
        result = make_request(API_URL, test_body, timeout=60)
        total_services = result.get('metadata', {}).get('total_services')
        if total_services and total_services > 0:
            print(f"检测到总服务数: {total_services}")
            return total_services
    except Exception as e:
        print(f"无法自动检测服务数: {e}，使用默认值348")
    return 348


def process_batch(batch, offset, limit, total_batches):
    """处理单个批次"""
    batch_num = batch + 1
    print(f"[{batch_num}/{total_batches}] 处理批次 {batch} (offset={offset}, limit={limit})...")
    
    body = {
        "include_database": False,
        "include_odata": True,
        "build_semantic_index": False,
        "sync_to_metadata_service": True,
        "limit": limit,
        "offset": offset
    }
    
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            request_start = time.time()
            result = make_request(API_URL, body, timeout=600)
            request_duration = time.time() - request_start
            
            assets_count = len(result.get('data_assets', []))
            entities_count = len(result.get('business_entities', []))
            processes_count = len(result.get('business_processes', []))
            
            sync_result = result.get('metadata', {}).get('sync_result', {})
            assets_result = sync_result.get('data_assets', {})
            entities_result = sync_result.get('business_entities', {})
            
            assets_created = assets_result.get('created', 0)
            assets_failed = assets_result.get('failed', 0)
            entities_created = entities_result.get('created', 0)
            entities_failed = entities_result.get('failed', 0)
            
            print(f"  ✓ 成功完成 (耗时: {request_duration:.1f}秒)")
            print(f"     发现数据资产: {assets_count}")
            print(f"     发现业务实体: {entities_count}")
            print(f"     发现业务流程: {processes_count}")
            print(f"     同步数据资产: {assets_created}/{assets_result.get('total', 0)} (失败: {assets_failed})")
            print(f"     同步业务实体: {entities_created}/{entities_result.get('total', 0)} (失败: {entities_failed})")
            
            return {
                'assetsCount': assets_count,
                'entitiesCount': entities_count,
                'processesCount': processes_count,
                'assetsCreated': assets_created,
                'assetsFailed': assets_failed,
                'entitiesCreated': entities_created,
                'entitiesFailed': entities_failed,
                'hasMore': result.get('metadata', {}).get('has_more', False)
            }
        except Exception as e:
            retry_count += 1
            if retry_count < MAX_RETRIES:
                print(f"  ⚠ 失败 (尝试 {retry_count}/{MAX_RETRIES}): {e}")
                print(f"     等待 {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  ✗ 最终失败: {e}")
                return None
    
    return None


def build_semantic_index():
    """构建语义索引"""
    print("\n开始构建语义索引...")
    try:
        body = {
            "include_database": False,
            "include_odata": False,
            "build_semantic_index": True,
            "sync_to_metadata_service": False
        }
        result = make_request(API_URL, body, timeout=1800)
        index_result = result.get('metadata', {}).get('semantic_index', {})
        indexed = index_result.get('indexed', 0)
        failed = index_result.get('failed', 0)
        print(f"  ✓ 语义索引构建完成")
        print(f"     已索引文档: {indexed}")
        print(f"     失败: {failed}")
        return True
    except Exception as e:
        print(f"  ⚠ 语义索引构建失败: {e}")
        return False


def main():
    """主程序"""
    print("\n========================================")
    print("SAP元数据完整构建")
    print("========================================")
    
    # 获取总服务数
    total_services = get_total_services()
    total_batches = (total_services + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"总服务数: {total_services}")
    print(f"批次大小: {BATCH_SIZE}")
    print(f"总批次数: {total_batches}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("========================================\n")
    
    start_time = time.time()
    completed_batches = 0
    failed_batches = 0
    total_assets = 0
    total_entities = 0
    total_processes = 0
    
    # 处理所有批次
    for batch in range(total_batches):
        offset = batch * BATCH_SIZE
        limit = min(BATCH_SIZE, total_services - offset)
        
        result = process_batch(batch, offset, limit, total_batches)
        
        if result:
            total_assets += result['assetsCount']
            total_entities += result['entitiesCount']
            total_processes += result['processesCount']
            completed_batches += 1
            
            if not result['hasMore'] and (offset + limit) >= total_services:
                print("\n  ℹ 所有服务已处理完成！")
                break
        else:
            failed_batches += 1
        
        if batch < total_batches - 1:
            time.sleep(2)
        
        if (batch + 1) % 10 == 0:
            elapsed = time.time() - start_time
            print(f"\n--- 进度报告 ---")
            print(f"已完成: {batch + 1}/{total_batches} 批次")
            print(f"成功: {completed_batches}, 失败: {failed_batches}")
            print(f"累计数据资产: {total_assets}")
            print(f"累计业务实体: {total_entities}")
            print(f"累计业务流程: {total_processes}")
            print(f"已用时间: {elapsed / 60:.1f} 分钟")
            print("----------------\n")
    
    total_duration = time.time() - start_time
    
    print("\n========================================")
    print("批次构建完成")
    print("========================================")
    print(f"总批次数: {total_batches}")
    print(f"成功批次: {completed_batches}")
    print(f"失败批次: {failed_batches}")
    print(f"累计数据资产: {total_assets}")
    print(f"累计业务实体: {total_entities}")
    print(f"累计业务流程: {total_processes}")
    print(f"总耗时: {total_duration / 60:.1f} 分钟")
    print("========================================\n")
    
    # 构建语义索引
    if completed_batches > 0:
        build_semantic_index()
    
    # 最终报告
    print("\n========================================")
    print("构建完成报告")
    print("========================================")
    print(f"数据资产发现: {total_assets}")
    print(f"业务实体提取: {total_entities}")
    print(f"业务流程分析: {total_processes}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("========================================\n")
    
    if failed_batches > 0:
        print(f"⚠ 有 {failed_batches} 个批次失败，请检查日志")
    else:
        print("✓ 所有元数据构建成功！")


if __name__ == "__main__":
    main()



