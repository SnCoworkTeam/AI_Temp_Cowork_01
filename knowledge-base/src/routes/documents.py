"""
文档管理API路由
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uuid
import os
import shutil
from pathlib import Path
from datetime import datetime

from ..models.document_models import (
    Document, DocumentUploadRequest, DocumentUploadResponse,
    DocumentListResponse, DocumentFilterParams, DocumentStatus, DocumentType
)
from ..core.document_processor import get_document_processor
from ..core.embedding_manager import get_embedding_manager
from ..core.vector_store import get_vector_store
from ..core.auto_tagger import get_auto_tagger
from ..core.category_classifier import get_category_classifier
from ..core.quality_assessor import get_quality_assessor
from ..core.auto_summarizer import get_auto_summarizer
from ..config import settings

# 尝试导入外部日志库，如果失败则使用标准库
try:
    from luminaos_common.common.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    # 回退到标准库 logging
    import logging
    logger = logging.getLogger(__name__)
    # 如果还没有配置日志，设置基本配置
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

# 尝试导入外部错误处理，如果失败则使用本地实现
try:
    from luminaos_common.common.error_handler import create_error_response
except ImportError:
    # 回退到本地错误处理实现
    def create_error_response(error: Exception, status_code: int = 500) -> JSONResponse:
        """本地错误响应创建函数"""
        return JSONResponse(
            status_code=status_code,
            content={"error": str(error), "detail": "An error occurred"}
        )

router = APIRouter()

# 内存中的文档存储（生产环境应使用数据库）
_documents: dict[str, Document] = {}
_document_files: dict[str, str] = {}  # document_id -> file_path


def get_document_by_id(document_id: str) -> Optional[Document]:
    """根据ID获取文档（供其他模块使用）"""
    return _documents.get(document_id)


def get_all_documents() -> List[Document]:
    """获取所有文档（供其他模块使用）"""
    return list(_documents.values())


def _ensure_storage_dir():
    """确保存储目录存在"""
    os.makedirs(settings.DOCUMENT_STORAGE_DIR, exist_ok=True)


async def _process_document_async(document_id: str, file_path: str):
    """异步处理文档"""
    try:
        logger.info(f"Processing document {document_id}: {file_path}")
        
        # 更新状态
        if document_id in _documents:
            _documents[document_id].status = DocumentStatus.PROCESSING
        
        # 处理文档
        processor = get_document_processor()
        text, metadata, chunks = processor.process_document(file_path)
        
        # 生成嵌入向量
        embedding_manager = get_embedding_manager()
        texts = [chunk.content for chunk in chunks]
        embeddings = embedding_manager.encode(texts)
        
        # 存储到向量数据库
        vector_store = get_vector_store()
        chunk_ids = []
        chunk_metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk.embedding = embeddings[i]
            chunk_metadata = {
                'document_id': document_id,
                'chunk_index': chunk.metadata.chunk_index,
                'filename': _documents[document_id].filename,
                **chunk.metadata.metadata
            }
            chunk_metadatas.append(chunk_metadata)
            chunk_ids.append(chunk.chunk_id)
        
        vector_store.add_documents(
            texts=texts,
            embeddings=embeddings,
            metadatas=chunk_metadatas,
            ids=chunk_ids
        )
        
        # 更新文档
        if document_id in _documents:
            _documents[document_id].chunks = chunks
            _documents[document_id].total_chunks = len(chunks)
            _documents[document_id].metadata = metadata
            _documents[document_id].status = DocumentStatus.PROCESSED
            _documents[document_id].processed_at = datetime.now()
        
        logger.info(f"Document {document_id} processed successfully")
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
        if document_id in _documents:
            _documents[document_id].status = DocumentStatus.FAILED


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    summary="上传文档",
    description="上传并处理文档",
    tags=["Documents"]
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tags: Optional[str] = None,
    process_async: bool = True
) -> DocumentUploadResponse:
    """
    上传文档
    
    支持批量上传（通过multipart/form-data）
    """
    try:
        # 验证文件类型
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported: {settings.SUPPORTED_EXTENSIONS}"
            )
        
        # 验证文件大小
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # 生成文档ID
        document_id = str(uuid.uuid4())
        
        # 保存文件
        _ensure_storage_dir()
        file_path = os.path.join(settings.DOCUMENT_STORAGE_DIR, f"{document_id}{file_ext}")
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 检测文件类型
        processor = get_document_processor()
        file_type = processor.detect_file_type(file_path)
        
        # 解析标签
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # 创建文档对象
        document = Document(
            id=document_id,
            filename=file.filename,
            file_type=file_type,
            file_size=len(file_content),
            file_path=file_path,
            status=DocumentStatus.UPLOADING,
            metadata=DocumentMetadata(),
            uploaded_at=datetime.now()
        )
        document.tags = tag_list
        
        _documents[document_id] = document
        _document_files[document_id] = file_path
        
        # 处理文档
        if process_async:
            background_tasks.add_task(_process_document_async, document_id, file_path)
            document.status = DocumentStatus.PROCESSING
        else:
            # 同步处理
            await _process_document_async(document_id, file_path)
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status=document.status,
            message="Document uploaded successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="获取文档列表",
    description="获取文档列表（支持分页和过滤）",
    tags=["Documents"]
)
async def list_documents(
    file_type: Optional[DocumentType] = None,
    status: Optional[DocumentStatus] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> DocumentListResponse:
    """获取文档列表"""
    try:
        # 过滤文档
        filtered_docs = list(_documents.values())
        
        if file_type:
            filtered_docs = [doc for doc in filtered_docs if doc.file_type == file_type]
        
        if status:
            filtered_docs = [doc for doc in filtered_docs if doc.status == status]
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            filtered_docs = [
                doc for doc in filtered_docs
                if any(tag in doc.tags for tag in tag_list)
            ]
        
        if search:
            search_lower = search.lower()
            filtered_docs = [
                doc for doc in filtered_docs
                if search_lower in doc.filename.lower()
                or (doc.metadata.title and search_lower in doc.metadata.title.lower())
            ]
        
        # 排序（按上传时间倒序）
        filtered_docs.sort(key=lambda x: x.uploaded_at, reverse=True)
        
        # 分页
        total = len(filtered_docs)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = filtered_docs[start:end]
        
        return DocumentListResponse(
            documents=paginated_docs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@router.get(
    "/documents/{document_id}",
    response_model=Document,
    summary="获取文档详情",
    description="根据ID获取文档详情",
    tags=["Documents"]
)
async def get_document(document_id: str) -> Document:
    """获取文档详情"""
    if document_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return _documents[document_id]


@router.delete(
    "/documents/{document_id}",
    summary="删除文档",
    description="删除文档及其向量数据",
    tags=["Documents"]
)
async def delete_document(document_id: str) -> Dict[str, Any]:
    """删除文档"""
    if document_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        document = _documents[document_id]
        
        # 删除向量数据
        vector_store = get_vector_store()
        chunk_ids = [chunk.chunk_id for chunk in document.chunks]
        if chunk_ids:
            vector_store.delete(chunk_ids)
        
        # 删除文件
        if document_id in _document_files:
            file_path = _document_files[document_id]
            if os.path.exists(file_path):
                os.remove(file_path)
            del _document_files[document_id]
        
        # 标记为已删除
        document.status = DocumentStatus.DELETED
        
        # 从字典中移除
        del _documents[document_id]
        
        return {"message": "Document deleted successfully", "document_id": document_id}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@router.post(
    "/documents/{document_id}/auto-tag",
    summary="自动生成标签",
    description="为文档自动生成标签",
    tags=["Documents"]
)
async def auto_tag_document(document_id: str) -> Dict[str, Any]:
    """自动生成文档标签"""
    if document_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        document = _documents[document_id]
        
        # 获取文档内容
        content = ""
        if document.chunks:
            content = " ".join([chunk.content for chunk in document.chunks])
        else:
            # 如果文档未处理，尝试读取文件
            if document_id in _document_files:
                processor = get_document_processor()
                text, _, _ = processor.process_document(document.file_path)
                content = text
        
        if not content:
            raise HTTPException(status_code=400, detail="Document content not available")
        
        # 生成标签
        tagger = get_auto_tagger(max_tags=10)
        tags = tagger.generate_tags(
            content,
            document_type=document.file_type.value,
            existing_tags=document.tags
        )
        
        # 更新文档标签
        suggested_tags = [tag["tag"] for tag in tags[:5]]  # 取前5个
        document.tags = list(set(document.tags + suggested_tags))
        
        return {
            "document_id": document_id,
            "suggested_tags": suggested_tags,
            "all_tags": tags,
            "current_tags": document.tags
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error auto-tagging document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error auto-tagging document: {str(e)}")


@router.post(
    "/documents/{document_id}/assess-quality",
    summary="评估文档质量",
    description="评估文档的质量和完整性",
    tags=["Documents"]
)
async def assess_document_quality(document_id: str) -> Dict[str, Any]:
    """评估文档质量"""
    if document_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        document = _documents[document_id]
        
        # 获取文档内容
        content = ""
        if document.chunks:
            content = " ".join([chunk.content for chunk in document.chunks])
        else:
            if document_id in _document_files:
                processor = get_document_processor()
                text, _, _ = processor.process_document(document.file_path)
                content = text
        
        if not content:
            raise HTTPException(status_code=400, detail="Document content not available")
        
        # 评估质量
        assessor = get_quality_assessor()
        assessment = assessor.assess(
            content,
            metadata=document.metadata.dict() if document.metadata else None,
            chunks=[chunk.dict() for chunk in document.chunks] if document.chunks else None
        )
        
        return {
            "document_id": document_id,
            "filename": document.filename,
            "assessment": assessment
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing document quality: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error assessing document quality: {str(e)}")


@router.post(
    "/documents/{document_id}/summarize",
    summary="生成文档摘要",
    description="为文档生成摘要",
    tags=["Documents"]
)
async def summarize_document(
    document_id: str,
    method: str = "extractive",
    max_length: Optional[int] = 200
) -> Dict[str, Any]:
    """生成文档摘要"""
    if document_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        document = _documents[document_id]
        
        # 获取文档内容
        content = ""
        if document.chunks:
            content = " ".join([chunk.content for chunk in document.chunks])
        else:
            if document_id in _document_files:
                processor = get_document_processor()
                text, _, _ = processor.process_document(document.file_path)
                content = text
        
        if not content:
            raise HTTPException(status_code=400, detail="Document content not available")
        
        # 生成摘要
        summarizer = get_auto_summarizer(max_summary_length=max_length or 200)
        summary_result = summarizer.summarize(content, method=method)
        
        return {
            "document_id": document_id,
            "filename": document.filename,
            "summary": summary_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error summarizing document: {str(e)}")

