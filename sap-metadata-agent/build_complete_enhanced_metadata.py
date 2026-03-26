#!/usr/bin/env python3
"""
SAP元数据完整构建脚本（增强版）
包含所有新功能：ABAP字典、业务术语映射、语义关系
确保分批构建，不一次性构建所有
"""
import json
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 尝试导入requests，如果失败则使用urllib
try:
    import requests
    USE_REQUESTS = True
except ImportError:
    USE_REQUESTS = False
    import urllib.request
    import urllib.parse

# 配置
API_URL = "http://localhost:8015/api/sap-metadata/discover"
STATUS_FILE = Path("build_enhanced_status.json")
BATCH_SIZE = 10
MAX_RETRIES = 3
RETRY_DELAY = 5
REQUEST_TIMEOUT = 600


class Colors:
    """终端颜色"""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    RESET = '\033[0m'


def print_color(message: str, color: str = Colors.WHITE):
    """打印彩色消息（处理Windows编码问题）"""
    try:
        print(f"{color}{message}{Colors.RESET}")
    except UnicodeEncodeError:
        # Windows GBK编码问题，移除特殊字符
        safe_message = message.encode('ascii', 'ignore').decode('ascii')
        print(f"{color}{safe_message}{Colors.RESET}")


def make_request(url: str, data: dict, timeout: int = 30) -> dict:
    """发送HTTP请求（支持requests和urllib）"""
    if USE_REQUESTS:
        response = requests.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        return response.json()
    else:
        # 使用urllib
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))


def check_database_connection() -> bool:
    """检查数据库连接是否可用"""
    print_color("\n检查SAP数据库连接...", Colors.CYAN)
    try:
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
            print_color(f"[OK] 数据库连接正常，发现 {tables_discovered} 个表", Colors.GREEN)
            return True
        else:
            print_color("[WARN] 数据库连接可能未配置或无法访问", Colors.YELLOW)
            return False
    except Exception as e:
        print_color(f"[WARN] 无法检查数据库连接: {e}", Colors.YELLOW)
        return False


def get_total_services() -> int:
    """获取总服务数"""
    print_color("\n正在检测SAP OData服务总数...", Colors.CYAN)
    try:
        test_body = {
            "include_database": False,
            "include_odata": True,
            "build_semantic_index": False,
            "sync_to_metadata_service": False,
            "limit": 1,  # 只获取1个服务用于检测总数
            "offset": 0
        }
        
        result = make_request(API_URL, test_body, timeout=60)
        
        total_services = result.get('metadata', {}).get('total_services')
        if total_services and total_services > 0:
            print_color(f"检测到总服务数: {total_services}", Colors.GREEN)
            return total_services
    except Exception as e:
        print_color(f"无法自动检测服务数: {e}，使用默认值348", Colors.YELLOW)
    
    return 348


