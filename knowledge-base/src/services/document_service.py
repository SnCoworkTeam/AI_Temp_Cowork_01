"""
文档服务
文档业务逻辑层（集成数据库）
"""
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID

from ..repositories.document_repository import DocumentRepository
from ..repositories.chunk_repository import ChunkRepository
from ..repositories.vector_repository import VectorRepository
from ..repositories.search_history_repository import UserBehaviorRepository
from ..core.document_processor import get_document_processor
from ..core.embedding_manager import get_embedding_manager
from ..core.vector_store import get_vector_store
from ..core.memory_optimizer import get_memory_optimizer, StreamingProcessor

# 导入数据库模型
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from database.src.models.knowledge_models import DocumentStatus

logger = logging.getLogger(__name__)


class DocumentService:
    """文档服务（集成数据库）"""
    
    def __init__(self, db: Session):
        self.db = db
        self.document_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.vector_repo = VectorRepository(db)
        self.behavior_repo = UserBehaviorRepository(db)
    
    async def upload_document(
        self,
        filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        uploaded_by: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        process_async: bool = True
    ) -> Dict[str, Any]:
        """
        上传文档
        
        Args:
            filename: 文件名
            file_path: 文件路径
            file_size: 文件大小
            file_type: 文件类型
            uploaded_by: 上传者ID
            tags: 标签列表
            metadata: 元数据
            process_async: 是否异步处理
        
        Returns:
            文档信息字典
        """
        try:
            uploaded_by_uuid = None
            if uploaded_by:
                try:
                    uploaded_by_uuid = UUID(uploaded_by)
                except ValueError:
                    pass
            
            knowledge_base_uuid = None
            if knowledge_base_id:
                try:
                    knowledge_base_uuid = UUID(knowledge_base_id)
                except ValueError:
                    pass
            
            # 创建文档记录
            db_document = self.document_repo.create_document(
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                file_path=file_path,
                uploaded_by=uploaded_by_uuid,
                knowledge_base_id=knowledge_base_uuid,
                tags=tags,
                metadata=metadata
            )
            
            self.db.commit()
            
            document_id = str(db_document.id)
            
            # 异步处理文档（如果需要）
            if not process_async:
                # 同步处理
                await self._process_document(document_id, file_path)
            
            return {
                "document_id": document_id,
                "filename": filename,
                "status": db_document.status.value if hasattr(db_document.status, 'value') else str(db_document.status),
                "message": "Document uploaded successfully"
            }
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}", exc_info=True)
            self.db.rollback()
            raise
    
    async def create_document_from_content(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        process_async: bool = False
    ) -> Dict[str, Any]:
        """
        从内容创建文档（支持JSON数据）
        
        Args:
            title: 文档标题
            content: 文档内容
            category: 文档分类
            tags: 标签列表
            metadata: 元数据
            process_async: 是否异步处理
        
        Returns:
            文档信息字典
        """
        try:
            import tempfile
            import os
            from ..config import settings
            
            # 创建临时文件
            temp_dir = settings.DOCUMENT_STORAGE_DIR
            os.makedirs(temp_dir, exist_ok=True)
            
            # 生成文件名
            filename = f"{title.replace(' ', '_')}.txt"
            file_path = os.path.join(temp_dir, filename)
            
            # 写入内容到临时文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 获取文件大小，确保不为None
            try:
                file_size = os.path.getsize(file_path)
                if file_size is None or file_size < 0:
                    file_size = len(content.encode('utf-8'))  # 使用内容长度作为后备
            except (OSError, ValueError) as e:
                logger.warning(f"Failed to get file size: {e}, using content length")
                file_size = len(content.encode('utf-8'))
            
            # 构建文档元数据
            doc_metadata = metadata or {}
            doc_metadata['title'] = title
            doc_metadata['source'] = 'semantic_index'
            
            # 处理knowledge_base_id
            knowledge_base_uuid = None
            if knowledge_base_id:
                try:
                    knowledge_base_uuid = UUID(knowledge_base_id)
                except ValueError:
                    logger.warning(f"Invalid knowledge_base_id format: {knowledge_base_id}")
            
            # 创建文档记录
            # repository 会将字符串转换为枚举，所以传入 "text" 即可
            db_document = self.document_repo.create_document(
                filename=filename,
                file_type="text",  # repository 会转换为 DocumentType.TEXT
                file_size=file_size,
                file_path=file_path,
                uploaded_by=None,
                knowledge_base_id=knowledge_base_uuid,
                tags=tags or [],
                category=category,
                metadata=doc_metadata
            )
            
            self.db.commit()
            
            document_id = str(db_document.id)
            
            # 处理文档（如果需要）
            if not process_async:
                # 同步处理
                await self._process_document(document_id, file_path)
            
            return {
                "document_id": document_id,
                "filename": filename,
                "title": title,
                "status": db_document.status.value if hasattr(db_document.status, 'value') else str(db_document.status),
                "message": "Document created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating document from content: {str(e)}", exc_info=True)
            self.db.rollback()
            raise
    
    async def _process_document(
        self,
        document_id: str,
        file_path: str,
        chunking_strategy: str = "smart",
        enable_preprocessing: bool = True,
        enable_quality_assessment: bool = True,
        enable_metadata_enhancement: bool = True
    ):
        """
        处理文档（解析、分块、向量化）
        
        增强功能：
        - 进度跟踪
        - 文档预处理
        - 质量评估
        - 元数据增强
        - 错误重试
        """
        from ..core.processing_progress import get_progress_tracker, ProcessingStage
        from ..core.document_preprocessor import get_preprocessor
        from ..core.document_quality import get_quality_assessor
        from ..core.metadata_enhancer import get_metadata_enhancer
        from ..core.error_handler import RetryHandler, RetryConfig
        
        # 初始化进度跟踪器
        progress_tracker = get_progress_tracker(document_id)
        progress_tracker.start_stage(ProcessingStage.PARSING)
        
        # 初始化重试处理器
        retry_handler = RetryHandler(RetryConfig(max_retries=3))
        
        try:
            # 更新状态为处理中
            self.document_repo.update_status(document_id, "processing")
            self.db.commit()
            
            # 步骤1: 文档解析（带重试和超时）
            import asyncio
            async def parse_document():
                processor = get_document_processor()
                # 使用 run_in_executor 在线程池中执行同步操作，避免阻塞事件循环
                # 在后台任务中，应该已经有运行的事件循环
                loop = asyncio.get_running_loop()

                # 添加详细的日志
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                logger.info(f"[Document Processing] Starting parsing for document {document_id}, file: {file_path}, size: {file_size} bytes, strategy: {chunking_strategy}")

                # 根据文件大小动态设置超时时间（从配置读取）
                from ..config import settings
                file_size_mb = file_size / 1024 / 1024
                timeout_seconds = min(
                    settings.DOCUMENT_PARSING_BASE_TIMEOUT + (file_size_mb * settings.DOCUMENT_PARSING_TIMEOUT_PER_MB),
                    settings.DOCUMENT_PROCESSING_TIMEOUT
                )
                logger.info(f"[Document Processing] Setting parsing timeout to {timeout_seconds:.1f} seconds for document {document_id} ({file_size_mb:.2f}MB)")

                try:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: processor.process_document(file_path, chunking_strategy=chunking_strategy)
                        ),
                        timeout=timeout_seconds
                    )
                    logger.info(f"[Document Processing] Parsing completed for document {document_id}")
                    return result
                except asyncio.TimeoutError:
                    logger.error(f"[Document Processing] Parsing timeout after {timeout_seconds:.1f} seconds for document {document_id}, file: {file_path}, size: {file_size} bytes")
                    raise TimeoutError(f"Document parsing timeout after {timeout_seconds:.1f} seconds. File may be too large or corrupted.")
            
            result = await retry_handler.execute_with_retry(
                parse_document,
                error_context={"document_id": document_id, "stage": "parsing", "file_path": file_path}
            )
            
            # 处理返回值
            # process_document 总是返回元组 (text, DocumentMetadata, chunks)
            if isinstance(result, tuple):
                text, document_metadata_obj, chunks = result
                # 将 DocumentMetadata 对象转换为字典
                if hasattr(document_metadata_obj, 'dict'):
                    document_metadata = document_metadata_obj.dict()
                elif hasattr(document_metadata_obj, 'model_dump'):
                    document_metadata = document_metadata_obj.model_dump()
                elif isinstance(document_metadata_obj, dict):
                    document_metadata = document_metadata_obj
                else:
                    # 如果是 Pydantic 模型，手动转换
                    document_metadata = {
                        'title': getattr(document_metadata_obj, 'title', None),
                        'author': getattr(document_metadata_obj, 'author', None),
                        'creation_date': getattr(document_metadata_obj, 'creation_date', None),
                        'modification_date': getattr(document_metadata_obj, 'modification_date', None),
                        'page_count': getattr(document_metadata_obj, 'page_count', None),
                        'word_count': getattr(document_metadata_obj, 'word_count', None),
                        'language': getattr(document_metadata_obj, 'language', None),
                        'custom_metadata': getattr(document_metadata_obj, 'custom_metadata', {})
                    }
            else:
                # 兼容旧格式（字典）
                text = result.get("text", "")
                metadata_obj = result.get("metadata", {})
                if isinstance(metadata_obj, dict):
                    document_metadata = metadata_obj
                else:
                    # 如果是对象，转换为字典
                    if hasattr(metadata_obj, 'dict'):
                        document_metadata = metadata_obj.dict()
                    elif hasattr(metadata_obj, 'model_dump'):
                        document_metadata = metadata_obj.model_dump()
                    else:
                        document_metadata = {}
                chunks = result.get("chunks", [])
            
            progress_tracker.complete_stage(ProcessingStage.PARSING)
            progress_tracker.update_step("parsing", completed=1, total=1)
            
            # 步骤2: 文档预处理
            if enable_preprocessing:
                progress_tracker.start_stage(ProcessingStage.CHUNKING, {"step": "preprocessing"})
                preprocessor = get_preprocessor()
                preprocess_result = preprocessor.preprocess(text)
                text = preprocess_result.cleaned_text
                
                # 更新元数据
                if hasattr(document_metadata, 'language') or isinstance(document_metadata, dict):
                    if isinstance(document_metadata, dict):
                        document_metadata['detected_language'] = preprocess_result.detected_language
                        document_metadata['detected_encoding'] = preprocess_result.detected_encoding
                    else:
                        document_metadata.language = preprocess_result.detected_language
            
            # 步骤3: 文档质量评估
            quality_score = None
            if enable_quality_assessment:
                progress_tracker.update_step("quality_assessment")
                quality_assessor = get_quality_assessor()
                quality_score = quality_assessor.assess_quality(text, document_metadata)
                
                # 更新文档质量评分
                document = self.document_repo.get_by_id(document_id)
                if document:
                    if document.document_metadata is None:
                        document.document_metadata = {}
                    document.document_metadata['quality_score'] = quality_score.overall_score
                    document.document_metadata['quality_details'] = {
                        "completeness": quality_score.completeness_score,
                        "readability": quality_score.readability_score,
                        "uniqueness": quality_score.uniqueness_score
                    }
                    self.db.commit()
            
            # 步骤4: 元数据增强
            if enable_metadata_enhancement:
                progress_tracker.update_step("metadata_enhancement")
                metadata_enhancer = get_metadata_enhancer()
                enhanced_metadata = metadata_enhancer.enhance(text)
                
                # 更新文档元数据
                document = self.document_repo.get_by_id(document_id)
                if document:
                    if document.document_metadata is None:
                        document.document_metadata = {}
                    if enhanced_metadata.summary:
                        document.document_metadata['summary'] = enhanced_metadata.summary
                    if enhanced_metadata.keywords:
                        document.document_metadata['keywords'] = enhanced_metadata.keywords
                    if enhanced_metadata.sentiment:
                        document.document_metadata['sentiment'] = enhanced_metadata.sentiment
                    self.db.commit()
            
            # 步骤5: 文档分块（如果预处理后文本有变化，重新分块）
            progress_tracker.start_stage(ProcessingStage.CHUNKING)
            processor = get_document_processor()
            chunks = processor.chunk_text(text, strategy=chunking_strategy)
            progress_tracker.update_step("chunking", completed=len(chunks), total=len(chunks))
            progress_tracker.complete_stage(ProcessingStage.CHUNKING)
            
            # 追踪知识处理血缘：文档解析步骤
            processing_steps = []
            processing_steps.append({
                "step_name": "document_parsing",
                "step_type": "parsing",
                "input_data": {"file_path": file_path},
                "output_data": {"text": text[:100] if text else "", "chunk_count": len(chunks)},
                "processing_time": None
            })
            
            # 步骤6: 生成嵌入向量（带进度跟踪、重试和批处理）
            progress_tracker.start_stage(ProcessingStage.EMBEDDING)
            progress_tracker.update_step("embedding", completed=0, total=len(chunks))

            # 批处理生成embeddings以降低内存占用
            # 使用内存优化器动态调整批次大小
            memory_optimizer = get_memory_optimizer()
            EMBEDDING_BATCH_SIZE = memory_optimizer.calculate_optimal_batch_size(
                len(chunks),
                default_batch_size=15,  # 进一步降低默认批次大小，减少内存占用
                min_batch_size=5,
                max_batch_size=30
            )

            async def generate_embeddings_batch():
                embedding_manager = get_embedding_manager()
                all_embeddings = []
                loop = asyncio.get_running_loop()

                logger.info(f"[Document Processing] Starting embedding generation for {len(chunks)} chunks in batches of {EMBEDDING_BATCH_SIZE}")
                logger.info(f"[Memory] Current usage: {memory_optimizer.get_memory_usage_mb():.2f} MB")

                for batch_start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
                    batch_end = min(batch_start + EMBEDDING_BATCH_SIZE, len(chunks))
                    batch_chunks = chunks[batch_start:batch_end]
                    batch_texts = [chunk.content for chunk in batch_chunks]

                    batch_num = batch_start // EMBEDDING_BATCH_SIZE + 1
                    total_batches = (len(chunks) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

                    # 使用内存监控
                    with memory_optimizer.memory_monitor(f"Embedding batch {batch_num}/{total_batches}"):
                        logger.info(f"[Document Processing] Processing embedding batch {batch_num}/{total_batches} ({len(batch_chunks)} chunks)")

                        # 生成这一批的embeddings
                        batch_embeddings = await loop.run_in_executor(
                            None,
                            lambda texts=batch_texts: embedding_manager.encode(texts, batch_size=8)  # 进一步降低内部批次大小，减少内存峰值
                        )
                        all_embeddings.extend(batch_embeddings)
                        
                        # 立即清理批次embeddings的临时数据
                        del batch_embeddings

                        # 更新进度
                        progress_tracker.update_step("embedding", completed=batch_end, total=len(chunks))

                        # 清理批次数据
                        del batch_texts
                        del batch_chunks

                        # 每批处理后都检查内存并清理
                        if batch_num % 2 == 0:  # 每2批清理一次
                            memory_optimizer.force_gc()
                        
                        # 检查内存阈值并清理
                        if memory_optimizer.check_memory_threshold(0.6):  # 降低阈值到60%
                            logger.warning(f"[Memory] Threshold reached at batch {batch_num}, forcing GC...")
                            memory_optimizer.force_gc()

                    logger.info(f"[Document Processing] Completed batch {batch_num}, total embeddings: {len(all_embeddings)}")

                return all_embeddings

            embeddings = await retry_handler.execute_with_retry(
                generate_embeddings_batch,
                error_context={"document_id": document_id, "stage": "embedding", "chunk_count": len(chunks)}
            )
            
            progress_tracker.update_step("embedding", completed=len(chunks), total=len(chunks))
            progress_tracker.complete_stage(ProcessingStage.EMBEDDING)
            
            # 步骤7: 保存文档块到数据库（分批保存以降低内存占用）
            progress_tracker.start_stage(ProcessingStage.STORING, {"step": "saving_chunks"})
            embedding_manager = get_embedding_manager()
            
            # 分批保存chunks，避免一次性加载所有数据到内存
            CHUNK_SAVE_BATCH_SIZE = 50  # 每批保存50个chunks
            db_chunks = []
            
            for batch_start in range(0, len(chunks), CHUNK_SAVE_BATCH_SIZE):
                batch_end = min(batch_start + CHUNK_SAVE_BATCH_SIZE, len(chunks))
                batch_chunks = chunks[batch_start:batch_end]
                batch_embeddings = embeddings[batch_start:batch_end] if embeddings else [None] * len(batch_chunks)
                
                chunk_data_list = []
                for i, chunk in enumerate(batch_chunks):
                    chunk_data = {
                        "chunk_index": chunk.metadata.chunk_index,
                        "content": chunk.content,
                        "start_char": chunk.metadata.start_char,
                        "end_char": chunk.metadata.end_char,
                        "page_number": chunk.metadata.page_number,
                        "embedding": batch_embeddings[i] if i < len(batch_embeddings) else None,
                        "embedding_model": embedding_manager.model_name if hasattr(embedding_manager, 'model_name') else os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
                        "metadata": chunk.metadata.metadata
                    }
                    chunk_data_list.append(chunk_data)
                
                # 批量创建文档块
                batch_db_chunks = self.chunk_repo.create_chunks_batch(document_id, chunk_data_list)
                db_chunks.extend(batch_db_chunks)
                self.db.commit()
                
                # 清理批次数据
                del chunk_data_list
                del batch_chunks
                
                # 每批保存后清理内存
                if (batch_start // CHUNK_SAVE_BATCH_SIZE) % 5 == 0:
                    memory_optimizer.force_gc()
            
            # 在清理前创建快照，供后续向量存储使用
            # 使用 db_chunks 的 content 字段作为 texts 来源，确保与 embeddings 对齐
            texts_snapshot = [chunk.content for chunk in db_chunks]
            embeddings_snapshot = embeddings[:] if embeddings else []
            
            # 清理大对象
            del chunks
            del embeddings
            memory_optimizer.force_gc()
            progress_tracker.update_step("saving_chunks", completed=len(db_chunks), total=len(db_chunks))
            
            # 追踪知识处理血缘：分块步骤
            processing_steps.append({
                "step_name": "chunking",
                "step_type": "chunking",
                "input_data": {"text_length": len(text) if text else 0},
                "output_data": {"chunk_count": len(db_chunks), "chunk_ids": [str(c.id) for c in db_chunks]},
                "processing_time": None
            })
            
            # 步骤8: 存储到向量数据库（带重试）
            progress_tracker.update_step("storing_vectors")
            async def store_vectors():
                vector_store = get_vector_store()
                chunk_ids = [str(chunk.id) for chunk in db_chunks]
                document = self.document_repo.get_by_id(document_id)
                chunk_metadatas = []
                for chunk in db_chunks:
                    # chunk.chunk_metadata 是 JSONB 字段，应该是一个字典
                    chunk_meta = {}
                    if chunk.chunk_metadata:
                        if isinstance(chunk.chunk_metadata, dict):
                            chunk_meta = chunk.chunk_metadata.copy()
                        else:
                            # 如果不是字典，尝试转换
                            chunk_meta = dict(chunk.chunk_metadata) if hasattr(chunk.chunk_metadata, '__dict__') else {}
                    
                    chunk_metadatas.append({
                        'document_id': document_id,
                        'chunk_index': chunk.chunk_index,
                        'filename': document.filename if document else '',
                        **chunk_meta
                    })
                
                # 使用快照数据，确保在变量被删除后仍能访问
                # 使用 run_in_executor 在线程池中执行同步操作，避免阻塞事件循环
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    lambda: vector_store.add_documents(
                        texts=texts_snapshot,
                        embeddings=embeddings_snapshot,
                        metadatas=chunk_metadatas,
                        ids=chunk_ids
                    )
                )
            
            await retry_handler.execute_with_retry(
                store_vectors,
                error_context={"document_id": document_id, "stage": "storing", "chunk_count": len(db_chunks)}
            )
            
            progress_tracker.update_step("storing_vectors", completed=len(db_chunks), total=len(db_chunks))
            
            # 追踪知识处理血缘：向量嵌入步骤
            processing_steps.append({
                "step_name": "vector_embedding",
                "step_type": "embedding",
                    "input_data": {"chunk_count": len(db_chunks), "model": embedding_manager.model_name if hasattr(embedding_manager, 'model_name') else os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")},
                "output_data": {"vector_count": len(embeddings_snapshot), "vector_store": "chroma"},
                "processing_time": None
            })
            
            # 追踪知识处理血缘到元数据服务
            try:
                import httpx
                from ..config import settings
                async with httpx.AsyncClient() as client:
                    lineage_data = {
                        "document_id": document_id,
                        "processing_id": f"processing_{document_id}",
                        "processing_steps": processing_steps
                    }
                    await client.post(
                        f"{getattr(settings, 'METADATA_SERVICE_URL', 'http://metadata-service:8005')}/api/collection/lineage/knowledge-processing",
                        json=lineage_data
                    )
            except Exception as e:
                logger.warning(f"Failed to track knowledge processing lineage: {str(e)}")
            
            # 更新向量索引信息（在chunk的metadata中）
            chunk_ids = [str(chunk.id) for chunk in db_chunks]
            for i, chunk in enumerate(db_chunks):
                # 注意：这里需要更新数据库中的chunk记录，而不是内存对象
                # 实际实现中应该通过repository更新
                pass
            self.db.commit()
            
            progress_tracker.complete_stage(ProcessingStage.STORING)
            
            # 步骤9: 更新文档状态和元数据
            progress_tracker.update_step("finalizing")
            document = self.document_repo.get_by_id(document_id)
            doc_metadata_dict = document_metadata
            if hasattr(document_metadata, 'dict'):
                doc_metadata_dict = document_metadata.dict()
            elif hasattr(document_metadata, '__dict__'):
                doc_metadata_dict = document_metadata.__dict__
            
            # 更新文档状态和元数据
            if document:
                document.status = DocumentStatus.PROCESSED
                document.processed_at = datetime.utcnow()
                # 更新 document_metadata（统一命名）
                if document.document_metadata is None:
                    document.document_metadata = {}
                if doc_metadata_dict:
                    # 如果 document_metadata 是字典，合并它
                    if isinstance(doc_metadata_dict, dict):
                        document.document_metadata.update(doc_metadata_dict)
                    else:
                        document.document_metadata['document_metadata'] = doc_metadata_dict
                self.db.commit()
            
            # 完成处理
            progress_tracker.start_stage(ProcessingStage.COMPLETED)
            progress_tracker.update_step("completed", completed=1, total=1)
            
            logger.info(f"Document {document_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            progress_tracker.set_error(str(e))
            self.document_repo.update_status(document_id, "failed")
            self.db.commit()
            raise
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取文档详情"""
        try:
            db_document = self.document_repo.get_by_id(document_id)
            if not db_document:
                return None
            
            # 获取文档块
            chunks = self.chunk_repo.get_by_document_id(document_id)
            
            # 记录查看行为
            self.behavior_repo.create_behavior(
                user_id=None,  # 可以从认证中间件获取
                action_type="view",
                target_type="document",
                target_id=document_id
            )
            self.db.commit()
            
            return self._document_to_dict(db_document, chunks)
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}", exc_info=True)
            return None
    
    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        uploaded_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """列出文档"""
        try:
            uploaded_by_uuid = None
            if uploaded_by:
                try:
                    uploaded_by_uuid = UUID(uploaded_by)
                except ValueError:
                    pass
            
            knowledge_base_uuid = None
            if knowledge_base_id:
                try:
                    knowledge_base_uuid = UUID(knowledge_base_id)
                except ValueError:
                    pass
            
            skip = (page - 1) * page_size
            documents = self.document_repo.list_documents(
                skip=skip,
                limit=page_size,
                status=status,
                knowledge_base_id=knowledge_base_uuid,
                category=category,
                tags=tags,
                uploaded_by=uploaded_by_uuid,
                search=search
            )
            
            # 获取总数（排除DELETED状态的文档）
            total = self.document_repo.count_documents(
                status=status,
                knowledge_base_id=knowledge_base_uuid,
                category=category,
                tags=tags,
                uploaded_by=uploaded_by_uuid,
                search=search
            )
            
            # 转换为字典（为每个文档获取chunks数量）
            document_dicts = []
            for doc in documents:
                # 获取文档的chunks数量
                chunks = self.chunk_repo.get_by_document_id(str(doc.id))
                document_dicts.append(self._document_to_dict(doc, chunks))
            
            return {
                "documents": document_dicts,
                "total": total,
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}", exc_info=True)
            return {
                "documents": [],
                "total": 0,
                "page": page,
                "page_size": page_size
            }
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            # 检查文档是否存在
            document = self.document_repo.get_by_id(document_id)
            if not document:
                logger.warning(f"Document {document_id} not found for deletion")
                return False
            
            logger.info(f"Starting deletion of document {document_id} (filename: {document.filename})")
            
            # 删除向量索引
            chunks = self.chunk_repo.get_chunks_with_embeddings(document_id)
            logger.info(f"Found {len(chunks)} chunks with embeddings for document {document_id}")
            
            if chunks:
                vector_store = get_vector_store()
                chunk_ids = [str(chunk.id) for chunk in chunks]
                
                # 批量删除向量（更高效）
                try:
                    vector_store.delete(ids=chunk_ids)
                    logger.info(f"Deleted {len(chunk_ids)} vectors from vector store")
                except Exception as e:
                    logger.warning(f"Failed to delete vectors from vector store: {str(e)}")
                    # 继续删除，不因为向量删除失败而阻止文档删除
                    # 尝试逐个删除
                    for chunk_id in chunk_ids:
                        try:
                            vector_store.delete(ids=[chunk_id])
                        except Exception as ve:
                            logger.warning(f"Failed to delete vector {chunk_id}: {str(ve)}")
            
            # 删除文档块
            deleted_chunks_count = self.chunk_repo.delete_by_document_id(document_id)
            logger.info(f"Deleted {deleted_chunks_count} chunks from database")
            
            # 软删除文档
            success = self.document_repo.delete_document(document_id)
            
            if success:
                self.db.commit()
                logger.info(f"Document {document_id} deleted successfully")
            else:
                logger.warning(f"Failed to delete document {document_id} (document not found or already deleted)")
                self.db.rollback()
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    def _document_to_dict(self, db_document, chunks: List) -> Dict[str, Any]:
        """将数据库文档模型转换为字典"""
        return {
            "id": str(db_document.id),
            "filename": db_document.filename,
            "file_type": db_document.file_type.value if hasattr(db_document.file_type, 'value') else str(db_document.file_type),
            "file_size": db_document.file_size,
            "file_path": db_document.file_path,
            "status": db_document.status.value if hasattr(db_document.status, 'value') else str(db_document.status),
            "version": db_document.version,
            "tags": db_document.tags or [],
            "category": db_document.category,
            "knowledge_base_id": str(db_document.knowledge_base_id) if db_document.knowledge_base_id else None,
            "quality_score": db_document.quality_score,
            "summary": db_document.summary,
            "metadata": db_document.document_metadata or {},
            "document_metadata": db_document.document_metadata or {},
            "total_chunks": len(chunks) if chunks else 0,
            "uploaded_at": db_document.created_at.isoformat() if db_document.created_at else None,
            "processed_at": db_document.processed_at.isoformat() if db_document.processed_at else None,
            "updated_at": db_document.updated_at.isoformat() if db_document.updated_at else None
        }

