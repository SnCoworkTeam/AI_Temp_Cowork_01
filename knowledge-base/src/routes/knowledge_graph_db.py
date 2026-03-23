"""
知识图谱API路由（数据库集成版本）
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository
from ..dependencies.database import get_db
from luminaos_common.common.logger import setup_logger
from sqlalchemy.orm import Session


class CreateNodeRequest(BaseModel):
    """创建节点请求模型"""
    label: str
    node_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    document_id: Optional[str] = None


class CreateEdgeRequest(BaseModel):
    """创建边请求模型"""
    source_node_id: str
    target_node_id: str
    label: Optional[str] = None
    weight: float = 1.0
    properties: Optional[Dict[str, Any]] = None

router = APIRouter()
logger = setup_logger(__name__)


def get_knowledge_graph_repo(db: Session = Depends(get_db)) -> KnowledgeGraphRepository:
    """获取知识图谱Repository"""
    return KnowledgeGraphRepository(db)


@router.get(
    "/knowledge-graph",
    summary="获取知识图谱",
    description="获取知识图谱的节点和边（数据库集成版本）",
    tags=["Knowledge Graph"]
)
async def get_knowledge_graph(
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    document_id: Optional[str] = Query(None, description="文档ID过滤"),
    max_nodes: int = Query(100, ge=1, le=1000, description="最大节点数"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取知识图谱"""
    try:
        repo = get_knowledge_graph_repo(db)
        
        nodes = repo.list_nodes(
            skip=0,
            limit=max_nodes,
            node_type=node_type,
            document_id=document_id
        )
        
        # 获取所有相关边
        node_ids = [str(node.id) for node in nodes]
        all_edges = []
        for node_id in node_ids:
            edges = repo.get_edges_by_node(node_id, direction="both")
            for edge in edges:
                if str(edge.id) not in [e.get("id") for e in all_edges]:
                    all_edges.append({
                        "id": str(edge.id),
                        "source": str(edge.source_node_id),
                        "target": str(edge.target_node_id),
                        "label": edge.label,
                        "weight": edge.weight,
                        "properties": edge.properties or {}
                    })
        
        return {
            "nodes": [
                {
                    "id": str(node.id),
                    "label": node.label,
                    "type": node.node_type,
                    "properties": node.properties or {},
                    "document_id": str(node.document_id) if node.document_id else None
                }
                for node in nodes
            ],
            "edges": all_edges,
            "total_nodes": len(nodes),
            "total_edges": len(all_edges)
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge graph: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting knowledge graph: {str(e)}")


@router.get(
    "/knowledge-graph/stats",
    summary="获取知识图谱统计",
    description="获取知识图谱的统计信息",
    tags=["Knowledge Graph"]
)
async def get_knowledge_graph_stats(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取知识图谱统计"""
    try:
        repo = get_knowledge_graph_repo(db)
        stats = repo.get_graph_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting knowledge graph stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting knowledge graph stats: {str(e)}")


@router.get(
    "/knowledge-graph/nodes/{node_id}/related",
    summary="获取相关节点",
    description="获取指定节点的相关节点",
    tags=["Knowledge Graph"]
)
async def get_related_nodes(
    node_id: str = Path(..., description="节点ID"),
    max_depth: int = Query(1, ge=1, le=3, description="最大深度"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取相关节点"""
    try:
        repo = get_knowledge_graph_repo(db)
        
        related_nodes = repo.get_related_nodes(node_id, max_depth=max_depth)
        
        return {
            "node_id": node_id,
            "related_nodes": [
                {
                    "id": str(node.id),
                    "label": node.label,
                    "type": node.node_type,
                    "properties": node.properties or {}
                }
                for node in related_nodes
            ],
            "total": len(related_nodes),
            "max_depth": max_depth
        }
        
    except Exception as e:
        logger.error(f"Error getting related nodes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting related nodes: {str(e)}")


@router.post(
    "/knowledge-graph/nodes",
    summary="创建知识图谱节点",
    description="创建新的知识图谱节点",
    tags=["Knowledge Graph"]
)
async def create_node(
    request: CreateNodeRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """创建知识图谱节点"""
    try:
        repo = get_knowledge_graph_repo(db)
        
        node = repo.create_node(
            label=request.label,
            node_type=request.node_type,
            properties=request.properties,
            document_id=request.document_id
        )
        
        db.commit()
        
        return {
            "node_id": str(node.id),
            "label": node.label,
            "type": node.node_type,
            "properties": node.properties or {},
            "message": "Node created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating node: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating node: {str(e)}")


@router.post(
    "/knowledge-graph/edges",
    summary="创建知识图谱边",
    description="创建新的知识图谱边（关系）",
    tags=["Knowledge Graph"]
)
async def create_edge(
    request: CreateEdgeRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """创建知识图谱边"""
    try:
        repo = get_knowledge_graph_repo(db)
        
        edge = repo.create_edge(
            source_node_id=request.source_node_id,
            target_node_id=request.target_node_id,
            label=request.label,
            weight=request.weight,
            properties=request.properties
        )
        
        db.commit()
        
        return {
            "edge_id": str(edge.id),
            "source": str(edge.source_node_id),
            "target": str(edge.target_node_id),
            "label": edge.label,
            "weight": edge.weight,
            "message": "Edge created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating edge: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating edge: {str(e)}")