def process_batch(
    batch: int,
    offset: int,
    limit: int,
    total_batches: int,
    include_database: bool = False
) -> Optional[Dict[str, Any]]:
    """处理单个批次（确保分批构建，不一次性构建所有）"""
    batch_num = batch + 1
    print_color(
        f"[{batch_num}/{total_batches}] 处理批次 {batch} (offset={offset}, limit={limit})...",
        Colors.YELLOW
    )
    
    # 确保分批构建：每批只处理limit个服务，不设置limit=None
    body = {
        "include_database": include_database and (batch == 0),  # 只在第一批次包含数据库
        "include_odata": True,
        "build_semantic_index": False,  # 最后统一构建
        "sync_to_metadata_service": True,
        "limit": limit,  # 明确限制每批处理数量
        "offset": offset  # 明确指定偏移量
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            start_time = time.time()
            # 确保分批构建：明确指定limit和offset
            result = make_request(API_URL, body, timeout=REQUEST_TIMEOUT)
            duration = time.time() - start_time
            
            assets = len(result.get('data_assets', []))
            entities = len(result.get('business_entities', []))
            processes = len(result.get('business_processes', []))
            term_mappings = len(result.get('metadata', {}).get('term_mappings', []))
            semantic_rels = len(result.get('metadata', {}).get('semantic_relationships', []))
            
            sync = result.get('metadata', {}).get('sync_result', {})
            assets_sync = sync.get('data_assets', {})
            
            print_color(
                f"  [OK] 完成 (耗时: {duration:.1f}s) - "
                f"资产: {assets}, 实体: {entities}, 流程: {processes}, "
                f"术语映射: {term_mappings}, 语义关系: {semantic_rels}",
                Colors.GREEN
            )
            print_color(
                f"    同步: {assets_sync.get('created', 0)}/{assets_sync.get('total', 0)} 资产",
                Colors.CYAN
            )
            
            return {
                "assets": assets,
                "entities": entities,
                "processes": processes,
                "term_mappings": term_mappings,
                "semantic_relationships": semantic_rels,
                "sync_created": assets_sync.get('created', 0),
                "duration": duration
            }
            
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                print_color(f"  [WARN] 超时 (尝试 {attempt + 1}/{MAX_RETRIES})", Colors.YELLOW)
            else:
                print_color(f"  [ERROR] 失败: {e} (尝试 {attempt + 1}/{MAX_RETRIES})", Colors.RED)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    print_color(f"  [ERROR] 批次 {batch} 最终失败", Colors.RED)
    return None


def build_database_metadata() -> Optional[Dict[str, Any]]:
    """构建数据库元数据（包含ABAP字典）"""
    print_color("\n" + "="*60, Colors.CYAN)
    print_color("步骤1: 从SAP数据库发现所有表（包含ABAP字典信息）", Colors.CYAN)
    print_color("="*60, Colors.CYAN)
    
    try:
        body = {
            "include_database": True,
            "include_odata": False,
            "build_semantic_index": False,
            "sync_to_metadata_service": True
        }
        
        print_color("开始发现数据库表（包含ABAP字典信息）...", Colors.YELLOW)
        print_color("注意：数据库发现会处理所有表，可能需要较长时间", Colors.YELLOW)
        start = time.time()
        result = make_request(API_URL, body, timeout=3600)
        duration = time.time() - start
        
        assets = len(result.get('data_assets', []))
        tables = result.get('tables_discovered', 0)
        entities = len(result.get('business_entities', []))
        processes = len(result.get('business_processes', []))
        term_mappings = len(result.get('metadata', {}).get('term_mappings', []))
        semantic_rels = len(result.get('metadata', {}).get('semantic_relationships', []))
        
        sync = result.get('metadata', {}).get('sync_result', {})
        assets_sync = sync.get('data_assets', {})
        entities_sync = sync.get('business_entities', {})
        
        print_color(f"\n[OK] 数据库发现完成 (耗时: {duration/60:.1f}分钟)", Colors.GREEN)
        print_color(f"   发现数据资产: {assets}", Colors.WHITE)
        print_color(f"   发现表: {tables}", Colors.WHITE)
        print_color(f"   发现业务实体: {entities}", Colors.WHITE)
        print_color(f"   发现业务流程: {processes}", Colors.WHITE)
        print_color(f"   业务术语映射: {term_mappings}", Colors.WHITE)
        print_color(f"   语义关系: {semantic_rels}", Colors.WHITE)
        print_color(f"   同步数据资产: {assets_sync.get('created', 0)}/{assets_sync.get('total', 0)}", Colors.WHITE)
        print_color(f"   同步业务实体: {entities_sync.get('created', 0)}/{entities_sync.get('total', 0)}", Colors.WHITE)
        
        return {
            'assets': assets,
            'tables': tables,
            'entities': entities,
            'processes': processes,
            'term_mappings': term_mappings,
            'semantic_relationships': semantic_rels
        }
    except Exception as e:
        print_color(f"[ERROR] 数据库发现失败: {e}", Colors.RED)
        return None


def build_semantic_index() -> bool:
    """构建语义索引"""
    print_color("\n" + "="*60, Colors.CYAN)
    print_color("步骤3: 构建语义索引", Colors.CYAN)
    print_color("="*60, Colors.CYAN)
    
    try:
        body = {
            "include_database": False,
            "include_odata": False,
            "build_semantic_index": True,
            "sync_to_metadata_service": False,
            "limit": None,
            "offset": 0
        }
        
        print_color("开始构建语义索引...", Colors.YELLOW)
        start = time.time()
        result = make_request(API_URL, body, timeout=1800)
        duration = time.time() - start
        
        index_result = result.get('metadata', {}).get('semantic_index', {})
        indexed = index_result.get('indexed', 0)
        failed = index_result.get('failed', 0)
        
        print_color(f"\n[OK] 语义索引构建完成 (耗时: {duration/60:.1f}分钟)", Colors.GREEN)
        print_color(f"   索引成功: {indexed}", Colors.WHITE)
        print_color(f"   索引失败: {failed}", Colors.YELLOW if failed > 0 else Colors.WHITE)
        
        return indexed > 0
    except Exception as e:
        print_color(f"[ERROR] 语义索引构建失败: {e}", Colors.RED)
        return False


def verify_metadata() -> Optional[Dict[str, Any]]:
    """验证元数据同步状态"""
    print_color("\n" + "="*60, Colors.CYAN)
    print_color("步骤4: 验证元数据同步", Colors.CYAN)
    print_color("="*60, Colors.CYAN)
    
    try:
        metadata_url = "http://localhost:8005/api/data-assets?limit=1&include_total=True"
        if USE_REQUESTS:
            response = requests.get(metadata_url, timeout=30)
            response.raise_for_status()
            total_assets = int(response.headers.get('X-Total-Count', 0))
        else:
            req = urllib.request.Request(metadata_url)
            with urllib.request.urlopen(req, timeout=30) as response:
                headers = dict(response.headers)
                total_assets = int(headers.get('X-Total-Count', 0))
        
        print_color(f"\n[OK] 元数据验证完成", Colors.GREEN)
        print_color(f"   metadata-service中的数据资产总数: {total_assets}", Colors.WHITE)
        
        return {"total_assets": total_assets}
    except Exception as e:
        print_color(f"[WARN] 验证失败: {e}", Colors.YELLOW)
        return None


def main():
    """主程序"""
    print_color("\n" + "="*60, Colors.CYAN)
    print_color("SAP元数据完整构建（增强版）", Colors.CYAN)
    print_color("包含: ABAP字典、业务术语映射、语义关系", Colors.CYAN)
    print_color("="*60, Colors.CYAN)
    print_color(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", Colors.WHITE)
    
    start_time = time.time()
    
    # 步骤1: 数据库发现（如果可用）
    db_available = check_database_connection()
    db_result = None
    if db_available:
        db_result = build_database_metadata()
    
    # 步骤2: OData服务发现（分批处理）
    print_color("\n" + "="*60, Colors.CYAN)
    print_color("步骤2: 从OData服务发现（包含业务术语和语义关系）", Colors.CYAN)
    print_color("="*60, Colors.CYAN)
    
    total_services = get_total_services()
    total_batches = (total_services + BATCH_SIZE - 1) // BATCH_SIZE
    
    print_color(f"总服务数: {total_services}", Colors.WHITE)
    print_color(f"批次大小: {BATCH_SIZE}", Colors.WHITE)
    print_color(f"总批次数: {total_batches}\n", Colors.WHITE)
    
    completed_batches = 0
    failed_batches = 0
    total_odata_assets = 0
    total_odata_entities = 0
    total_odata_processes = 0
    total_term_mappings = 0
    total_semantic_rels = 0
    
    # 确保分批构建：每批只处理BATCH_SIZE个服务
    for batch in range(total_batches):
        offset = batch * BATCH_SIZE
        # 确保limit不超过剩余服务数，且不超过BATCH_SIZE
        remaining_services = total_services - offset
        limit = min(BATCH_SIZE, remaining_services)
        
        if limit <= 0:
            print_color(f"批次 {batch} 跳过（无剩余服务）", Colors.YELLOW)
            break
        
        print_color(f"\n处理批次 {batch + 1}/{total_batches}: offset={offset}, limit={limit} (剩余: {remaining_services})", Colors.CYAN)
        
        result = process_batch(
            batch,
            offset,
            limit,  # 明确限制每批处理数量
            total_batches,
            include_database=False  # 数据库已在步骤1处理
        )
        
        if result:
            completed_batches += 1
            total_odata_assets += result['assets']
            total_odata_entities += result['entities']
            total_odata_processes += result['processes']
            total_term_mappings += result.get('term_mappings', 0)
            total_semantic_rels += result.get('semantic_relationships', 0)
        else:
            failed_batches += 1
        
        # 短暂延迟，避免过载
        if batch < total_batches - 1:
            time.sleep(2)  # 增加延迟，确保分批处理
    
    # 步骤3: 构建语义索引
    index_success = build_semantic_index()
    
    # 步骤4: 验证
    verify_result = verify_metadata()
    
    # 最终报告
    total_duration = time.time() - start_time
    
    print_color("\n" + "="*60, Colors.CYAN)
    print_color("构建完成报告", Colors.CYAN)
    print_color("="*60, Colors.CYAN)
    
    if db_result:
        print_color(f"\n数据库发现:", Colors.GREEN)
        print_color(f"  - 数据资产: {db_result['assets']}", Colors.WHITE)
        print_color(f"  - 表: {db_result['tables']}", Colors.WHITE)
        print_color(f"  - 业务实体: {db_result['entities']}", Colors.WHITE)
        print_color(f"  - 业务流程: {db_result['processes']}", Colors.WHITE)
        print_color(f"  - 业务术语映射: {db_result['term_mappings']}", Colors.WHITE)
        print_color(f"  - 语义关系: {db_result['semantic_relationships']}", Colors.WHITE)
    
    print_color(f"\nOData服务发现:", Colors.GREEN)
    print_color(f"  - 完成批次: {completed_batches}/{total_batches}", Colors.WHITE)
    print_color(f"  - 失败批次: {failed_batches}", Colors.YELLOW if failed_batches > 0 else Colors.WHITE)
    print_color(f"  - 数据资产: {total_odata_assets}", Colors.WHITE)
    print_color(f"  - 业务实体: {total_odata_entities}", Colors.WHITE)
    print_color(f"  - 业务流程: {total_odata_processes}", Colors.WHITE)
    print_color(f"  - 业务术语映射: {total_term_mappings}", Colors.WHITE)
    print_color(f"  - 语义关系: {total_semantic_rels}", Colors.WHITE)
    
    total_assets = (db_result['assets'] if db_result else 0) + total_odata_assets
    total_entities = (db_result['entities'] if db_result else 0) + total_odata_entities
    total_processes = (db_result['processes'] if db_result else 0) + total_odata_processes
    total_term_mappings_all = (db_result.get('term_mappings', 0) if db_result else 0) + total_term_mappings
    total_semantic_rels_all = (db_result.get('semantic_relationships', 0) if db_result else 0) + total_semantic_rels
    
    print_color(f"\n总计:", Colors.CYAN)
    print_color(f"  - 数据资产: {total_assets}", Colors.WHITE)
    print_color(f"  - 业务实体: {total_entities}", Colors.WHITE)
    print_color(f"  - 业务流程: {total_processes}", Colors.WHITE)
    print_color(f"  - 业务术语映射: {total_term_mappings_all}", Colors.WHITE)
    print_color(f"  - 语义关系: {total_semantic_rels_all}", Colors.WHITE)
    print_color(f"  - 语义索引: {'✓ 完成' if index_success else '⚠ 部分失败'}", Colors.GREEN if index_success else Colors.YELLOW)
    
    if verify_result:
        print_color(f"  - metadata-service中的资产: {verify_result['total_assets']}", Colors.WHITE)
    
    print_color(f"\n总耗时: {total_duration/60:.1f} 分钟", Colors.CYAN)
    print_color(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.CYAN)
    
    print_color("\n[OK] 元数据构建完成！现在可以测试任务编排功能。", Colors.GREEN)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_color("\n\n⚠ 构建被用户中断", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_color(f"\n\n✗ 构建失败: {e}", Colors.RED)
        sys.exit(1)

