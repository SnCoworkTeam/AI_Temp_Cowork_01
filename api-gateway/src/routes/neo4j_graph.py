"""
Neo4j图数据库API路由
提供Neo4j图数据的查询接口
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, Dict, Any, List
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/neo4j", tags=["Neo4j Graph"])


def get_metadata_service_url() -> str:
    """获取metadata-service的URL"""
    import os
    if os.getenv("ENVIRONMENT") == "development":
        return "http://localhost:8005"
    else:
        return "http://metadata-service:8005"


@router.get("/graph", summary="获取Neo4j图数据")
async def get_graph(
    limit: int = Query(500, ge=1, le=2000, description="节点数量限制"),
    nodeType: Optional[str] = Query(None, alias="node_type", description="节点类型过滤"),
    relationshipType: Optional[str] = Query(None, alias="relationship_type", description="关系类型过滤")
):
    """
    从Neo4j获取图数据，用于前端可视化
    
    返回格式：
    {
        "nodes": [...],
        "links": [...]
    }
    """
    try:
        base_url = get_metadata_service_url()
        
        # 调用metadata-service的Neo4j API
        params = {"limit": limit}
        if nodeType:
            params["node_type"] = nodeType
        if relationshipType:
            params["relationship_type"] = relationshipType
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/api/neo4j/graph", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get Neo4j graph: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get Neo4j graph data: {response.text}"
                )
    except httpx.TimeoutException:
        logger.error("Timeout while fetching Neo4j graph data")
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        logger.error(f"Error getting Neo4j graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes", summary="查询节点")
async def query_nodes(
    labels: Optional[str] = Query(None, description="节点标签（逗号分隔）"),
    limit: int = Query(100, ge=1, le=1000, description="结果数量限制")
):
    """查询Neo4j节点"""
    try:
        base_url = get_metadata_service_url()
        
        params = {"limit": limit}
        if labels:
            params["labels"] = labels
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/api/neo4j/nodes", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to query nodes: {response.text}"
                )
    except Exception as e:
        logger.error(f"Error querying nodes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}", summary="获取节点详情")
async def get_node_details(node_id: str):
    """获取节点详情"""
    try:
        base_url = get_metadata_service_url()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/api/neo4j/nodes/{node_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Node not found")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get node details: {response.text}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}/neighbors", summary="获取节点邻居")
async def get_node_neighbors(
    node_id: str,
    depth: int = Query(1, ge=1, le=5, description="遍历深度"),
    relationshipTypes: Optional[str] = Query(None, alias="relationship_types", description="关系类型过滤"),
    limit: int = Query(50, ge=1, le=200, description="结果数量限制")
):
    """获取节点的邻居节点"""
    try:
        base_url = get_metadata_service_url()
        
        params = {"depth": depth, "limit": limit}
        if relationshipTypes:
            params["relationship_types"] = relationshipTypes
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/api/neo4j/nodes/{node_id}/neighbors",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get neighbors: {response.text}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting neighbors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/search", summary="搜索节点")
async def search_nodes(
    q: str = Query(..., description="搜索查询"),
    limit: int = Query(20, ge=1, le=100, description="结果数量限制")
):
    """按名称或属性搜索节点"""
    try:
        base_url = get_metadata_service_url()
        
        params = {"q": q, "limit": limit}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/api/neo4j/nodes/search", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to search nodes: {response.text}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching nodes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationships", summary="查询关系")
async def query_relationships(
    types: Optional[str] = Query(None, description="关系类型（逗号分隔）"),
    limit: int = Query(100, ge=1, le=1000, description="结果数量限制")
):
    """查询Neo4j关系"""
    try:
        base_url = get_metadata_service_url()
        
        params = {"limit": limit}
        if types:
            params["types"] = types
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/api/neo4j/relationships", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to query relationships: {response.text}"
                )
    except Exception as e:
        logger.error(f"Error querying relationships: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cypher", summary="执行Cypher查询")
async def execute_cypher(request: Dict[str, Any]):
    """
    执行Cypher查询
    
    请求体：
    {
        "query": "MATCH (n) RETURN n LIMIT 10",
        "params": {}
    }
    """
    try:
        base_url = get_metadata_service_url()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{base_url}/api/neo4j/cypher", json=request)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to execute Cypher query: {response.text}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



