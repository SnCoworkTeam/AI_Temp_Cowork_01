"""
服务元数据向量化脚本
将服务元数据向量化并存储到knowledge-base，用于语义搜索
一次性执行脚本
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from metadata_service.src.core.database import init_database, get_db, close_database
from metadata_service.src.services.metadata_catalog import MetadataCatalogService
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_URL = os.getenv("KNOWLEDGE_BASE_URL", "http://localhost:8004")


async def vectorize_service_metadata():
    """向量化服务元数据"""
    try:
        # 初始化数据库
        if not init_database():
            logger.error("Failed to initialize database")
            return False
        
        db = next(get_db())
        catalog = MetadataCatalogService(db)
        
        # 获取所有服务元数据
        logger.info("Collecting service metadata...")
        
        # 1. AI模型
        ai_models = catalog.list_ai_models(limit=1000, skip=0)
        logger.info(f"Found {len(ai_models)} AI models")
        
        # 2. 数据资产（作为服务）
        data_assets = catalog.list_data_assets(limit=1000, skip=0)
        logger.info(f"Found {len(data_assets)} data assets")
        
        # 3. 工作流（作为服务）
        workflows = catalog.list_workflow_metadata(limit=1000, skip=0)
        logger.info(f"Found {len(workflows)} workflows")
        
        # 构建服务元数据文档
        service_documents = []
        
        for model in ai_models:
            model_dict = model.model_dump() if hasattr(model, 'model_dump') else dict(model)
            service_documents.append({
                "content": f"""
服务名称: {model_dict.get('display_name', model_dict.get('name', ''))}
服务类型: AI模型
描述: {model_dict.get('description', '')}
框架: {model_dict.get('framework', '')}
用途: {', '.join(model_dict.get('use_cases', []))}
标签: {', '.join(model_dict.get('tags', []))}
""".strip(),
                "metadata": {
                    "service_id": f"ai_model_{model_dict.get('id')}",
                    "service_name": model_dict.get('display_name', model_dict.get('name', '')),
                    "service_type": "ai_model",
                    "original_id": model_dict.get('id'),
                    **model_dict
                }
            })
        
        for asset in data_assets:
            asset_dict = asset.model_dump() if hasattr(asset, 'model_dump') else dict(asset)
            service_documents.append({
                "content": f"""
服务名称: {asset_dict.get('display_name', asset_dict.get('name', ''))}
服务类型: 数据资产
描述: {asset_dict.get('description', '')}
资产类型: {asset_dict.get('asset_type', '')}
来源系统: {asset_dict.get('source_system', '')}
标签: {', '.join(asset_dict.get('tags', []))}
""".strip(),
                "metadata": {
                    "service_id": f"data_asset_{asset_dict.get('id')}",
                    "service_name": asset_dict.get('display_name', asset_dict.get('name', '')),
                    "service_type": "data_asset",
                    "original_id": asset_dict.get('id'),
                    **asset_dict
                }
            })
        
        for workflow in workflows:
            workflow_dict = workflow.model_dump() if hasattr(workflow, 'model_dump') else dict(workflow)
            service_documents.append({
                "content": f"""
服务名称: {workflow_dict.get('display_name', workflow_dict.get('name', ''))}
服务类型: 工作流
描述: {workflow_dict.get('description', '')}
类别: {workflow_dict.get('category', '')}
状态: {workflow_dict.get('status', '')}
标签: {', '.join(workflow_dict.get('tags', []))}
""".strip(),
                "metadata": {
                    "service_id": f"workflow_{workflow_dict.get('id')}",
                    "service_name": workflow_dict.get('display_name', workflow_dict.get('name', '')),
                    "service_type": "workflow",
                    "original_id": workflow_dict.get('id'),
                    **workflow_dict
                }
            })
        
        logger.info(f"Prepared {len(service_documents)} service documents for vectorization")
        
        # 批量上传到knowledge-base
        async with httpx.AsyncClient(timeout=60.0) as client:
            batch_size = 10
            total_batches = (len(service_documents) + batch_size - 1) // batch_size
            
            for i in range(0, len(service_documents), batch_size):
                batch = service_documents[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                logger.info(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} documents)...")
                
                try:
                    # 调用knowledge-base的文档上传API
                    # 注意：这里需要根据knowledge-base的实际API调整
                    response = await client.post(
                        f"{KNOWLEDGE_BASE_URL}/api/documents/batch",
                        json={
                            "documents": batch,
                            "collection": "service_metadata",
                            "auto_vectorize": True  # 自动向量化
                        }
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Batch {batch_num} uploaded successfully")
                    else:
                        logger.warning(f"Batch {batch_num} upload failed: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.error(f"Error uploading batch {batch_num}: {e}")
        
        logger.info("Service metadata vectorization completed!")
        return True
        
    except Exception as e:
        logger.error(f"Error in vectorize_service_metadata: {e}", exc_info=True)
        return False
    finally:
        close_database()


if __name__ == "__main__":
    asyncio.run(vectorize_service_metadata())


