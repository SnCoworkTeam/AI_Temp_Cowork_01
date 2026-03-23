"""
智能搜索API路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..models.document_models import (
    SemanticSearchRequest, KeywordSearchRequest,
    SearchResponse, SearchResult, ChunkMetadata
)
from ..core.embedding_manager import get_embedding_manager
from ..core.vector_store import get_vector_store
from luminaos_common.common.logger import setup_logger
from luminaos_common.common.error_handler import create_error_response

# 导入文档存储（从documents模块）
from ..routes import documents as documents_module

router = APIRouter()
logger = setup_logger(__name__)


@router.post(
    "/search/semantic",
    response_model=SearchResponse,
    summary="语义搜索",
    description="基于向量相似度的语义搜索",
    tags=["Search"]
)
async def semantic_search(request: SemanticSearchRequest) -> SearchResponse:
    """
    语义搜索

    将查询文本转换为向量，在向量数据库中进行相似度搜索
    """
    try:
        # 如果指定了knowledge_base_id，获取该知识库下的所有文档ID
        if request.knowledge_base_id:
            kb_documents = [doc_id for doc_id, doc in documents_module._documents.items()
                           if hasattr(doc, 'knowledge_base_id') and doc.knowledge_base_id == request.knowledge_base_id]
            if not kb_documents:
                # 如果知识库没有文档，返回空结果
                return SearchResponse(
                    results=[],
                    total=0,
                    query=request.query,
                    search_type="semantic"
                )
            # 如果也指定了document_ids，取交集
            if request.document_ids:
                request.document_ids = list(set(request.document_ids) & set(kb_documents))
            else:
                request.document_ids = kb_documents

        # 生成查询向量
        embedding_manager = get_embedding_manager()
        query_embedding = embedding_manager.encode_single(request.query)

        # 构建过滤条件
        filters = {}
        if request.document_ids:
            # 注意：这取决于向量存储的实现，可能需要调整
            filters['document_id'] = request.document_ids[0] if len(request.document_ids) == 1 else None

        if request.filters:
            filters.update(request.filters)

        # 在向量存储中搜索
        vector_store = get_vector_store()
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            filters=filters if filters else None
        )

        # 过滤结果
        filtered_results = []
        for result in results:
            # 应用最小分数过滤
            score = result.get('score', 0.0)
            if score < request.min_score:
                continue

            # 应用文档ID过滤
            if request.document_ids:
                doc_id = result.get('metadata', {}).get('document_id')
                if doc_id not in request.document_ids:
                    continue

            # 获取文档信息
            doc_id = result.get('metadata', {}).get('document_id', '')
            document = documents_module._documents.get(doc_id)

            if not document:
                continue

            # 构建块元数据
            chunk_metadata = ChunkMetadata(
                chunk_id=result['id'],
                chunk_index=result.get('metadata', {}).get('chunk_index', 0),
                start_char=0,
                end_char=0,
                metadata=result.get('metadata', {})
            )

            search_result = SearchResult(
                chunk_id=result['id'],
                document_id=doc_id,
                document_name=document.filename,
                content=result['content'],
                score=score,
                metadata=result.get('metadata', {}),
                chunk_metadata=chunk_metadata
            )

            filtered_results.append(search_result)

        # 按分数排序
        filtered_results.sort(key=lambda x: x.score, reverse=True)

        return SearchResponse(
            results=filtered_results[:request.top_k],
            total=len(filtered_results),
            query=request.query,
            search_type="semantic"
        )
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in semantic search: {str(e)}")


@router.post(
    "/search/keyword",
    response_model=SearchResponse,
    summary="关键词搜索",
    description="基于关键词的全文搜索",
    tags=["Search"]
)
async def keyword_search(request: KeywordSearchRequest) -> SearchResponse:
    """
    关键词搜索

    在文档内容中搜索关键词
    """
    try:
        # 如果指定了knowledge_base_id，获取该知识库下的所有文档ID
        if request.knowledge_base_id:
            kb_documents = [doc_id for doc_id, doc in documents_module._documents.items()
                           if hasattr(doc, 'knowledge_base_id') and doc.knowledge_base_id == request.knowledge_base_id]
            # 如果也指定了document_ids，取交集
            if request.document_ids:
                request.document_ids = list(set(request.document_ids) & set(kb_documents))
            else:
                request.document_ids = kb_documents

        results = []

        # 遍历所有文档
        for doc_id, document in documents_module._documents.items():
            # 应用文档ID过滤
            if request.document_ids and doc_id not in request.document_ids:
                continue

            # 跳过已删除的文档
            if document.status.value == 'deleted':
                continue

            # 在文档块中搜索
            for chunk in document.chunks:
                content_lower = chunk.content.lower()
                keywords_lower = [kw.lower() for kw in request.keywords]

                # 检查关键词匹配
                if request.match_all:
                    # 必须匹配所有关键词
                    if not all(kw in content_lower for kw in keywords_lower):
                        continue
                else:
                    # 匹配任意关键词
                    if not any(kw in content_lower for kw in keywords_lower):
                        continue

                # 计算匹配分数（简单实现：关键词出现次数）
                score = sum(content_lower.count(kw) for kw in keywords_lower)
                score = min(score / 10.0, 1.0)  # 归一化到0-1

                # 提取包含关键词的片段
                content_snippet = chunk.content
                if len(content_snippet) > 500:
                    # 查找第一个关键词的位置
                    first_keyword_pos = -1
                    for kw in keywords_lower:
                        pos = content_lower.find(kw)
                        if pos != -1 and (first_keyword_pos == -1 or pos < first_keyword_pos):
                            first_keyword_pos = pos

                    if first_keyword_pos != -1:
                        start = max(0, first_keyword_pos - 100)
                        end = min(len(content_snippet), first_keyword_pos + 400)
                        content_snippet = content_snippet[start:end]
                        if start > 0:
                            content_snippet = "..." + content_snippet
                        if end < len(content_snippet):
                            content_snippet = content_snippet + "..."

                search_result = SearchResult(
                    chunk_id=chunk.chunk_id,
                    document_id=doc_id,
                    document_name=document.filename,
                    content=content_snippet,
                    score=score,
                    metadata={},
                    chunk_metadata=chunk.metadata
                )

                results.append(search_result)

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)

        # 分页
        total = len(results)
        start = (request.page - 1) * request.page_size
        end = start + request.page_size
        paginated_results = results[start:end]

        return SearchResponse(
            results=paginated_results,
            total=total,
            query=", ".join(request.keywords),
            search_type="keyword"
        )
    except Exception as e:
        logger.error(f"Error in keyword search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in keyword search: {str(e)}")


@router.get(
    "/search/hybrid",
    summary="混合搜索",
    description="结合语义搜索和关键词搜索",
    tags=["Search"]
)
async def hybrid_search(
    query: str,
    keywords: str = "",
    top_k: int = 10,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3
) -> Dict[str, Any]:
    """
    混合搜索
    
    结合语义搜索和关键词搜索的结果
    """
    try:
        # 执行语义搜索
        semantic_request = SemanticSearchRequest(query=query, top_k=top_k * 2)
        semantic_response = await semantic_search(semantic_request)
        
        # 执行关键词搜索
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        if keyword_list:
            keyword_request = KeywordSearchRequest(keywords=keyword_list, top_k=top_k * 2)
            keyword_response = await keyword_search(keyword_request)
        else:
            keyword_response = SearchResponse(results=[], total=0, query="", search_type="keyword")
        
        # 合并结果
        result_map: Dict[str, SearchResult] = {}
        
        # 添加语义搜索结果
        for result in semantic_response.results:
            key = result.chunk_id
            if key not in result_map:
                result.score = result.score * semantic_weight
                result_map[key] = result
            else:
                result_map[key].score += result.score * semantic_weight
        
        # 添加关键词搜索结果
        for result in keyword_response.results:
            key = result.chunk_id
            if key not in result_map:
                result.score = result.score * keyword_weight
                result_map[key] = result
            else:
                result_map[key].score += result.score * keyword_weight
        
        # 排序并返回Top-K
        combined_results = sorted(result_map.values(), key=lambda x: x.score, reverse=True)
        
        return {
            "results": combined_results[:top_k],
            "total": len(combined_results),
            "query": query,
            "keywords": keywords,
            "search_type": "hybrid"
        }
    except Exception as e:
        logger.error(f"Error in hybrid search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in hybrid search: {str(e)}")

