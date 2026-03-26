#!/usr/bin/env python3
"""
SAP元数据完整构建脚本 - 包含数据库发现
同时从SAP数据库和OData服务发现所有元数据
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


def check_database_connection():
    """检查数据库连接是否可用"""
    print("\n检查SAP数据库连接...")
    try:
        # 尝试调用API，如果数据库连接可用，会返回表信息
        test_body = {
            "include_database": True,
            "include_odata": False,
            "build_semantic_index": False,
            "sync_to_metadata_service": False,
            "limit": 1,
            "offset": 0
        }
        result = make_request(API_URL, test_body, timeout=30)
        tables_discovered = result.get('tables_discovered', 0)
        if tables_discovered > 0:
            print(f"✓ 数据库连接正常，发现 {tables_discovered} 个表")
            return True
        else:
            print("⚠ 数据库连接可能未配置或无法访问")
            return False
    except Exception as e:
        print(f"⚠ 无法检查数据库连接: {e}")
        return False


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
        print(f"无法自动检测服务数: {e}")
    return 348


def discover_from_database():
    """从数据库发现所有表"""
    print("\n" + "="*50)
    print("步骤1: 从SAP数据库发现所有表")
    print("="*50)
    
    try:
        body = {
            "include_database": True,
            "include_odata": False,
            "build_semantic_index": False,
            "sync_to_metadata_service": True
        }
        
        print("开始发现数据库表...")
        request_start = time.time()
        result = make_request(API_URL, body, timeout=3600)  # 数据库发现可能需要更长时间
        request_duration = time.time() - request_start
        
        assets_count = len(result.get('data_assets', []))
        tables_discovered = result.get('tables_discovered', 0)
        entities_count = len(result.get('business_entities', []))
        processes_count = len(result.get('business_processes', []))
        
        sync_result = result.get('metadata', {}).get('sync_result', {})
        assets_result = sync_result.get('data_assets', {})
        entities_result = sync_result.get('business_entities', {})
        
        assets_created = assets_result.get('created', 0)
        assets_failed = assets_result.get('failed', 0)
        entities_created = entities_result.get('created', 0)
        entities_failed = entities_result.get('failed', 0)
        
        print(f"\n✓ 数据库发现完成 (耗时: {request_duration/60:.1f}分钟)")
        print(f"   发现数据资产: {assets_count}")
        print(f"   发现表: {tables_discovered}")
        print(f"   发现业务实体: {entities_count}")
        print(f"   发现业务流程: {processes_count}")
        print(f"   同步数据资产: {assets_created}/{assets_result.get('total', 0)} (失败: {assets_failed})")
        print(f"   同步业务实体: {entities_created}/{entities_result.get('total', 0)} (失败: {entities_failed})")
        
        return {
            'assetsCount': assets_count,
            'tablesCount': tables_discovered,
            'entitiesCount': entities_count,
            'processesCount': processes_count,
            'assetsCreated': assets_created,
            'assetsFailed': assets_failed,
            'entitiesCreated': entities_created,
            'entitiesFailed': entities_failed
        }
    except Exception as e:
        print(f"\n✗ 数据库发现失败: {e}")
        return None


def process_odata_batch(batch, offset, limit, total_batches):
    """处理OData服务批次"""
    batch_num = batch + 1
    print(f"[{batch_num}/{total_batches}] 处理OData批次 {batch} (offset={offset}, limit={limit})...")
    
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
    print("\n" + "="*50)
    print("步骤3: 构建语义索引")
    print("="*50)
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
    print("\n" + "="*50)
    print("SAP元数据完整构建 - 数据库 + OData")
    print("="*50)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    # 检查数据库连接
    db_available = check_database_connection()
    
    # 步骤1: 从数据库发现
    db_result = None
    if db_available:
        db_result = discover_from_database()
        if db_result:
            print(f"\n数据库发现统计:")
            print(f"  - 数据资产: {db_result['assetsCount']}")
            print(f"  - 表: {db_result['tablesCount']}")
            print(f"  - 业务实体: {db_result['entitiesCount']}")
            print(f"  - 业务流程: {db_result['processesCount']}")
    else:
        print("\n⚠ 跳过数据库发现（未配置或无法连接）")
    
    # 步骤2: 从OData服务发现
    print("\n" + "="*50)
    print("步骤2: 从OData服务发现")
    print("="*50)
    
    total_services = get_total_services()
    total_batches = (total_services + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"总服务数: {total_services}")
    print(f"批次大小: {BATCH_SIZE}")
    print(f"总批次数: {total_batches}\n")
    
    completed_batches = 0
    failed_batches = 0
    total_odata_assets = 0
    total_odata_entities = 0
    total_odata_processes = 0
    
    for batch in range(total_batches):
        offset = batch * BATCH_SIZE
        limit = min(BATCH_SIZE, total_services - offset)
        
        result = process_odata_batch(batch, offset, limit, total_batches)
        
        if result:
            total_odata_assets += result['assetsCount']
            total_odata_entities += result['entitiesCount']
            total_odata_processes += result['processesCount']
            completed_batches += 1
            
            if not result['hasMore'] and (offset + limit) >= total_services:
                print("\n  ℹ 所有OData服务已处理完成！")
                break
        else:
            failed_batches += 1
        
        if batch < total_batches - 1:
            time.sleep(2)
        
        if (batch + 1) % 10 == 0:
            elapsed = time.time() - start_time
            print(f"\n--- OData进度报告 ---")
            print(f"已完成: {batch + 1}/{total_batches} 批次")
            print(f"成功: {completed_batches}, 失败: {failed_batches}")
            print(f"累计数据资产: {total_odata_assets}")
            print(f"已用时间: {elapsed / 60:.1f} 分钟")
            print("----------------\n")
    
    # 步骤3: 构建语义索引
    if (db_result and db_result['assetsCount'] > 0) or total_odata_assets > 0:
        build_semantic_index()
    
    # 最终报告
    total_duration = time.time() - start_time
    
    print("\n" + "="*50)
    print("构建完成报告")
    print("="*50)
    
    if db_result:
        print(f"\n数据库发现:")
        print(f"  - 数据资产: {db_result['assetsCount']}")
        print(f"  - 表: {db_result['tablesCount']}")
        print(f"  - 业务实体: {db_result['entitiesCount']}")
        print(f"  - 业务流程: {db_result['processesCount']}")
    
    print(f"\nOData服务发现:")
    print(f"  - 数据资产: {total_odata_assets}")
    print(f"  - 业务实体: {total_odata_entities}")
    print(f"  - 业务流程: {total_odata_processes}")
    print(f"  - 成功批次: {completed_batches}/{total_batches}")
    print(f"  - 失败批次: {failed_batches}")
    
    total_assets = (db_result['assetsCount'] if db_result else 0) + total_odata_assets
    total_entities = (db_result['entitiesCount'] if db_result else 0) + total_odata_entities
    total_processes = (db_result['processesCount'] if db_result else 0) + total_odata_processes
    
    print(f"\n总计:")
    print(f"  - 数据资产: {total_assets}")
    print(f"  - 业务实体: {total_entities}")
    print(f"  - 业务流程: {total_processes}")
    print(f"  - 总耗时: {total_duration / 60:.1f} 分钟")
    print(f"  - 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")
    
    if failed_batches > 0:
        print(f"⚠ 有 {failed_batches} 个批次失败，请检查日志")
    else:
        print("✓ 所有元数据构建成功！")


if __name__ == "__main__":
    main()



