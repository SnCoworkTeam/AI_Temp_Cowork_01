"""
数据资产API路由
"""
import json
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.data_asset import (
    DataAssetSchema,
    DataAssetCreate,
    DataAssetUpdate,
    DataAssetDetail
)
from ..services.metadata_catalog import MetadataCatalogService
from ..services.usage_tracker import UsageTracker
from ..core.database import get_db
from luminaos_common.common.logger import setup_logger
from luminaos_common.common.error_handler import create_error_response

router = APIRouter()
logger = setup_logger(__name__)


def get_catalog_service(db: Session = Depends(get_db)) -> MetadataCatalogService:
    """获取元数据目录服务"""
    return MetadataCatalogService(db)


@router.post(
    "/data-assets",
    response_model=DataAssetSchema,
    summary="创建数据资产",
    tags=["Data Assets"]
)
async def create_data_asset(
    asset_data: DataAssetCreate,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """创建数据资产"""
    try:
        return service.create_data_asset(asset_data)
    except Exception as e:
        logger.error(f"Failed to create data asset: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/data-assets",
    response_model=List[DataAssetSchema],
    summary="列出数据资产",
    tags=["Data Assets"]
)
async def list_data_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=10000),  # 增加limit上限到10000
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    category: Optional[str] = None,
    domain: Optional[str] = None,
    classification: Optional[str] = Query(None, description="主分类（classification字段）"),
    business_domain: Optional[str] = Query(None, description="业务领域（classification_dimensions.business.domain）"),
    technical_source: Optional[str] = Query(None, description="技术来源（classification_dimensions.technical.source）"),
    lifecycle_stage: Optional[str] = Query(None, description="生命周期阶段（classification_dimensions.lifecycle.stage）"),
    standardized_tag: Optional[str] = Query(None, description="标准化标签（standardized_tags）"),
    quality_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    include_total: bool = Query(False, description="是否在响应头中包含总数"),
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """列出数据资产"""
    try:
        assets = service.list_data_assets(
            skip=skip,
            limit=limit,
            asset_type=asset_type,
            status=status,
            search=search,
            category=category,
            domain=domain,
            classification=classification,
            business_domain=business_domain,
            technical_source=technical_source,
            lifecycle_stage=lifecycle_stage,
            standardized_tag=standardized_tag,
            quality_score=quality_score
        )
        
        # 如果请求包含总数，在响应头中添加总数
        if include_total:
            total = service.count_data_assets(
                asset_type=asset_type,
                status=status,
                search=search,
                category=category,
                domain=domain,
                classification=classification,
                business_domain=business_domain,
                technical_source=technical_source,
                lifecycle_stage=lifecycle_stage,
                standardized_tag=standardized_tag,
                quality_score=quality_score
            )
            from fastapi import Response
            import json
            from fastapi.encoders import jsonable_encoder
            json_compatible_data = jsonable_encoder(assets)
            response = Response(
                content=json.dumps(json_compatible_data),
                media_type="application/json",
                headers={"X-Total-Count": str(total)}
            )
            return response
        
        return assets
    except Exception as e:
        logger.error(f"Failed to list data assets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/data-assets/{asset_id}",
    response_model=DataAssetSchema,
    summary="获取数据资产",
    tags=["Data Assets"]
)
async def get_data_asset(
    asset_id: int,
    service: MetadataCatalogService = Depends(get_catalog_service),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="用户ID（用于使用统计）")
):
    """获取数据资产"""
    asset = service.get_data_asset(asset_id)
    
    # 跟踪访问统计
    if asset:
        try:
            usage_tracker = UsageTracker(db)
            await usage_tracker.track_access(
                asset_type="data_asset",
                asset_id=asset_id,
                user_id=user_id,
                service_name="metadata-service"
            )
        except Exception as e:
            logger.debug(f"Failed to track usage: {e}")
    if not asset:
        raise HTTPException(status_code=404, detail="Data asset not found")
    return asset


