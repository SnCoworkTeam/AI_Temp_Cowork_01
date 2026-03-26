"""
分类体系迁移API
提供数据迁移的API接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..utils.classification_migration import ClassificationMigrationTool
from ..core.database import get_db
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


class MigrationRequest(BaseModel):
    """迁移请求"""
    dry_run: bool = True
    batch_size: int = 100


@router.post(
    "/classification/migrate",
    summary="执行分类体系迁移",
    tags=["Classification"]
)
async def migrate_classifications(
    request: MigrationRequest = Body(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    执行分类体系迁移
    
    将现有分类数据迁移到新的三层分类体系：
    1. 主分类（primary classification）
    2. 维度分类（dimension classification）
    3. 标准化标签（standardized tags）
    
    Args:
        request: 迁移请求参数
            - dry_run: 是否为试运行（默认True，不实际更新数据库）
            - batch_size: 每批处理的记录数
    
    Returns:
        迁移统计信息
    """
    try:
        migration_tool = ClassificationMigrationTool(db)
        stats = migration_tool.migrate_all(
            batch_size=request.batch_size,
            dry_run=request.dry_run
        )
        
        return {
            "status": "success",
            "dry_run": request.dry_run,
            "stats": stats,
            "message": "迁移完成" if not request.dry_run else "试运行完成，未实际更新数据库"
        }
    except Exception as e:
        logger.error(f"分类迁移失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"迁移失败: {str(e)}")


@router.get(
    "/classification/migration/preview",
    summary="预览分类迁移结果",
    tags=["Classification"]
)
async def preview_migration(
    limit: int = Query(10, ge=1, le=100, description="预览记录数"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    预览分类迁移结果（不实际执行迁移）
    
    返回示例迁移结果，用于验证迁移逻辑
    """
    try:
        migration_tool = ClassificationMigrationTool(db)
        
        # 获取示例数据
        from ..models.data_asset import DataAsset
        from ..models.ai_model import AIModel
        from ..models.workflow_metadata import WorkflowMetadata
        from ..models.business_entity import BusinessEntity
        
        preview = {
            "data_assets": [],
            "ai_models": [],
            "workflows": [],
            "business_entities": []
        }
        
        # 预览数据资产
        data_assets = db.query(DataAsset).limit(limit).all()
        for asset in data_assets:
            migration_data = migration_tool.migrate_data_asset(asset)
            preview["data_assets"].append({
                "id": asset.id,
                "name": asset.name,
                "current": {
                    "classification": asset.classification,
                    "tags": asset.tags,
                    "source_system": asset.source_system
                },
                "migrated": migration_data
            })
        
        # 预览AI模型
        ai_models = db.query(AIModel).limit(limit).all()
        for model in ai_models:
            migration_data = migration_tool.migrate_ai_model(model)
            preview["ai_models"].append({
                "id": model.id,
                "name": model.name,
                "current": {
                    "model_type": model.model_type.value,
                    "status": model.status.value,
                    "tags": model.tags
                },
                "migrated": migration_data
            })
        
        # 预览工作流
        workflows = db.query(WorkflowMetadata).limit(limit).all()
        for workflow in workflows:
            migration_data = migration_tool.migrate_workflow(workflow)
            preview["workflows"].append({
                "id": workflow.id,
                "name": workflow.name,
                "current": {
                    "category": workflow.category,
                    "workflow_type": workflow.workflow_type,
                    "tags": workflow.tags
                },
                "migrated": migration_data
            })
        
        # 预览业务实体
        business_entities = db.query(BusinessEntity).limit(limit).all()
        for entity in business_entities:
            migration_data = migration_tool.migrate_business_entity(entity)
            preview["business_entities"].append({
                "id": entity.id,
                "name": entity.name,
                "current": {
                    "entity_type": entity.entity_type.value,
                    "classification": entity.classification,
                    "tags": entity.tags
                },
                "migrated": migration_data
            })
        
        return {
            "status": "success",
            "preview": preview,
            "message": f"预览了 {limit} 条记录"
        }
    except Exception as e:
        logger.error(f"预览迁移结果失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")








