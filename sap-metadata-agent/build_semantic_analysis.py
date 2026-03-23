"""
SAP元数据语义分析构建脚本
从元数据服务获取已构建的SAP元数据，构建语义索引到知识库
支持分批处理、断点续传、进度跟踪
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import time
import json

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.core.sap_semantic_index_builder import SAPSemanticIndexBuilder
from src.services.metadata_client import MetadataClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置参数
DEFAULT_BATCH_SIZE = int(os.getenv("SEMANTIC_BATCH_SIZE", "50"))  # 每批处理的元数据数量
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试延迟（秒）
BATCH_DELAY = 1  # 批次间延迟（秒）
PROGRESS_FILE = "semantic_build_progress.json"  # 进度文件


def load_progress() -> Dict[str, Any]:
    """加载构建进度"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载进度文件失败: {e}")
    return {
        "assets_offset": 0,
        "entities_offset": 0,
        "total_indexed": 0,
        "total_failed": 0,
        "last_update": None
    }


def save_progress(progress: Dict[str, Any]):
    """保存构建进度"""
    progress["last_update"] = datetime.now().isoformat()
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"保存进度文件失败: {e}")


async def get_total_count(metadata_client: MetadataClient, item_type: str = "assets") -> int:
    """
    获取元数据总数（通过分页估算）
    
    Args:
        metadata_client: 元数据客户端
        item_type: 类型（assets或entities）
    
    Returns:
        估算的总数
    """
    try:
        if item_type == "assets":
            # 获取一批数据来估算总数
            assets = await metadata_client.list_data_assets(
                limit=1000,
                offset=0,
                source_system="SAP"
            )
            # 如果返回了1000个，说明可能还有更多
            if len(assets) == 1000:
                # 尝试获取更多来估算
                more_assets = await metadata_client.list_data_assets(
                    limit=1000,
                    offset=1000,
                    source_system="SAP"
                )
                if len(more_assets) == 1000:
                    # 可能有很多，返回一个较大的估算值
                    return 100000  # 保守估算
            return len(assets)
        else:
            entities = await metadata_client.list_business_entities(
                limit=1000,
                offset=0,
                tags=["SAP"]
            )
            if len(entities) == 1000:
                return 10000  # 实体通常比资产少
            return len(entities)
    except Exception as e:
        logger.warning(f"获取总数失败: {e}")
        return 0


async def process_batch(
    semantic_builder: SAPSemanticIndexBuilder,
    assets_batch: List[Dict[str, Any]],
    entities_batch: List[Dict[str, Any]],
    processes_batch: List[Dict[str, Any]],
    batch_num: int,
    total_batches: Optional[int] = None
) -> Dict[str, int]:
    """
    处理一批元数据的语义分析
    
    Args:
        semantic_builder: 语义索引构建器
        assets_batch: 数据资产批次
        entities_batch: 业务实体批次
        processes_batch: 业务流程批次
        batch_num: 批次编号
        total_batches: 总批次数（可选）
        
    Returns:
        处理结果统计
    """
    batch_info = f"[{batch_num + 1}"
    if total_batches:
        batch_info += f"/{total_batches}"
    batch_info += "]"
    
    total_items = len(assets_batch) + len(entities_batch) + len(processes_batch)
    logger.info(f"{batch_info} 处理批次: {len(assets_batch)} 个资产, {len(entities_batch)} 个实体, {len(processes_batch)} 个流程")
    
    for attempt in range(MAX_RETRIES):
        try:
            start_time = time.time()
            result = await semantic_builder.build_semantic_index(
                assets=assets_batch,
                entities=entities_batch,
                processes=processes_batch
            )
            duration = time.time() - start_time
            
            indexed = result.get("indexed", 0)
            failed = result.get("failed", 0)
            
            print(f"  {batch_info} ✅ 完成 (耗时: {duration:.1f}秒) - 索引: {indexed}, 失败: {failed}")
            
            return {
                "indexed": indexed,
                "failed": failed,
                "total": indexed + failed,
                "duration": duration
            }
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"{batch_info} 处理失败，重试 {attempt + 1}/{MAX_RETRIES}: {e}")
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
            else:
                logger.error(f"{batch_info} 处理失败: {e}", exc_info=True)
                print(f"  {batch_info} ❌ 失败: {e}")
                return {
                    "indexed": 0,
                    "failed": total_items,
                    "total": total_items,
                    "duration": 0
                }
    
    return {"indexed": 0, "failed": 0, "total": 0, "duration": 0}


