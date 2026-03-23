#!/usr/bin/env python3
"""
完整构建所有SAP元数据 - 确保所有步骤都完成
"""
import json
import time
import urllib.request
from datetime import datetime

API_URL = "http://localhost:8015/api/sap-metadata/discover"
METADATA_URL = "http://localhost:8005/api/data-assets"


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


def check_database():
    """检查数据库连接"""
    print("\n检查SAP数据库连接...")
    try:
        body = {
            "include_database": True,
            "include_odata": False,
            "build_semantic_index": False,
            "sync_to_metadata_service": False,
            "limit": 1
        }
        result = make_request(API_URL, body, timeout=30)
        tables = result.get('tables_discovered', 0)
        if tables > 0:
            print(f"✓ 数据库连接正常，发现 {tables} 个表")
            return True
        else:
            print("⚠ 数据库未配置或无法连接")
            return False
    except:
        print("⚠ 数据库未配置或无法连接")
        return False


def build_database_metadata():
    """构建数据库元数据"""
    print("\n" + "="*60)
    print("步骤1: 从SAP数据库发现所有表")
    print("="*60)
    
    try:
        body = {
            "include_database": True,
            "include_odata": False,
            "build_semantic_index": False,
            "sync_to_metadata_service": True
        }
        
        print("开始发现数据库表...")
        start = time.time()
        result = make_request(API_URL, body, timeout=3600)
        duration = time.time() - start
        
        assets = len(result.get('data_assets', []))
        tables = result.get('tables_discovered', 0)
        entities = len(result.get('business_entities', []))
        processes = len(result.get('business_processes', []))
        
        sync = result.get('metadata', {}).get('sync_result', {})
        assets_sync = sync.get('data_assets', {})
        entities_sync = sync.get('business_entities', {})
        
        print(f"\n✓ 数据库发现完成 (耗时: {duration/60:.1f}分钟)")
        print(f"   发现数据资产: {assets}")
        print(f"   发现表: {tables}")
        print(f"   发现业务实体: {entities}")
        print(f"   发现业务流程: {processes}")
        print(f"   同步数据资产: {assets_sync.get('created', 0)}/{assets_sync.get('total', 0)}")
        print(f"   同步业务实体: {entities_sync.get('created', 0)}/{entities_sync.get('total', 0)}")
        
        return {'assets': assets, 'tables': tables, 'entities': entities, 'processes': processes}
    except Exception as e:
        print(f"✗ 数据库发现失败: {e}")
        return None


def build_odata_metadata():
    """构建OData元数据"""
    print("\n" + "="*60)
    print("步骤2: 从OData服务发现元数据")
    print("="*60)
    
    # 获取总服务数
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
        total_services = result.get('metadata', {}).get('total_services', 348)
    except:
        total_services = 348
    
    print(f"总服务数: {total_services}")
    
    # 检查已同步的数据资产数量
    try:
        response = urllib.request.urlopen(f"{METADATA_URL}?limit=1", timeout=10)
        data = json.loads(response.read().decode('utf-8'))
        if isinstance(data, list) and len(data) > 0:
            # 获取总数
            total_synced = 0
            try:
                # 尝试获取总数
                count_url = f"{METADATA_URL}?source_system=SAP&limit=1"
                count_resp = urllib.request.urlopen(count_url, timeout=10)
                count_data = json.loads(count_resp.read().decode('utf-8'))
                # 如果有total字段
                if isinstance(count_data, dict) and 'total' in count_data:
                    total_synced = count_data['total']
            except:
                pass
            
            if total_synced > 0:
                print(f"已同步数据资产: {total_synced}")
                if total_synced >= 20000:
                    print("✓ OData元数据已构建完成，跳过重复构建")
                    return {'assets': total_synced, 'entities': 0, 'processes': 0}
    except:
        pass
    
    # 如果已构建完成，跳过
    print("⚠ 检测到可能已有元数据，继续构建以确保完整...")
    
    batch_size = 10
    total_batches = (total_services + batch_size - 1) // batch_size
    total_assets = 0
    total_entities = 0
    total_processes = 0
    completed = 0
    
    for batch in range(total_batches):
        offset = batch * batch_size
        limit = min(batch_size, total_services - offset)
        
        print(f"[{batch+1}/{total_batches}] 处理批次 {batch} (offset={offset}, limit={limit})...")
        
        try:
            body = {
                "include_database": False,
                "include_odata": True,
                "build_semantic_index": False,
                "sync_to_metadata_service": True,
                "limit": limit,
                "offset": offset
            }
            
            start = time.time()
            result = make_request(API_URL, body, timeout=600)
            duration = time.time() - start
            
            assets = len(result.get('data_assets', []))
            entities = len(result.get('business_entities', []))
            processes = len(result.get('business_processes', []))
            
            total_assets += assets
            total_entities += entities
            total_processes += processes
            completed += 1
            
            print(f"  ✓ 完成 (耗时: {duration:.1f}秒) - 资产: {assets}, 实体: {entities}, 流程: {processes}")
            
            if not result.get('metadata', {}).get('has_more', False) and (offset + limit) >= total_services:
                break
            
            time.sleep(1)
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            continue
        
        if (batch + 1) % 10 == 0:
            print(f"\n--- 进度: {batch+1}/{total_batches} 批次, 累计资产: {total_assets} ---\n")
    
    return {'assets': total_assets, 'entities': total_entities, 'processes': total_processes}


