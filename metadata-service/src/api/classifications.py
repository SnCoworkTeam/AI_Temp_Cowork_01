"""
分类管理API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func
from pydantic import BaseModel

from ..core.database import get_db
from ..models.data_asset import DataAsset
from ..services.classification_management_service import ClassificationManagementService
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


class ClassificationCreate(BaseModel):
    """创建分类请求"""
    name: str
    display_name: str
    description: Optional[str] = None
    parent: Optional[str] = None


class ClassificationUpdate(BaseModel):
    """更新分类请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None


def get_classification_service(db: Session = Depends(get_db)) -> ClassificationManagementService:
    """获取分类管理服务"""
    return ClassificationManagementService(db)


@router.get(
    "/classifications",
    response_model=Dict[str, Any],
    summary="获取所有分类",
    tags=["Metadata"]
)
async def get_classifications(
    db: Session = Depends(get_db)
):
    """获取所有可用的分类列表"""
    try:
        # 获取所有唯一的分类值
        classifications = db.query(
            distinct(DataAsset.classification).label("classification")
        ).filter(
            DataAsset.classification.isnot(None),
            DataAsset.classification != ""
        ).all()
        
        classification_list = [c.classification for c in classifications if c.classification]
        
        # 获取每个分类的资产数量
        classification_counts = {}
        for classification in classification_list:
            count = db.query(func.count(DataAsset.id)).filter(
                DataAsset.classification == classification
            ).scalar()
            classification_counts[classification] = count
        
        # 定义有效分类列表（从quality_rules_engine.py中提取）
        valid_classifications = [
            "sap_master_data_customer",
            "sap_master_data_vendor",
            "sap_master_data_material",
            "sap_transaction_sales_order",
            "sap_transaction_purchase_order",
            "sap_odata_entity",
            "sap_table"
        ]
        
        return {
            "classifications": classification_list,
            "counts": classification_counts,
            "valid_classifications": valid_classifications,
            "total": len(classification_list)
        }
    except Exception as e:
        logger.error(f"Failed to get classifications: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/classifications/{classification}/assets",
    response_model=List[Dict[str, Any]],
    summary="获取指定分类的资产",
    tags=["Metadata"]
)
async def get_assets_by_classification(
    classification: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取指定分类的所有资产"""
    try:
        assets = db.query(DataAsset).filter(
            DataAsset.classification == classification
        ).offset(skip).limit(limit).all()
        
        return [
            {
                "id": asset.id,
                "name": asset.name,
                "display_name": asset.display_name,
                "asset_type": asset.asset_type,
                "classification": asset.classification,
                "domain": asset.domain,
                "status": asset.status
            }
            for asset in assets
        ]
    except Exception as e:
        logger.error(f"Failed to get assets by classification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== 分类管理API（企业架构） ==========

@router.post(
    "/classifications",
    summary="创建分类",
    tags=["Metadata"]
)
async def create_classification(
    classification_data: ClassificationCreate,
    service: ClassificationManagementService = Depends(get_classification_service)
):
    """创建新的分类"""
    try:
        return service.create_classification(
            name=classification_data.name,
            display_name=classification_data.display_name,
            description=classification_data.description,
            parent_name=classification_data.parent
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create classification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/classifications/managed",
    summary="获取管理的分类列表",
    tags=["Metadata"]
)
async def list_managed_classifications(
    service: ClassificationManagementService = Depends(get_classification_service)
):
    """获取所有管理的分类列表（树形结构）"""
    try:
        return service.list_classifications()
    except Exception as e:
        logger.error(f"Failed to list classifications: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/classifications/managed/{name}",
    summary="获取分类详情",
    tags=["Metadata"]
)
async def get_managed_classification(
    name: str,
    service: ClassificationManagementService = Depends(get_classification_service)
):
    """获取分类详情"""
    try:
        classification = service.get_classification(name)
        if not classification:
            raise HTTPException(status_code=404, detail=f"Classification '{name}' not found")
        return classification
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get classification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/classifications/managed/{name}",
    summary="更新分类",
    tags=["Metadata"]
)
async def update_classification(
    name: str,
    classification_data: ClassificationUpdate,
    service: ClassificationManagementService = Depends(get_classification_service)
):
    """更新分类"""
    try:
        return service.update_classification(
            name=name,
            display_name=classification_data.display_name,
            description=classification_data.description
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update classification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/classifications/managed/{name}",
    summary="删除分类",
    tags=["Metadata"]
)
async def delete_classification(
    name: str,
    service: ClassificationManagementService = Depends(get_classification_service)
):
    """删除分类"""
    try:
        service.delete_classification(name)
        return {"message": f"Classification '{name}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete classification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




