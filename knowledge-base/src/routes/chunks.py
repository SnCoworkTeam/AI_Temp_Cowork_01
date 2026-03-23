"""
文档块查询API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID

from ..dependencies.database import get_db
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get(
    "/documents/{document_id}/chunks",
    summary="获取文档的所有分块",
    description="获取指定文档的所有chunks",
    tags=["Documents"]
)
async def get_document_chunks(
    document_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取文档的所有chunks"""
    try:
        # 导入模型
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))
        from database.src.models.knowledge_models import Document, DocumentChunk

        # 验证文档是否存在
        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document ID format")

        document = db.query(Document).filter(Document.id == doc_uuid).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # 查询chunks
        skip = (page - 1) * page_size
        chunks_query = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc_uuid
        ).order_by(DocumentChunk.chunk_index)

        total = chunks_query.count()
        chunks = chunks_query.offset(skip).limit(page_size).all()

        # 转换为字典
        chunks_data = []
        for chunk in chunks:
            chunk_dict = {
                "id": str(chunk.id),
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "page_number": chunk.page_number,
                "embedding_model": chunk.embedding_model,
                "metadata": chunk.chunk_metadata or {},
                "created_at": chunk.created_at.isoformat() if chunk.created_at else None
            }
            chunks_data.append(chunk_dict)

        return {
            "document_id": document_id,
            "document_name": document.filename,
            "chunks": chunks_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get document chunks: {str(e)}")


@router.get(
    "/chunks/{chunk_id}",
    summary="获取单个分块详情",
    description="获取指定chunk的详细信息",
    tags=["Documents"]
)
async def get_chunk_detail(
    chunk_id: str,
    db: Session = Depends(get_db)
):
    """获取单个chunk详情"""
    try:
        # 导入模型
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))
        from database.src.models.knowledge_models import DocumentChunk, Document

        try:
            chunk_uuid = UUID(chunk_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid chunk ID format")

        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_uuid).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")

        # 获取文档信息
        document = db.query(Document).filter(Document.id == chunk.document_id).first()

        return {
            "id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "document_name": document.filename if document else None,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char,
            "page_number": chunk.page_number,
            "embedding_model": chunk.embedding_model,
            "metadata": chunk.chunk_metadata or {},
            "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
            "updated_at": chunk.updated_at.isoformat() if chunk.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chunk detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get chunk detail: {str(e)}")