def build_semantic_index():
    """构建语义索引"""
    print("\n" + "="*60)
    print("步骤3: 构建语义索引")
    print("="*60)
    
    try:
        body = {
            "include_database": False,
            "include_odata": False,
            "build_semantic_index": True,
            "sync_to_metadata_service": False
        }
        
        print("开始构建语义索引...")
        start = time.time()
        result = make_request(API_URL, body, timeout=3600)
        duration = time.time() - start
        
        index_result = result.get('metadata', {}).get('semantic_index', {})
        indexed = index_result.get('indexed', 0)
        failed = index_result.get('failed', 0)
        
        print(f"\n✓ 语义索引构建完成 (耗时: {duration/60:.1f}分钟)")
        print(f"   已索引文档: {indexed}")
        print(f"   失败: {failed}")
        
        if failed > 0:
            print(f"⚠ 有 {failed} 个文档索引失败，可能需要检查知识库服务")
        
        return indexed > 0
    except Exception as e:
        print(f"✗ 语义索引构建失败: {e}")
        print("⚠ 这可能是知识库服务未运行或配置问题，但不影响元数据发现")
        return False


def verify_metadata():
    """验证元数据同步"""
    print("\n" + "="*60)
    print("步骤4: 验证元数据同步")
    print("="*60)
    
    try:
        # 检查数据资产
        response = urllib.request.urlopen(f"{METADATA_URL}?source_system=SAP&limit=1", timeout=30)
        data = json.loads(response.read().decode('utf-8'))
        
        if isinstance(data, list):
            total_assets = len(data)
            print(f"✓ 元数据服务中的数据资产: {total_assets} (样本)")
        elif isinstance(data, dict) and 'total' in data:
            total_assets = data['total']
            print(f"✓ 元数据服务中的数据资产: {total_assets}")
        else:
            print("⚠ 无法获取数据资产总数")
            total_assets = 0
        
        # 检查业务实体
        try:
            entities_url = "http://localhost:8005/api/business-entities?limit=1"
            entities_resp = urllib.request.urlopen(entities_url, timeout=30)
            entities_data = json.loads(entities_resp.read().decode('utf-8'))
            
            if isinstance(entities_data, list):
                total_entities = len(entities_data)
            elif isinstance(entities_data, dict) and 'total' in entities_data:
                total_entities = entities_data['total']
            else:
                total_entities = 0
            
            print(f"✓ 元数据服务中的业务实体: {total_entities}")
        except:
            print("⚠ 无法获取业务实体总数")
            total_entities = 0
        
        return {'assets': total_assets, 'entities': total_entities}
    except Exception as e:
        print(f"⚠ 验证失败: {e}")
        return None


def main():
    """主程序"""
    print("\n" + "="*60)
    print("SAP元数据完整构建")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    start_time = time.time()
    
    # 步骤1: 数据库发现
    db_available = check_database()
    db_result = None
    if db_available:
        db_result = build_database_metadata()
    
    # 步骤2: OData发现
    odata_result = build_odata_metadata()
    
    # 步骤3: 语义索引
    index_success = build_semantic_index()
    
    # 步骤4: 验证
    verify_result = verify_metadata()
    
    # 最终报告
    total_duration = time.time() - start_time
    
    print("\n" + "="*60)
    print("构建完成报告")
    print("="*60)
    
    if db_result:
        print(f"\n数据库发现:")
        print(f"  - 数据资产: {db_result['assets']}")
        print(f"  - 表: {db_result['tables']}")
        print(f"  - 业务实体: {db_result['entities']}")
        print(f"  - 业务流程: {db_result['processes']}")
    
    print(f"\nOData服务发现:")
    print(f"  - 数据资产: {odata_result['assets']}")
    print(f"  - 业务实体: {odata_result['entities']}")
    print(f"  - 业务流程: {odata_result['processes']}")
    
    total_assets = (db_result['assets'] if db_result else 0) + odata_result['assets']
    total_entities = (db_result['entities'] if db_result else 0) + odata_result['entities']
    total_processes = (db_result['processes'] if db_result else 0) + odata_result['processes']
    
    print(f"\n总计:")
    print(f"  - 数据资产: {total_assets}")
    print(f"  - 业务实体: {total_entities}")
    print(f"  - 业务流程: {total_processes}")
    print(f"  - 语义索引: {'✓ 完成' if index_success else '⚠ 部分失败'}")
    
    if verify_result:
        print(f"\n元数据服务验证:")
        print(f"  - 已同步数据资产: {verify_result['assets']}")
        print(f"  - 已同步业务实体: {verify_result['entities']}")
    
    print(f"\n总耗时: {total_duration / 60:.1f} 分钟")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    if total_assets > 0:
        print("✓ SAP元数据构建完成！")
    else:
        print("⚠ 未发现任何元数据，请检查配置")


if __name__ == "__main__":
    main()