def convert_asset_to_sap_format(asset: Dict[str, Any]) -> Dict[str, Any]:
    """将元数据服务的资产格式转换为SAP格式"""
    metadata = asset.get("metadata") or {}
    schema_info = asset.get("schema_info") or {}
    
    return {
        "name": asset.get("name", ""),
        "display_name": asset.get("display_name", ""),
        "description": asset.get("description", ""),
        "asset_type": asset.get("asset_type", "table"),
        "sap_table_name": metadata.get("sap_table_name"),
        "sap_module": metadata.get("sap_module"),
        "odata_service": metadata.get("odata_service"),
        "odata_entity": metadata.get("odata_entity"),
        "schema_info": schema_info,
        "classification": asset.get("classification", ""),
        "tags": asset.get("tags", []),
        "business_terms": metadata.get("business_terms", []),
        "semantic_relationships": metadata.get("semantic_relationships", []),
        "metadata": metadata
    }


def convert_entity_to_sap_format(entity: Dict[str, Any]) -> Dict[str, Any]:
    """将元数据服务的实体格式转换为SAP格式"""
    metadata = entity.get("metadata") or {}
    
    return {
        "name": entity.get("name", ""),
        "display_name": entity.get("display_name", ""),
        "description": entity.get("description", ""),
        "entity_type": metadata.get("entity_type", ""),
        "business_domain": metadata.get("business_domain", ""),
        "key_fields": metadata.get("key_fields", []),
        "business_terms": metadata.get("business_terms", []),
        "semantic_relationships": metadata.get("semantic_relationships", []),
        "tags": entity.get("tags", []),
        "metadata": metadata
    }


