"""
知识图谱查询API路由
提供图谱查询、路径查询、子图查询等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/knowledge-graph", tags=["Knowledge Graph"])
logger = setup_logger(__name__)


def get_kg_repo(db: Session = Depends(get_db)) -> KnowledgeGraphRepository:
    """获取知识图谱Repository"""
    return KnowledgeGraphRepository(db)


@router.get("/nodes", summary="查询节点")
async def get_nodes(
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    label_pattern: Optional[str] = Query(None, description="标签模式过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """查询知识图谱节点"""
    try:
        kg_repo = get_kg_repo(db)
        nodes = kg_repo.list_nodes(
            skip=skip,
            limit=limit,
            node_type=node_type,
            label_pattern=label_pattern
        )
        
        return {
            "success": True,
            "nodes": [
                {
                    "id": str(node.id),
                    "label": node.label,
                    "node_type": node.node_type,
                    "properties": node.properties or {}
                }
                for node in nodes
            ],
            "count": len(nodes)
        }
    except Exception as e:
        logger.error(f"Failed to get nodes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}", summary="获取节点详情")
async def get_node(
    node_id: str,
    db: Session = Depends(get_db)
):
    """获取节点详情，包括邻居节点"""
    try:
        kg_repo = get_kg_repo(db)
        node = kg_repo.get_node_by_id(node_id)
        
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # 获取邻居节点
        neighbors = kg_repo.get_neighbors(node_id, direction="both")
        
        return {
            "success": True,
            "node": {
                "id": str(node.id),
                "label": node.label,
                "node_type": node.node_type,
                "properties": node.properties or {}
            },
            "neighbors": [
                {
                    "id": str(n.id),
                    "label": n.label,
                    "node_type": n.node_type
                }
                for n in neighbors
            ],
            "neighbor_count": len(neighbors)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/paths", summary="查找路径")
async def find_paths(
    source_id: str = Body(..., description="源节点ID"),
    target_id: str = Body(..., description="目标节点ID"),
    max_depth: int = Body(3, ge=1, le=10, description="最大深度"),
    relationship_types: Optional[List[str]] = Body(None, description="关系类型过滤"),
    db: Session = Depends(get_db)
):
    """查找两个节点之间的路径"""
    try:
        kg_repo = get_kg_repo(db)
        paths = kg_repo.find_paths(
            source_id=source_id,
            target_id=target_id,
            max_depth=max_depth,
            relationship_types=relationship_types
        )
        
        return {
            "success": True,
            "paths": paths,
            "path_count": len(paths)
        }
    except Exception as e:
        logger.error(f"Failed to find paths: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subgraph/{node_id}", summary="获取子图")
async def get_subgraph(
    node_id: str,
    max_depth: int = Query(2, ge=1, le=5, description="最大深度"),
    relationship_types: Optional[str] = Query(None, description="关系类型过滤，逗号分隔"),
    db: Session = Depends(get_db)
):
    """获取以指定节点为中心的子图"""
    try:
        kg_repo = get_kg_repo(db)
        
        rel_types = None
        if relationship_types:
            rel_types = [t.strip() for t in relationship_types.split(",")]
        
        subgraph = kg_repo.get_subgraph(
            node_id=node_id,
            max_depth=max_depth,
            relationship_types=rel_types
        )
        
        return {
            "success": True,
            "subgraph": subgraph,
            "node_count": len(subgraph.get("nodes", [])),
            "edge_count": len(subgraph.get("edges", []))
        }
    except Exception as e:
        logger.error(f"Failed to get subgraph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/edges", summary="查询边")
async def get_edges(
    relationship_type: Optional[str] = Query(None, description="关系类型过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """查询知识图谱边"""
    try:
        kg_repo = get_kg_repo(db)
        edges = kg_repo.list_edges(
            skip=skip,
            limit=limit,
            relationship_type=relationship_type
        )
        
        return {
            "success": True,
            "edges": [
                {
                    "id": str(edge.id),
                    "source_id": str(edge.source_node_id),
                    "target_id": str(edge.target_node_id),
                    "relationship_type": edge.relationship_type,
                    "properties": edge.edge_metadata or {}
                }
                for edge in edges
            ],
            "count": len(edges)
        }
    except Exception as e:
        logger.error(f"Failed to get edges: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", summary="获取图谱统计信息")
async def get_statistics(
    db: Session = Depends(get_db)
):
    """获取知识图谱统计信息"""
    try:
        kg_repo = get_kg_repo(db)
        
        # 统计节点
        all_nodes = kg_repo.list_nodes(limit=10000)
        nodes_by_type = {}
        for node in all_nodes:
            node_type = node.node_type or "unknown"
            nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + 1
        
        # 统计边
        all_edges = kg_repo.list_edges(limit=10000)
        edges_by_type = {}
        for edge in all_edges:
            rel_type = edge.relationship_type or "unknown"
            edges_by_type[rel_type] = edges_by_type.get(rel_type, 0) + 1
        
        return {
            "success": True,
            "statistics": {
                "total_nodes": len(all_nodes),
                "total_edges": len(all_edges),
                "nodes_by_type": nodes_by_type,
                "edges_by_type": edges_by_type
            }
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="获取图谱统计信息（别名）")
async def get_stats(
    db: Session = Depends(get_db)
):
    """
    获取知识图谱统计信息（/stats别名，兼容性端点）
    
    此端点是/statistics的别名，用于兼容性
    """
    return await get_statistics(db)



