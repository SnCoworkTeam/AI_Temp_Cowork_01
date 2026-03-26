#!/usr/bin/env python3
"""
SAP元数据完整构建脚本
自动检测总服务数，处理所有批次，确保所有元数据构建完成
"""
import json
import time
import requests
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 配置
API_URL = "http://localhost:8015/api/sap-metadata/discover"
STATUS_FILE = Path("build_status.json")
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
    """打印彩色消息"""
    print(f"{color}{message}{Colors.RESET}")


def load_progress() -> Optional[Dict[str, Any]]:
    """加载保存的进度"""
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            print_color(f"找到保存的进度: 已完成 {progress['completedBatches']} 批次", Colors.CYAN)
            return progress
        except Exception as e:
            print_color(f"无法加载进度文件: {e}，将从头开始", Colors.YELLOW)
    return None


def save_progress(progress: Dict[str, Any]):
    """保存进度"""
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def get_total_services() -> int:
    """获取总服务数"""
    print_color("\n正在检测SAP OData服务总数...", Colors.CYAN)
    try:
        test_body = {
            "include_database": False,
            "include_odata": True,
            "build_semantic_index": False,
            "sync_to_metadata_service": False,
            "limit": 1,
            "offset": 0
        }
        
        response = requests.post(
            API_URL,
            json=test_body,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        total_services = result.get('metadata', {}).get('total_services')
        if total_services and total_services > 0:
            print_color(f"检测到总服务数: {total_services}", Colors.GREEN)
            return total_services
    except Exception as e:
        print_color(f"无法自动检测服务数: {e}，使用默认值348", Colors.YELLOW)
    
    return 348


def process_batch(batch: int, offset: int, limit: int, total_batches: int) -> Optional[Dict[str, Any]]:
    """处理单个批次"""
    batch_num = batch + 1
    print_color(f"[{batch_num}/{total_batches}] 处理批次 {batch} (offset={offset}, limit={limit})...", Colors.YELLOW)
    
    body = {
        "include_database": False,
        "include_odata": True,
        "build_semantic_index": False,
        "sync_to_metadata_service": True,
        "limit": limit,
        "offset": offset
    }
    
    retry_count = 0
    success = False
    result = None
    
    while retry_count < MAX_RETRIES and not success:
        try:
            request_start = time.time()
            response = requests.post(
                API_URL,
                json=body,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            request_duration = time.time() - request_start
            assets_count = len(data.get('data_assets', []))
            entities_count = len(data.get('business_entities', []))
            processes_count = len(data.get('business_processes', []))
            
            # 检查同步结果
            sync_result = data.get('metadata', {}).get('sync_result', {})
            assets_result = sync_result.get('data_assets', {})
            entities_result = sync_result.get('business_entities', {})
            
            assets_created = assets_result.get('created', 0)
            assets_failed = assets_result.get('failed', 0)
            entities_created = entities_result.get('created', 0)
            entities_failed = entities_result.get('failed', 0)
            
            print_color(f"  ✅ 成功完成 (耗时: {request_duration:.1f}秒)", Colors.GREEN)
            print_color(f"     发现数据资产: {assets_count}", Colors.WHITE)
            print_color(f"     发现业务实体: {entities_count}", Colors.WHITE)
            print_color(f"     发现业务流程: {processes_count}", Colors.WHITE)
            print_color(
                f"     同步数据资产: {assets_created}/{assets_result.get('total', 0)} (失败: {assets_failed})",
                Colors.GREEN if assets_failed == 0 else Colors.YELLOW
            )
            print_color(
                f"     同步业务实体: {entities_created}/{entities_result.get('total', 0)} (失败: {entities_failed})",
                Colors.GREEN if entities_failed == 0 else Colors.YELLOW
            )
            
            success = True
            result = {
                'assetsCount': assets_count,
                'entitiesCount': entities_count,
                'processesCount': processes_count,
                'assetsCreated': assets_created,
                'assetsFailed': assets_failed,
                'entitiesCreated': entities_created,
                'entitiesFailed': entities_failed,
                'hasMore': data.get('metadata', {}).get('has_more', False)
            }
            
        except Exception as e:
            retry_count += 1
            error_msg = str(e)
            
            if retry_count < MAX_RETRIES:
                print_color(f"  ⚠️  失败 (尝试 {retry_count}/{MAX_RETRIES}): {error_msg}", Colors.YELLOW)
                print_color(f"     等待 {RETRY_DELAY} 秒后重试...", Colors.YELLOW)
                time.sleep(RETRY_DELAY)
            else:
                print_color(f"  ❌ 最终失败: {error_msg}", Colors.RED)
                print_color("     跳过此批次，继续下一批次...", Colors.YELLOW)
    
    return result


def build_semantic_index() -> bool:
    """构建语义索引"""
    print_color("\n开始构建语义索引...", Colors.CYAN)
    try:
        body = {
            "include_database": False,
            "include_odata": False,
            "build_semantic_index": True,
            "sync_to_metadata_service": False
        }
        
        response = requests.post(
            API_URL,
            json=body,
            timeout=1800
        )
        response.raise_for_status()
        data = response.json()
        
        index_result = data.get('metadata', {}).get('semantic_index', {})
        indexed = index_result.get('indexed', 0)
        failed = index_result.get('failed', 0)
        
        print_color("  ✅ 语义索引构建完成", Colors.GREEN)
        print_color(f"     已索引文档: {indexed}", Colors.WHITE)
        print_color(
            f"     失败: {failed}",
            Colors.GREEN if failed == 0 else Colors.YELLOW
        )
        
        return True
    except Exception as e:
        print_color(f"  ⚠️  语义索引构建失败: {e}", Colors.YELLOW)
        return False


def verify_metadata_sync() -> Optional[Dict[str, int]]:
    """验证元数据同步"""
    print_color("\n验证元数据同步状态...", Colors.CYAN)
    try:
        metadata_service_url = "http://localhost:8005"
        
        # 检查数据资产
        assets_response = requests.get(
            f"{metadata_service_url}/api/data-assets?limit=1",
            timeout=30
        )
        assets_response.raise_for_status()
        assets_data = assets_response.json()
        total_assets = assets_data.get('total', 0)
        
        print_color(f"  ✅ 元数据服务中的数据资产: {total_assets}", Colors.GREEN)
        
        # 检查业务实体
        entities_response = requests.get(
            f"{metadata_service_url}/api/business-entities?limit=1",
            timeout=30
        )
        entities_response.raise_for_status()
        entities_data = entities_response.json()
        total_entities = entities_data.get('total', 0)
        
        print_color(f"  ✅ 元数据服务中的业务实体: {total_entities}", Colors.GREEN)
        
        return {
            'assets': total_assets,
            'entities': total_entities
        }
    except Exception as e:
        print_color(f"  ⚠️  无法验证元数据同步状态: {e}", Colors.YELLOW)
        return None


def main():
    """主程序"""
    print_color("\n========================================", Colors.CYAN)
    print_color("SAP元数据完整构建", Colors.CYAN)
    print_color("========================================", Colors.CYAN)
    
    # 加载进度
    progress = load_progress()
    start_offset = 0
    completed_batches = 0
    total_assets = 0
    total_entities = 0
    total_processes = 0
    failed_batches = 0
    
    if progress:
        start_offset = progress['lastOffset'] + progress['batchSize']
        completed_batches = progress['completedBatches']
        total_assets = progress['totalAssets']
        total_entities = progress['totalEntities']
        total_processes = progress['totalProcesses']
        failed_batches = progress['failedBatches']
        print_color(f"从批次 {start_offset // BATCH_SIZE} 继续构建...", Colors.CYAN)
    
    # 获取总服务数
    total_services = get_total_services()
    total_batches = (total_services + BATCH_SIZE - 1) // BATCH_SIZE
    
    print_color(f"总服务数: {total_services}", Colors.WHITE)
    print_color(f"批次大小: {BATCH_SIZE}", Colors.WHITE)
    print_color(f"总批次数: {total_batches}", Colors.WHITE)
    print_color(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.WHITE)
    print_color("========================================\n", Colors.CYAN)
    
    start_time = time.time()
    
    # 处理所有批次
    start_batch = start_offset // BATCH_SIZE
    for batch in range(start_batch, total_batches):
        offset = batch * BATCH_SIZE
        limit = min(BATCH_SIZE, total_services - offset)
        
        result = process_batch(batch, offset, limit, total_batches)
        
        if result:
            total_assets += result['assetsCount']
            total_entities += result['entitiesCount']
            total_processes += result['processesCount']
            completed_batches += 1
            
            # 保存进度
            progress = {
                'lastOffset': offset,
                'batchSize': BATCH_SIZE,
                'completedBatches': completed_batches,
                'totalAssets': total_assets,
                'totalEntities': total_entities,
                'totalProcesses': total_processes,
                'failedBatches': failed_batches,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            save_progress(progress)
            
            # 检查是否还有更多批次
            if not result['hasMore'] and (offset + limit) >= total_services:
                print_color("\n  ℹ️  所有服务已处理完成！", Colors.CYAN)
                break
        else:
            failed_batches += 1
        
        # 批次间短暂休息
        if batch < total_batches - 1:
            time.sleep(2)
        
        # 每10个批次显示一次进度
        if (batch + 1) % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / (batch + 1)
            remaining_batches = total_batches - (batch + 1)
            estimated_remaining = avg_time * remaining_batches
            
            print_color("\n--- 进度报告 ---", Colors.CYAN)
            print_color(f"已完成: {batch + 1}/{total_batches} 批次", Colors.WHITE)
            print_color(f"成功: {completed_batches}, 失败: {failed_batches}", Colors.WHITE)
            print_color(f"累计数据资产: {total_assets}", Colors.WHITE)
            print_color(f"累计业务实体: {total_entities}", Colors.WHITE)
            print_color(f"累计业务流程: {total_processes}", Colors.WHITE)
            print_color(f"已用时间: {elapsed / 60:.1f} 分钟", Colors.WHITE)
            print_color(f"预计剩余: {estimated_remaining / 60:.1f} 分钟", Colors.WHITE)
            print_color("----------------\n", Colors.CYAN)
    
    total_duration = time.time() - start_time
    
    print_color("\n========================================", Colors.CYAN)
    print_color("批次构建完成", Colors.CYAN)
    print_color("========================================", Colors.CYAN)
    print_color(f"总批次数: {total_batches}", Colors.WHITE)
    print_color(f"成功批次: {completed_batches}", Colors.GREEN)
    print_color(
        f"失败批次: {failed_batches}",
        Colors.GREEN if failed_batches == 0 else Colors.RED
    )
    print_color(f"累计数据资产: {total_assets}", Colors.WHITE)
    print_color(f"累计业务实体: {total_entities}", Colors.WHITE)
    print_color(f"累计业务流程: {total_processes}", Colors.WHITE)
    print_color(f"总耗时: {total_duration / 60:.1f} 分钟", Colors.WHITE)
    print_color("========================================\n", Colors.CYAN)
    
    # 构建语义索引
    if completed_batches > 0:
        index_success = build_semantic_index()
    else:
        print_color("\n⚠️  没有成功构建的批次，跳过语义索引构建", Colors.YELLOW)
        index_success = False
    
    # 验证元数据同步
    sync_status = verify_metadata_sync()
    
    # 最终报告
    print_color("\n========================================", Colors.CYAN)
    print_color("构建完成报告", Colors.CYAN)
    print_color("========================================", Colors.CYAN)
    print_color(f"数据资产发现: {total_assets}", Colors.WHITE)
    print_color(f"业务实体提取: {total_entities}", Colors.WHITE)
    print_color(f"业务流程分析: {total_processes}", Colors.WHITE)
    print_color(
        f"语义索引构建: {'✅ 完成' if index_success else '❌ 失败'}",
        Colors.GREEN if index_success else Colors.RED
    )
    
    if sync_status:
        print_color("元数据服务同步:", Colors.WHITE)
        print_color(f"  - 数据资产: {sync_status['assets']}", Colors.WHITE)
        print_color(f"  - 业务实体: {sync_status['entities']}", Colors.WHITE)
    
    print_color(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.WHITE)
    print_color("========================================\n", Colors.CYAN)
    
    # 清理进度文件
    if STATUS_FILE.exists():
        STATUS_FILE.unlink()
        print_color("已清理进度文件", Colors.CYAN)
    
    if failed_batches > 0:
        print_color(f"⚠️  有 {failed_batches} 个批次失败，请检查日志", Colors.YELLOW)
        sys.exit(1)
    else:
        print_color("✅ 所有元数据构建成功！", Colors.GREEN)
        sys.exit(0)


if __name__ == "__main__":
    main()