async def build_semantic_analysis(
    start_assets_offset: int = 0,
    start_entities_offset: int = 0,
    batch_size: Optional[int] = None,
    resume: bool = True
):
    """
    构建语义分析索引
    
    Args:
        start_assets_offset: 数据资产起始偏移量
        start_entities_offset: 业务实体起始偏移量
        batch_size: 批次大小
        resume: 是否从进度文件恢复
    """
    batch_size = batch_size or DEFAULT_BATCH_SIZE
    
    # 加载进度
    progress = load_progress() if resume else {
        "assets_offset": start_assets_offset,
        "entities_offset": start_entities_offset,
        "total_indexed": 0,
        "total_failed": 0,
        "last_update": None
    }
    
    print("=" * 80)
    print("SAP元数据语义分析构建")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"批次大小: {batch_size}")
    print(f"数据资产起始偏移: {progress['assets_offset']}")
    print(f"业务实体起始偏移: {progress['entities_offset']}")
    if progress.get('last_update'):
        print(f"上次更新: {progress['last_update']}")
    print()
    
    # 初始化客户端
    metadata_service_url = os.getenv("METADATA_SERVICE_URL", "http://localhost:8005")
    knowledge_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://localhost:8004")
    
    metadata_client = MetadataClient(metadata_service_url=metadata_service_url)
    semantic_builder = SAPSemanticIndexBuilder(knowledge_base_url)
    
    try:
        # 统计信息
        total_indexed = progress.get("total_indexed", 0)
        total_failed = progress.get("total_failed", 0)
        total_processed = 0
        start_time = time.time()
        
        # 步骤1: 分批处理数据资产
        print("步骤1: 处理数据资产")
        print("-" * 80)
        
        assets_offset = progress["assets_offset"]
        assets_batch_num = 0
        
        # 估算总数
        estimated_total_assets = await get_total_count(metadata_client, "assets")
        if estimated_total_assets > 0:
            estimated_batches = (estimated_total_assets - assets_offset + batch_size - 1) // batch_size
            print(f"估算总资产数: {estimated_total_assets:,}")
            print(f"估算剩余批次数: {estimated_batches}\n")
        
        while True:
            # 获取一批数据资产
            assets = await metadata_client.list_data_assets(
                limit=batch_size,
                offset=assets_offset,
                source_system="SAP"
            )
            
            if not assets:
                print(f"  所有数据资产已处理完成\n")
                break
            
            # 转换为SAP格式
            sap_assets = [convert_asset_to_sap_format(asset) for asset in assets]
            
            # 处理这一批
            result = await process_batch(
                semantic_builder,
                sap_assets,
                [],
                [],
                assets_batch_num,
                None  # 总批次数未知
            )
            
            total_indexed += result["indexed"]
            total_failed += result["failed"]
            total_processed += result["total"]
            assets_offset += len(assets)
            assets_batch_num += 1
            
            # 更新进度
            progress["assets_offset"] = assets_offset
            progress["total_indexed"] = total_indexed
            progress["total_failed"] = total_failed
            save_progress(progress)
            
            # 显示进度
            if assets_batch_num % 10 == 0:
                elapsed = time.time() - start_time
                print(f"\n  进度: 已处理 {assets_offset:,} 个资产")
                print(f"  已索引: {total_indexed:,} | 失败: {total_failed:,}")
                print(f"  耗时: {elapsed / 60:.1f} 分钟\n")
            
            # 批次间延迟
            if len(assets) == batch_size:
                await asyncio.sleep(BATCH_DELAY)
            else:
                break  # 最后一批
        
        # 步骤2: 分批处理业务实体
        print("步骤2: 处理业务实体")
        print("-" * 80)
        
        entities_offset = progress["entities_offset"]
        entities_batch_num = 0
        
        # 估算总数
        estimated_total_entities = await get_total_count(metadata_client, "entities")
        if estimated_total_entities > 0:
            estimated_batches = (estimated_total_entities - entities_offset + batch_size - 1) // batch_size
            print(f"估算总实体数: {estimated_total_entities:,}")
            print(f"估算剩余批次数: {estimated_batches}\n")
        
        while True:
            # 获取一批业务实体
            entities = await metadata_client.list_business_entities(
                limit=batch_size,
                offset=entities_offset,
                tags=["SAP"]
            )
            
            if not entities:
                print(f"  所有业务实体已处理完成\n")
                break
            
            # 转换为SAP格式
            sap_entities = [convert_entity_to_sap_format(entity) for entity in entities]
            
            # 处理这一批
            result = await process_batch(
                semantic_builder,
                [],
                sap_entities,
                [],
                entities_batch_num,
                None
            )
            
            total_indexed += result["indexed"]
            total_failed += result["failed"]
            total_processed += result["total"]
            entities_offset += len(entities)
            entities_batch_num += 1
            
            # 更新进度
            progress["entities_offset"] = entities_offset
            progress["total_indexed"] = total_indexed
            progress["total_failed"] = total_failed
            save_progress(progress)
            
            # 显示进度
            if entities_batch_num % 10 == 0:
                elapsed = time.time() - start_time
                print(f"\n  进度: 已处理 {entities_offset:,} 个实体")
                print(f"  已索引: {total_indexed:,} | 失败: {total_failed:,}")
                print(f"  耗时: {elapsed / 60:.1f} 分钟\n")
            
            # 批次间延迟
            if len(entities) == batch_size:
                await asyncio.sleep(BATCH_DELAY)
            else:
                break  # 最后一批
        
        # 最终报告
        total_duration = time.time() - start_time
        print("=" * 80)
        print("语义分析构建完成")
        print("=" * 80)
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {total_duration / 60:.1f} 分钟 ({total_duration / 3600:.2f} 小时)")
        print(f"\n结果统计:")
        print(f"  成功索引: {total_indexed:,}")
        print(f"  失败: {total_failed:,}")
        print(f"  总计: {total_processed:,}")
        
        if total_indexed > 0:
            success_rate = (total_indexed / total_processed * 100) if total_processed > 0 else 0
            print(f"  成功率: {success_rate:.1f}%")
            print(f"\n✅ 语义分析构建成功完成！")
            
            # 清理进度文件
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
                print(f"  进度文件已清理")
            
            return True
        else:
            print(f"\n⚠️  没有文档被成功索引")
            if total_failed > 0:
                print(f"   请检查知识库服务是否正常运行: {knowledge_base_url}")
            return False
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  构建已中断")
        print(f"   进度已保存到: {PROGRESS_FILE}")
        print(f"   可以使用 --resume 参数继续构建")
        save_progress(progress)
        return False
    except Exception as e:
        logger.error(f"语义分析构建失败: {e}", exc_info=True)
        print(f"\n❌ 语义分析构建失败: {e}")
        save_progress(progress)
        return False
    
    finally:
        # 清理资源
        await semantic_builder.close()
        await metadata_client.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="构建SAP元数据语义分析索引",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从头开始构建
  python build_semantic_analysis.py
  
  # 指定批次大小
  python build_semantic_analysis.py --batch-size 100
  
  # 从指定偏移量开始
  python build_semantic_analysis.py --assets-offset 1000 --entities-offset 0
  
  # 从进度文件恢复
  python build_semantic_analysis.py --resume
        """
    )
    parser.add_argument(
        "--assets-offset",
        type=int,
        default=0,
        help="数据资产起始偏移量"
    )
    parser.add_argument(
        "--entities-offset",
        type=int,
        default=0,
        help="业务实体起始偏移量"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help=f"批次大小（默认: {DEFAULT_BATCH_SIZE}）"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="从进度文件恢复构建"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="不从进度文件恢复（从头开始）"
    )
    
    args = parser.parse_args()
    
    resume = args.resume and not args.no_resume
    
    try:
        success = asyncio.run(
            build_semantic_analysis(
                start_assets_offset=args.assets_offset,
                start_entities_offset=args.entities_offset,
                batch_size=args.batch_size,
                resume=resume
            )
        )
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