@router.get(
    "/metadata/assets",
    response_model=List[DataAssetSchema],
    summary="列出数据资产（元数据API）",
    tags=["Metadata"]
)
async def list_metadata_assets(
    category: Optional[str] = Query(None, description="分类"),
    domain: Optional[str] = Query(None, description="业务域"),
    quality_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="质量分数阈值"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """列出数据资产（支持分类、业务域、质量分数过滤）"""
    try:
        return service.list_data_assets(
            skip=skip,
            limit=limit,
            category=category,
            domain=domain,
            quality_score=quality_score
        )
    except Exception as e:
        logger.error(f"Failed to list metadata assets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/metadata/assets/{asset_id}",
    response_model=DataAssetDetail,
    summary="获取资产详情（元数据API）",
    tags=["Metadata"]
)
async def get_asset_detail(
    asset_id: str,
    service: MetadataCatalogService = Depends(get_catalog_service),
    db: Session = Depends(get_db)
):
    """获取资产详情（包含血缘关系等扩展信息）"""
    try:
        # 尝试将asset_id转换为int
        try:
            asset_id_int = int(asset_id)
        except ValueError:
            # 如果不是数字，尝试通过name查找
            assets = service.list_data_assets(search=asset_id, limit=1)
            if not assets:
                raise HTTPException(status_code=404, detail="Data asset not found")
            asset_id_int = assets[0].id
        
        # 获取基础资产信息
        asset = service.get_data_asset(asset_id_int)
        if not asset:
            raise HTTPException(status_code=404, detail="Data asset not found")
        
        # 获取血缘关系
        from ..services.data_lineage import DataLineageService
        
        lineage_service = DataLineageService(db)
        
        # 获取上游和下游血缘（返回LineageGraph）
        upstream_graph = lineage_service.get_upstream_lineage(
            entity_type="data_asset",
            entity_id=str(asset_id_int),
            max_depth=3
        )
        downstream_graph = lineage_service.get_downstream_lineage(
            entity_type="data_asset",
            entity_id=str(asset_id_int),
            max_depth=3
        )
        
        # 构建详情对象
        asset_dict = asset.model_dump()
        
        # 从metadata中提取category和domain
        metadata = asset_dict.get("metadata", {}) or {}
        category = metadata.get("category")
        domain = metadata.get("domain")
        
        # 构建血缘关系（从LineageGraph中提取edges）
        upstream_lineage = None
        if upstream_graph and upstream_graph.edges:
            upstream_lineage = [
                {
                    "source_type": edge.source.split(":")[0] if ":" in edge.source else "unknown",
                    "source_id": edge.source.split(":")[1] if ":" in edge.source else edge.source,
                    "source_asset": edge.source,
                    "target_type": edge.target.split(":")[0] if ":" in edge.target else "unknown",
                    "target_id": edge.target.split(":")[1] if ":" in edge.target else edge.target,
                    "target_asset": edge.target,
                    "relation_type": edge.relation_type.value if hasattr(edge.relation_type, 'value') else str(edge.relation_type),
                    "lineage_type": edge.lineage_type.value if hasattr(edge.lineage_type, 'value') else str(edge.lineage_type),
                    "transformation": edge.transformation_logic
                }
                for edge in upstream_graph.edges
            ]
        
        downstream_lineage = None
        if downstream_graph and downstream_graph.edges:
            downstream_lineage = [
                {
                    "source_type": edge.source.split(":")[0] if ":" in edge.source else "unknown",
                    "source_id": edge.source.split(":")[1] if ":" in edge.source else edge.source,
                    "source_asset": edge.source,
                    "target_type": edge.target.split(":")[0] if ":" in edge.target else "unknown",
                    "target_id": edge.target.split(":")[1] if ":" in edge.target else edge.target,
                    "target_asset": edge.target,
                    "relation_type": edge.relation_type.value if hasattr(edge.relation_type, 'value') else str(edge.relation_type),
                    "lineage_type": edge.lineage_type.value if hasattr(edge.lineage_type, 'value') else str(edge.lineage_type),
                    "transformation": edge.transformation_logic
                }
                for edge in downstream_graph.edges
            ]
        
        return DataAssetDetail(
            **asset_dict,
            category=category,
            domain=domain,
            upstream_lineage=upstream_lineage,
            downstream_lineage=downstream_lineage
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get asset detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/data-assets/{asset_id}",
    response_model=DataAssetSchema,
    summary="更新数据资产",
    tags=["Data Assets"]
)
async def update_data_asset(
    asset_id: int,
    asset_data: DataAssetUpdate,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """更新数据资产"""
    asset = service.update_data_asset(asset_id, asset_data)
    if not asset:
        raise HTTPException(status_code=404, detail="Data asset not found")
    return asset


@router.delete(
    "/data-assets/{asset_id}",
    summary="删除数据资产",
    tags=["Data Assets"]
)
async def delete_data_asset(
    asset_id: int,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """删除数据资产"""
    success = service.delete_data_asset(asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Data asset not found")
    return {"message": "Data asset deleted successfully"}

