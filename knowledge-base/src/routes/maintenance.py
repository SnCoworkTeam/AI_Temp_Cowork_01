"""
知识库维护API路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.knowledge_maintainer import get_knowledge_maintainer
from ..core.outdated_detector import get_outdated_detector
from ..core.duplicate_detector import get_duplicate_detector
from ..routes.documents import get_all_documents
from luminaos_common.common.logger import setup_logger
from luminaos_common.common.error_handler import create_error_response

router = APIRouter()
logger = setup_logger(__name__)


@router.get(
    "/maintenance/outdated",
    summary="检测过时内容",
    description="检测知识库中的过时文档",
    tags=["Maintenance"]
)
async def get_outdated_documents(
    max_age_days: int = Query(365, description="最大年龄（天数）"),
    severity: Optional[str] = Query(None, description="严重程度过滤（high, medium, low）")
) -> Dict[str, Any]:
    """检测过时文档"""
    try:
        # 获取所有文档
        all_docs = list(_documents.values())
        
        # 转换为字典格式
        documents = []
        for doc in all_docs:
            documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "content": " ".join([chunk.content for chunk in doc.chunks]) if doc.chunks else "",
                "metadata": doc.metadata.dict() if doc.metadata else {},
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                "version": doc.version
            })
        
        # 检测过时文档
        detector = get_outdated_detector(max_age_days=max_age_days)
        outdated_docs = detector.detect_outdated(documents)
        
        # 按严重程度过滤
        if severity:
            outdated_docs = [doc for doc in outdated_docs if doc.get("severity") == severity]
        
        return {
            "outdated_documents": outdated_docs,
            "total_outdated": len(outdated_docs),
            "total_documents": len(documents),
            "max_age_days": max_age_days,
            "checked_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error detecting outdated documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error detecting outdated documents: {str(e)}")


@router.post(
    "/maintenance/run",
    summary="运行维护任务",
    description="执行知识库维护任务",
    tags=["Maintenance"]
)
async def run_maintenance(
    tasks: Optional[List[str]] = Query(None, description="要执行的任务列表（quality, duplicates, outdated, health）")
) -> Dict[str, Any]:
    """运行维护任务"""
    try:
        # 获取所有文档
        all_docs = get_all_documents()
        
        # 转换为字典格式
        documents = []
        for doc in all_docs:
            documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "content": " ".join([chunk.content for chunk in doc.chunks]) if doc.chunks else "",
                "metadata": doc.metadata.dict() if doc.metadata else {},
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                "version": doc.version,
                "chunks": [chunk.dict() for chunk in doc.chunks] if doc.chunks else []
            })
        
        # 运行维护
        maintainer = get_knowledge_maintainer()
        report = maintainer.run_maintenance(documents, tasks=tasks)
        
        return report
    except Exception as e:
        logger.error(f"Error running maintenance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error running maintenance: {str(e)}")


@router.get(
    "/maintenance/health",
    summary="知识库健康度",
    description="获取知识库健康度评估",
    tags=["Maintenance"]
)
async def get_knowledge_base_health() -> Dict[str, Any]:
    """获取知识库健康度"""
    try:
        # 获取所有文档
        all_docs = get_all_documents()
        
        # 转换为字典格式
        documents = []
        for doc in all_docs:
            documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "content": " ".join([chunk.content for chunk in doc.chunks]) if doc.chunks else "",
                "metadata": doc.metadata.dict() if doc.metadata else {},
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                "version": doc.version,
                "chunks": [chunk.dict() for chunk in doc.chunks] if doc.chunks else []
            })
        
        # 运行维护（只检查健康度）
        maintainer = get_knowledge_maintainer()
        report = maintainer.run_maintenance(documents, tasks=["health", "quality", "duplicates", "outdated"])
        
        return {
            "health": report["tasks"].get("health", {}),
            "summary": report["summary"],
            "recommendations": report["recommendations"],
            "assessed_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error assessing knowledge base health: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error assessing knowledge base health: {str(e)}")


@router.get(
    "/maintenance/duplicates",
    summary="检测重复文档",
    description="检测知识库中的重复或相似文档",
    tags=["Maintenance"]
)
async def get_duplicate_documents(
    similarity_threshold: float = Query(0.95, description="相似度阈值（0-1）", ge=0.0, le=1.0),
    method: str = Query("embedding", description="检测方法（embedding, hash, content）")
) -> Dict[str, Any]:
    """检测重复文档"""
    try:
        # 获取所有文档
        all_docs = get_all_documents()
        
        # 转换为字典格式
        documents = []
        for doc in all_docs:
            documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "content": " ".join([chunk.content for chunk in doc.chunks]) if doc.chunks else "",
                "metadata": doc.metadata.dict() if doc.metadata else {}
            })
        
        # 检测重复
        detector = get_duplicate_detector(similarity_threshold=similarity_threshold)
        duplicate_groups = detector.detect_duplicates(documents, method=method)
        
        return {
            "duplicate_groups": duplicate_groups,
            "total_duplicates": sum(len(group["documents"]) for group in duplicate_groups),
            "total_groups": len(duplicate_groups),
            "similarity_threshold": similarity_threshold,
            "method": method,
            "checked_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error detecting duplicate documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error detecting duplicate documents: {str(e)}")

