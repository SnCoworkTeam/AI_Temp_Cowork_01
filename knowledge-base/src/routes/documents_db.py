"""
文档管理API路由（数据库集成版本）
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uuid
import os
from pathlib import Path
from datetime import datetime

from ..models.document_models import (
    DocumentUploadResponse, DocumentListResponse, DocumentStatus, DocumentType,
    DocumentCreateRequest
)
from ..services.document_service import DocumentService
from ..dependencies.database import get_db
from ..config import settings
from luminaos_common.common.logger import setup_logger
from luminaos_common.common.error_handler import create_error_response
from sqlalchemy.orm import Session

router = APIRouter()
logger = setup_logger(__name__)


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """获取文档服务"""
    return DocumentService(db)


def _ensure_storage_dir():
    """确保存储目录存在"""
    try:
        os.makedirs(settings.DOCUMENT_STORAGE_DIR, exist_ok=True)
        logger.info(f"Storage directory ensured: {settings.DOCUMENT_STORAGE_DIR}")
    except Exception as e:
        logger.error(f"Failed to create storage directory {settings.DOCUMENT_STORAGE_DIR}: {str(e)}", exc_info=True)
        raise


async def _process_document_async(document_id: str, file_path: str):
    """
    异步处理文档（在后台任务中执行）
    
    Args:
        document_id: 文档ID
        file_path: 文件路径
    """
    from ..core.database import SessionLocal
    import os
    
    # 验证文件是否存在
    if not os.path.exists(file_path):
        logger.error(f"File not found for document {document_id}: {file_path}")
        # 更新状态为失败
        error_db = SessionLocal()
        try:
            error_service = DocumentService(error_db)
            error_service.document_repo.update_status(document_id, "failed")
            error_db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update document status to failed: {str(update_error)}", exc_info=True)
        finally:
            error_db.close()
        return
    
    # 创建新的数据库会话（后台任务需要独立的会话）
    db = SessionLocal()
    service = None
    try:
        logger.info(f"[Background Task] Starting processing for document {document_id}, file: {file_path}")
        logger.info(f"[Background Task] File exists: {os.path.exists(file_path)}, File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'} bytes")
        
        # 先更新状态为处理中（确保状态正确，即使_process_document内部也会更新）
        service = DocumentService(db)
        service.document_repo.update_status(document_id, "processing")
        db.commit()
        logger.info(f"[Background Task] Document {document_id} status confirmed as processing")
        
        # 执行文档处理（_process_document内部会再次更新状态为processing，这是安全的）
        logger.info(f"[Background Task] Calling _process_document for document {document_id}")
        await service._process_document(document_id, file_path)
        logger.info(f"[Background Task] Document {document_id} processed successfully")
        
    except Exception as e:
        logger.error(f"[Background Task] Error processing document {document_id}: {str(e)}", exc_info=True)
        # 更新状态为失败（使用新的数据库会话，确保状态更新成功）
        error_db = SessionLocal()
        try:
            error_service = DocumentService(error_db)
            error_service.document_repo.update_status(document_id, "failed")
            error_db.commit()
            logger.info(f"[Background Task] Document {document_id} status updated to failed")
        except Exception as update_error:
            logger.error(f"[Background Task] Failed to update document status to failed: {str(update_error)}", exc_info=True)
        finally:
            error_db.close()
    finally:
        if db:
            try:
                db.close()
            except Exception as close_error:
                logger.warning(f"[Background Task] Error closing database session: {str(close_error)}")


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    summary="上传文档",
    description="上传并处理文档（数据库集成版本）",
    tags=["Documents"]
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tags: Optional[str] = None,
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID"),
    process_async: bool = True,  # 改为True，默认异步处理，避免HTTP请求阻塞
    db: Session = Depends(get_db),
    uploaded_by: Optional[str] = None  # 可以从认证中间件获取
) -> DocumentUploadResponse:
    """
    上传文档

    支持批量上传（通过multipart/form-data）
    """
    try:
        logger.info(f"[Document Upload] Starting upload for file: {file.filename}, knowledge_base_id: {knowledge_base_id}, process_async: {process_async}")

        # 验证文件类型
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.SUPPORTED_EXTENSIONS:
            logger.warning(f"[Document Upload] Unsupported file type: {file_ext} for file: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported: {settings.SUPPORTED_EXTENSIONS}"
            )

        # 验证文件大小
        file_content = await file.read()
        file_size_mb = len(file_content) / 1024 / 1024
        logger.info(f"[Document Upload] File size: {file_size_mb:.2f}MB")

        if len(file_content) > settings.MAX_FILE_SIZE:
            logger.warning(f"[Document Upload] File too large: {file_size_mb:.2f}MB > {settings.MAX_FILE_SIZE / 1024 / 1024}MB")
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # 生成文档ID
        document_id = str(uuid.uuid4())
        logger.info(f"[Document Upload] Generated document ID: {document_id}")

        # 保存文件
        _ensure_storage_dir()
        file_path = os.path.join(settings.DOCUMENT_STORAGE_DIR, f"{document_id}{file_ext}")
        with open(file_path, 'wb') as f:
            f.write(file_content)
        logger.info(f"[Document Upload] File saved to: {file_path}")

        # 检测文件类型
        from ..core.document_processor import get_document_processor
        processor = get_document_processor()
        file_type = processor.detect_file_type(file_path)
        logger.info(f"[Document Upload] Detected file type: {file_type}")

        # 解析标签
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            logger.info(f"[Document Upload] Tags: {tag_list}")

        # 使用服务层上传文档
        logger.info(f"[Document Upload] Creating document record in database")
        service = get_document_service(db)
        result = await service.upload_document(
            filename=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            file_type=file_type,
            uploaded_by=uploaded_by,
            knowledge_base_id=knowledge_base_id,
            tags=tag_list,
            process_async=process_async
        )

        document_id = result["document_id"]

        # 处理文档（同步或异步）
        if process_async:
            logger.info(f"[Document Upload] Starting async processing for document {document_id}")
            # 立即更新状态为PROCESSING，避免前端一直显示"上传中"
            service.document_repo.update_status(document_id, "processing")
            db.commit()
            logger.info(f"[Document Upload] Document {document_id} status updated to processing, starting background task")

            # 添加到后台任务
            background_tasks.add_task(_process_document_async, document_id, file_path)

            # 返回处理中状态
            return DocumentUploadResponse(
                document_id=document_id,
                filename=result["filename"],
                status=DocumentStatus.PROCESSING,
                message="Document uploaded and processing started"
            )
        else:
            logger.info(f"[Document Upload] Starting synchronous processing for document {document_id}")
            # 同步处理，返回实际状态
            final_status = DocumentStatus(result["status"])
            logger.info(f"[Document Upload] Document {document_id} processing completed with status: {final_status}")

            return DocumentUploadResponse(
                document_id=document_id,
                filename=result["filename"],
                status=final_status,
                message=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.post(
    "/documents/{document_id}/retry",
    response_model=DocumentUploadResponse,
    summary="重试文档处理",
    description="重新处理失败的文档（数据库集成版本）",
    tags=["Documents"]
)
async def retry_document_processing(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> DocumentUploadResponse:
    """重试处理失败文档"""
    service = get_document_service(db)
    document = service.document_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if hasattr(document, "status") and str(document.status).lower() == "deleted":
        raise HTTPException(status_code=400, detail="Document is deleted and cannot be retried")

    file_path = getattr(document, "file_path", None)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document file not found for retry")

    # 清理已存在的chunks与向量（避免重复）
    try:
        existing_chunks = service.chunk_repo.get_by_document_id(document_id)
        if existing_chunks:
            try:
                from ..core.vector_store import get_vector_store
                vector_store = get_vector_store()
                chunk_ids = [str(chunk.id) for chunk in existing_chunks]
                vector_store.delete(ids=chunk_ids)
                logger.info(f"[Document Retry] Deleted {len(chunk_ids)} vectors for document {document_id}")
            except Exception as ve:
                logger.warning(f"[Document Retry] Failed to delete vectors: {str(ve)}")

        deleted_count = service.chunk_repo.delete_by_document_id(document_id)
        if deleted_count:
            logger.info(f"[Document Retry] Deleted {deleted_count} chunks for document {document_id}")
        db.commit()
    except Exception as cleanup_err:
        logger.warning(f"[Document Retry] Cleanup failed for document {document_id}: {cleanup_err}")
        db.rollback()

    # 更新状态为处理中
    service.document_repo.update_status(document_id, "processing")
    db.commit()

    # 启动后台处理
    background_tasks.add_task(_process_document_async, document_id, file_path)

    return DocumentUploadResponse(
        document_id=document_id,
        filename=document.filename,
        status=DocumentStatus.PROCESSING,
        message="Document reprocessing started"
    )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="获取文档列表",
    description="获取文档列表（支持分页和过滤，数据库集成版本）",
    tags=["Documents"]
)
async def list_documents(
    file_type: Optional[DocumentType] = Query(None, description="文件类型过滤"),
    status: Optional[DocumentStatus] = Query(None, description="状态过滤"),
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID过滤"),
    tags: Optional[str] = Query(None, description="标签过滤（逗号分隔）"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db),
    uploaded_by: Optional[str] = Query(None, description="上传者ID")
) -> DocumentListResponse:
    """获取文档列表"""
    try:
        service = get_document_service(db)
        
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        result = await service.list_documents(
            page=page,
            page_size=page_size,
            status=status.value if status else None,
            knowledge_base_id=knowledge_base_id,
            category=category,
            tags=tag_list,
            search=search,
            uploaded_by=uploaded_by
        )
        
        # 转换为Pydantic模型
        from ..models.document_models import Document, DocumentMetadata
        
        document_models = []
        for doc_dict in result["documents"]:
            # 转换文档元数据
            doc_metadata = doc_dict.get("document_metadata", {})
            metadata = DocumentMetadata(**doc_metadata) if doc_metadata else DocumentMetadata()
            
            document_models.append(Document(
                id=doc_dict["id"],
                filename=doc_dict["filename"],
                file_type=DocumentType(doc_dict["file_type"]),
                file_size=doc_dict["file_size"],
                file_path=doc_dict["file_path"],
                status=DocumentStatus(doc_dict["status"]),
                metadata=metadata,
                chunks=[],  # 不包含块列表（减少数据量）
                total_chunks=doc_dict.get("total_chunks", 0),
                uploaded_at=datetime.fromisoformat(doc_dict["uploaded_at"]) if doc_dict.get("uploaded_at") else datetime.now(),
                processed_at=datetime.fromisoformat(doc_dict["processed_at"]) if doc_dict.get("processed_at") else None,
                version=doc_dict.get("version", 1),
                tags=doc_dict.get("tags", []),
                created_by=uploaded_by
            ))
        
        total_pages = (result["total"] + page_size - 1) // page_size
        
        return DocumentListResponse(
            documents=document_models,
            total=result["total"],
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@router.get(
    "/documents/{document_id}",
    summary="获取文档详情",
    description="根据ID获取文档详情（数据库集成版本）",
    tags=["Documents"]
)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取文档详情"""
    try:
        service = get_document_service(db)
        document = await service.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting document: {str(e)}")


@router.post(
    "/documents/create",
    summary="创建文档（支持JSON数据）",
    description="从JSON数据创建文档，用于语义索引等场景",
    tags=["Documents"]
)
async def create_document(
    request: DocumentCreateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """从内容创建文档"""
    try:
        logger.info(f"收到创建文档请求: title={request.title}, category={request.category}, tags={request.tags}")
        logger.info(f"内容长度: {len(request.content)} 字符, process_async={request.process_async}")
        
        service = get_document_service(db)
        result = await service.create_document_from_content(
            title=request.title,
            content=request.content,
            category=request.category,
            knowledge_base_id=request.knowledge_base_id,
            tags=request.tags,
            metadata=request.metadata,
            process_async=request.process_async
        )
        
        logger.info(f"文档创建成功: document_id={result.get('document_id', 'unknown')}")
        return result
        
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating document: {str(e)}")


@router.delete(
    "/documents/{document_id}",
    summary="删除文档",
    description="删除文档及其向量数据（数据库集成版本）",
    tags=["Documents"]
)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """删除文档"""
    try:
        service = get_document_service(db)
        success = await service.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")







