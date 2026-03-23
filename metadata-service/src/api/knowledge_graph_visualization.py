"""
知识图谱可视化API路由
提供图谱可视化所需的数据接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/knowledge-graph/viz", tags=["Knowledge Graph Visualization"])
logger = setup_logger(__name__)


def get_kg_repo(db: Session = Depends(get_db)) -> KnowledgeGraphRepository:
    """获取知识图谱Repository"""
    return KnowledgeGraphRepository(db)


@router.get("/graph-data", summary="获取图谱可视化数据")
async def get_graph_data(
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    max_nodes: int = Query(500, ge=1, le=2000, description="最大节点数"),
    max_edges: int = Query(1000, ge=1, le=5000, description="最大边数"),
    db: Session = Depends(get_db)
):
    """
    获取图谱可视化所需的数据
    
    返回格式适合前端可视化库（如D3.js、Cytoscape.js）使用
    """
    try:
        kg_repo = get_kg_repo(db)
        
        # 获取节点
        nodes = kg_repo.list_nodes(limit=max_nodes, node_type=node_type)
        
        # 获取边
        edges = kg_repo.list_edges(limit=max_edges)
        
        # 转换为可视化格式
        viz_nodes = []
        for node in nodes:
            viz_nodes.append({
                "id": str(node.id),
                "label": node.label,
                "type": node.node_type,
                "properties": node.properties or {},
                "group": node.node_type or "default"  # 用于分组
            })
        
        viz_edges = []
        for edge in edges:
            viz_edges.append({
                "id": str(edge.id),
                "source": str(edge.source_id),
                "target": str(edge.target_id),
                "type": edge.relationship_type,
                "properties": edge.properties or {}
            })
        
        return {
            "success": True,
            "nodes": viz_nodes,
            "edges": viz_edges,
            "stats": {
                "node_count": len(viz_nodes),
                "edge_count": len(viz_edges)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get graph data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subgraph-data/{node_id}", summary="获取子图可视化数据")
async def get_subgraph_data(
    node_id: str,
    max_depth: int = Query(2, ge=1, le=5, description="最大深度"),
    relationship_types: Optional[str] = Query(None, description="关系类型过滤，逗号分隔"),
    db: Session = Depends(get_db)
):
    """
    获取以指定节点为中心的子图可视化数据
    """
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
        
        # 转换为可视化格式
        viz_nodes = []
        for node in subgraph.get("nodes", []):
            viz_nodes.append({
                "id": node.get("id"),
                "label": node.get("label"),
                "type": node.get("node_type"),
                "properties": node.get("properties", {}),
                "group": node.get("node_type", "default")
            })
        
        viz_edges = []
        for edge in subgraph.get("edges", []):
            viz_edges.append({
                "id": edge.get("id"),
                "source": edge.get("source_id"),
                "target": edge.get("target_id"),
                "type": edge.get("relationship_type"),
                "properties": edge.get("properties", {})
            })
        
        return {
            "success": True,
            "center_node_id": node_id,
            "nodes": viz_nodes,
            "edges": viz_edges,
            "stats": {
                "node_count": len(viz_nodes),
                "edge_count": len(viz_edges),
                "max_depth": max_depth
            }
        }
    except Exception as e:
        logger.error(f"Failed to get subgraph data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/path-visualization", summary="获取路径可视化数据")
async def get_path_visualization(
    source_id: str = Body(..., description="源节点ID"),
    target_id: str = Body(..., description="目标节点ID"),
    max_depth: int = Body(5, ge=1, le=10, description="最大深度"),
    db: Session = Depends(get_db)
):
    """
    获取两个节点之间路径的可视化数据
    """
    try:
        kg_repo = get_kg_repo(db)
        
        # 查找路径
        paths = kg_repo.find_paths(
            source_id=source_id,
            target_id=target_id,
            max_depth=max_depth
        )
        
        if not paths:
            return {
                "success": True,
                "paths": [],
                "nodes": [],
                "edges": [],
                "message": "No paths found"
            }
        
        # 收集路径上的所有节点和边
        path_nodes = set()
        path_edges = []
        
        for path in paths:
            for i in range(len(path) - 1):
                path_nodes.add(path[i])
                path_nodes.add(path[i + 1])
                # 查找边
                edges = kg_repo.get_edges_by_node(path[i], direction="out")
                for edge in edges:
                    if str(edge.target_id) == path[i + 1]:
                        path_edges.append({
                            "id": str(edge.id),
                            "source": str(edge.source_id),
                            "target": str(edge.target_id),
                            "type": edge.relationship_type,
                            "properties": edge.properties or {}
                        })
        
        # 获取节点详情
        viz_nodes = []
        for node_id in path_nodes:
            node = kg_repo.get_node_by_id(node_id)
            if node:
                viz_nodes.append({
                    "id": str(node.id),
                    "label": node.label,
                    "type": node.node_type,
                    "properties": node.properties or {},
                    "group": node.node_type or "default"
                })
        
        return {
            "success": True,
            "source_id": source_id,
            "target_id": target_id,
            "paths": paths,
            "nodes": viz_nodes,
            "edges": path_edges,
            "stats": {
                "path_count": len(paths),
                "node_count": len(viz_nodes),
                "edge_count": len(path_edges)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get path visualization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", summary="导出图谱数据")
async def export_graph(
    format: str = Query("json", description="导出格式：json, csv, graphml"),
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    db: Session = Depends(get_db)
):
    """
    导出图谱数据
    
    支持格式：
    - json: JSON格式
    - csv: CSV格式（节点和边分别导出）
    - graphml: GraphML格式（用于Gephi等工具）
    """
    try:
        kg_repo = get_kg_repo(db)
        
        nodes = kg_repo.list_nodes(limit=10000, node_type=node_type)
        edges = kg_repo.list_edges(limit=10000)
        
        if format == "json":
            return {
                "success": True,
                "format": "json",
                "nodes": [
                    {
                        "id": str(node.id),
                        "label": node.label,
                        "type": node.node_type,
                        "properties": node.properties or {}
                    }
                    for node in nodes
                ],
                "edges": [
                    {
                        "id": str(edge.id),
                        "source": str(edge.source_id),
                        "target": str(edge.target_id),
                        "type": edge.relationship_type,
                        "properties": edge.properties or {}
                    }
                    for edge in edges
                ]
            }
        elif format == "csv":
            # CSV格式（简化实现）
            nodes_csv = "id,label,type\n"
            for node in nodes:
                nodes_csv += f"{node.id},{node.label},{node.node_type}\n"
            
            edges_csv = "id,source,target,type\n"
            for edge in edges:
                edges_csv += f"{edge.id},{edge.source_id},{edge.target_id},{edge.relationship_type}\n"
            
            return {
                "success": True,
                "format": "csv",
                "nodes_csv": nodes_csv,
                "edges_csv": edges_csv
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
    except Exception as e:
        logger.error(f"Failed to export graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




