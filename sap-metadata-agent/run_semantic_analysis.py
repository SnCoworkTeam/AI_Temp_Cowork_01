"""
运行完整的语义分析脚本（分批处理）
为所有SAP元数据生成语义索引，支持分批处理以避免内存和超时问题
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import time

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.core.sap_metadata_orchestrator import SAPMetadataOrchestrator
from src.core.sap_semantic_index_builder import SAPSemanticIndexBuilder
from src.services.metadata_client import MetadataClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置参数
BATCH_SIZE = int(os.getenv("SEMANTIC_BATCH_SIZE", "50"))  # 每批处理的元数据数量
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试延迟（秒）
BATCH_DELAY = 1  # 批次间延迟（秒）


async def get_total_counts(metadata_client: MetadataClient) -> Dict[str, int]:
    """
    获取元数据总数
    
    Returns:
        包含总数的字典
    """
    try:
        # 获取数据资产总数（通过获取第一页来估算）
        assets = await metadata_client.list_data_assets(
            limit=1,
            offset=0,
            source_system="SAP"
        )
        # 注意：这里需要根据实际API返回的总数来调整
        # 如果API不返回总数，我们需要通过分页来统计
        
        # 获取业务实体总数
        entities = await metadata_client.list_business_entities(
            limit=1,
            offset=0,
            tags=["SAP"]
        )
        
        return {
            "assets_estimated": len(assets) > 0,  # 是否有数据
            "entities_estimated": len(entities) > 0
        }
    except Exception as e:
        logger.warning(f"获取总数失败: {e}")
        return {"assets_estimated": True, "entities_estimated": True}


async def process_batch(
    semantic_builder: SAPSemanticIndexBuilder,
    assets_batch: List[Dict[str, Any]],
    entities_batch: List[Dict[str, Any]],
    batch_num: int,
    total_batches: int
) -> Dict[str, int]:
    """
    处理一批元数据的语义分析
    
    Args:
        semantic_builder: 语义索引构建器
        assets_batch: 数据资产批次
        entities_batch: 业务实体批次
        batch_num: 批次编号
        total_batches: 总批次数
        
    Returns:
        处理结果统计
    """
    logger.info(f"处理批次 {batch_num + 1}/{total_batches}: {len(assets_batch)} 个资产, {len(entities_batch)} 个实体")
    
    for attempt in range(MAX_RETRIES):
        try:
            result = await semantic_builder.build_semantic_index(
                assets=assets_batch,
                entities=entities_batch,
                processes=[]
            )
            
            indexed = result.get("indexed", 0)
            failed = result.get("failed", 0)
            
            print(f"  [{batch_num + 1}/{total_batches}] ✅ 完成: 索引 {indexed}, 失败 {failed}")
            
            return {
                "indexed": indexed,
                "failed": failed,
                "total": indexed + failed
            }
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"批次 {batch_num + 1} 处理失败，重试 {attempt + 1}/{MAX_RETRIES}: {e}")
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
            else:
                logger.error(f"批次 {batch_num + 1} 处理失败: {e}", exc_info=True)
                print(f"  [{batch_num + 1}/{total_batches}] ❌ 失败: {e}")
                return {"indexed": 0, "failed": len(assets_batch) + len(entities_batch), "total": len(assets_batch) + len(entities_batch)}
    
    return {"indexed": 0, "failed": 0, "total": 0}


async def run_semantic_analysis(
    start_offset: int = 0,
    batch_size: Optional[int] = None
):
    """
    运行完整的语义分析（分批处理）
    
    Args:
        start_offset: 起始偏移量（用于断点续传）
        batch_size: 批次大小（默认使用BATCH_SIZE）
    """
    batch_size = batch_size or BATCH_SIZE
    
    print("=" * 80)
    print("SAP元数据语义分析（分批处理）")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"批次大小: {batch_size}")
    print(f"起始偏移: {start_offset}\n")
    
    # 初始化客户端
    metadata_client = MetadataClient(
        base_url=os.getenv("METADATA_SERVICE_URL", "http://localhost:8005")
    )
    
    knowledge_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://localhost:8004")
    
    # 创建语义索引构建器
    semantic_builder = SAPSemanticIndexBuilder(knowledge_base_url)
    
    try:
        # 统计信息
        total_indexed = 0
        total_failed = 0
        total_processed = 0
        
        # 步骤1: 分批处理数据资产
        logger.info("步骤1: 分批处理数据资产...")
        print("\n处理数据资产:")
        print("-" * 80)
        
        assets_offset = start_offset
        assets_batch_num = 0
        
        while True:
            # 获取一批数据资产
            assets = await metadata_client.list_data_assets(
                limit=batch_size,
                offset=assets_offset,
                source_system="SAP"
            )
            
            if not assets:
                break
            
            # 转换为SAP格式
            sap_assets = []
            for asset in assets:
                sap_asset = {
                    "name": asset.get("name", ""),
                    "display_name": asset.get("display_name", ""),
                    "description": asset.get("description", ""),
                    "asset_type": asset.get("asset_type", "table"),
                    "sap_table_name": asset.get("metadata", {}).get("sap_table_name"),
                    "sap_module": asset.get("metadata", {}).get("sap_module"),
                    "odata_service": asset.get("metadata", {}).get("odata_service"),
                    "odata_entity": asset.get("metadata", {}).get("odata_entity"),
                    "schema_info": asset.get("schema_info", {}),
                    "classification": asset.get("classification", ""),
                    "tags": asset.get("tags", []),
                    "business_terms": asset.get("metadata", {}).get("business_terms", []),
                    "semantic_relationships": asset.get("metadata", {}).get("semantic_relationships", []),
                    "metadata": asset.get("metadata", {})
                }
                sap_assets.append(sap_asset)
            
            # 处理这一批
            result = await process_batch(
                semantic_builder,
                sap_assets,
                [],  # 这一批只处理资产
                assets_batch_num,
                999  # 总批次数未知，使用大数
            )
            
            total_indexed += result["indexed"]
            total_failed += result["failed"]
            total_processed += result["total"]
            assets_offset += len(assets)
            assets_batch_num += 1
            
            # 批次间延迟
            if len(assets) == batch_size:
                await asyncio.sleep(BATCH_DELAY)
            else:
                break  # 最后一批
        
        # 步骤2: 分批处理业务实体
        logger.info("步骤2: 分批处理业务实体...")
        print("\n处理业务实体:")
        print("-" * 80)
        
        entities_offset = 0
        entities_batch_num = 0
        
        while True:
            # 获取一批业务实体
            entities = await metadata_client.list_business_entities(
                limit=batch_size,
                offset=entities_offset,
                tags=["SAP"]
            )
            
            if not entities:
                break
            
            # 转换为SAP格式
            sap_entities = []
            for entity in entities:
                sap_entity = {
                    "name": entity.get("name", ""),
                    "display_name": entity.get("display_name", ""),
                    "description": entity.get("description", ""),
                    "entity_type": entity.get("metadata", {}).get("entity_type", ""),
                    "business_domain": entity.get("metadata", {}).get("business_domain", ""),
                    "key_fields": entity.get("metadata", {}).get("key_fields", []),
                    "business_terms": entity.get("metadata", {}).get("business_terms", []),
                    "semantic_relationships": entity.get("metadata", {}).get("semantic_relationships", []),
                    "tags": entity.get("tags", []),
                    "metadata": entity.get("metadata", {})
                }
                sap_entities.append(sap_entity)
            
            # 处理这一批
            result = await process_batch(
                semantic_builder,
                [],  # 这一批只处理实体
                sap_entities,
                entities_batch_num,
                999  # 总批次数未知
            )
            
            total_indexed += result["indexed"]
            total_failed += result["failed"]
            total_processed += result["total"]
            entities_offset += len(entities)
            entities_batch_num += 1
            
            # 批次间延迟
            if len(entities) == batch_size:
                await asyncio.sleep(BATCH_DELAY)
            else:
                break  # 最后一批
        
        # 最终报告
        print(f"\n{'=' * 80}")
        print(f"语义分析完成")
        print(f"{'=' * 80}")
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n结果统计:")
        print(f"  成功索引: {total_indexed}")
        print(f"  失败: {total_failed}")
        print(f"  总计: {total_processed}")
        
        if total_indexed > 0:
            success_rate = (total_indexed / total_processed * 100) if total_processed > 0 else 0
            print(f"  成功率: {success_rate:.1f}%")
            print(f"\n✅ 语义分析成功完成！")
            return True
        else:
            print(f"\n⚠️  没有文档被成功索引")
            if total_failed > 0:
                print(f"   请检查知识库服务是否正常运行")
            return False
        
    except Exception as e:
        logger.error(f"语义分析失败: {e}", exc_info=True)
        print(f"\n❌ 语义分析失败: {e}")
        return False
    
    finally:
        # 清理资源
        await semantic_builder.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="运行SAP元数据语义分析（分批处理）")
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="起始偏移量（用于断点续传）"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help=f"批次大小（默认: {BATCH_SIZE}）"
    )
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(
            run_semantic_analysis(
                start_offset=args.offset,
                batch_size=args.batch_size
            )
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        print("   可以使用 --offset 参数从上次中断的位置继续")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)

