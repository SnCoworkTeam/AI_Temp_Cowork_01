"""
本体构建API路由（已迁移到metadata-service）

⚠️ DEPRECATED: 此功能已迁移到metadata-service
请使用 metadata-service 的 /api/ontology 端点

迁移日期: 2025-11-28
迁移原因: 职责重构，业务本体功能应属于metadata-service
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
import os

from ..core.database import SessionLocal
from shared_libs.luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/ontology", tags=["Ontology (Deprecated)"])
logger = setup_logger(__name__)

# metadata-service URL（用于重定向）
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8005")


# 以下函数已不再使用，保留仅为兼容性
# def get_db():
#     """获取数据库会话"""
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#
# def get_ontology_builder(db: Session = Depends(get_db)) -> OntologyBuilder:
#     """获取本体构建器"""
#     kg_repo = KnowledgeGraphRepository(db)
#     return OntologyBuilder(db, kg_repo)


@router.post("/build", summary="构建业务本体（已迁移）", deprecated=True)
async def build_ontology():
    """
    ⚠️ DEPRECATED: 此功能已迁移到metadata-service
    
    请使用: POST http://metadata-service:8005/api/ontology/build
    
    此端点将重定向到metadata-service
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{METADATA_SERVICE_URL}/api/ontology/build"
            )
            response.raise_for_status()
            result = response.json()
            result["_migration_note"] = "此功能已迁移到metadata-service，请更新您的客户端代码"
            return result
    except Exception as e:
        logger.error(f"Failed to redirect to metadata-service: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"此功能已迁移到metadata-service，但重定向失败: {str(e)}。请直接使用 metadata-service 的 /api/ontology/build 端点"
        )


@router.get("/concepts", summary="获取概念列表（已迁移）", deprecated=True)
async def get_concepts(
    skip: int = 0,
    limit: int = 100
):
    """
    ⚠️ DEPRECATED: 此功能已迁移到metadata-service
    
    请使用: GET http://metadata-service:8005/api/ontology/concepts?skip={skip}&limit={limit}
    
    此端点将重定向到metadata-service
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{METADATA_SERVICE_URL}/api/ontology/concepts",
                params={"skip": skip, "limit": limit}
            )
            response.raise_for_status()
            result = response.json()
            result["_migration_note"] = "此功能已迁移到metadata-service，请更新您的客户端代码"
            return result
    except Exception as e:
        logger.error(f"Failed to redirect to metadata-service: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"此功能已迁移到metadata-service，但重定向失败: {str(e)}。请直接使用 metadata-service 的 /api/ontology/concepts 端点"
        )


@router.post("/sap/build", summary="构建SAP业务本体（已迁移）", deprecated=True)
async def build_sap_ontology():
    """
    ⚠️ DEPRECATED: 此功能已迁移到metadata-service
    
    请使用: POST http://metadata-service:8005/api/ontology/sap/build
    
    此端点将重定向到metadata-service
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{METADATA_SERVICE_URL}/api/ontology/sap/build"
            )
            response.raise_for_status()
            result = response.json()
            result["_migration_note"] = "此功能已迁移到metadata-service，请更新您的客户端代码"
            return result
    except Exception as e:
        logger.error(f"Failed to redirect to metadata-service: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"此功能已迁移到metadata-service，但重定向失败: {str(e)}。请直接使用 metadata-service 的 /api/ontology/sap/build 端点"
        )

