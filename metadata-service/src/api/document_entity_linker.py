"""
文档实体关联API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.document_entity_linker import DocumentEntityLinker
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/document-entity-linker", tags=["Document Entity Linker"])
logger = setup_logger(__name__)


@router.post("/link", summary="关联文档与实体")
async def link_documents_to_entities(
    document_ids: Optional[List[str]] = Body(None, description="文档ID列表，如果为空则处理所有文档"),
    entity_ids: Optional[List[int]] = Body(None, description="实体ID列表，如果为空则处理所有实体"),
    db: Session = Depends(get_db)
):
    """
    将知识库文档与业务实体关联
    
    通过提取文档中的实体名称，自动建立文档与实体的关联关系
    """
    try:
        linker = DocumentEntityLinker(db)
        result = await linker.link_documents_to_entities(
            document_ids=document_ids,
            entity_ids=entity_ids
        )
        await linker.close()
        return result
    except Exception as e:
        logger.error(f"Failed to link documents to entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))







