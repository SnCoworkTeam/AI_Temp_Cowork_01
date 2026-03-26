"""
Neo4j图数据库API
提供Neo4j数据的查询接口
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, Dict, Any, List
from database.src.core.neo4j_client import Neo4jClient, get_neo4j_client
from database.src.core.session import get_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/neo4j", tags=["Neo4j"])


@router.get("/graph", summary="获取Neo4j图数据")
async def get_graph(
    limit: int = Query(500, ge=1, le=2000, description="节点数量限制"),
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    relationship_type: Optional[str] = Query(None, description="关系类型过滤")
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
        neo4j_client = get_neo4j_client()
        await neo4j_client.connect()
        
        try:
            # 策略：先查询关系，然后根据关系的节点来查询节点数据
            # 这样可以确保返回的节点都是有关系的节点
            
            # 第一步：查询关系
            # 如果指定了node_type，只查询涉及该类型节点的关系
            if node_type:
                if relationship_type:
                    rel_query = f"""
                    MATCH (a)-[r:{relationship_type}]->(b)
                    WHERE '{node_type}' IN labels(a) OR '{node_type}' IN labels(b)
                    RETURN id(a) AS source, id(b) AS target, type(r) AS type, r AS rel, labels(a) AS source_labels, labels(b) AS target_labels
                    LIMIT {limit * 2}
                    """
                else:
                    rel_query = f"""
                    MATCH (a)-[r]->(b)
                    WHERE '{node_type}' IN labels(a) OR '{node_type}' IN labels(b)
                    RETURN id(a) AS source, id(b) AS target, type(r) AS type, r AS rel, labels(a) AS source_labels, labels(b) AS target_labels
                    LIMIT {limit * 2}
                    """
            else:
                if relationship_type:
                    rel_query = f"""
                    MATCH (a)-[r:{relationship_type}]->(b)
                    RETURN id(a) AS source, id(b) AS target, type(r) AS type, r AS rel
                    LIMIT {limit * 2}
                    """
                else:
                    rel_query = f"""
                    MATCH (a)-[r]->(b)
                    RETURN id(a) AS source, id(b) AS target, type(r) AS type, r AS rel
                    LIMIT {limit * 2}
                    """
            
            rel_results = await neo4j_client.execute_query(rel_query)
            
            # 收集所有涉及到的节点ID
            all_node_ids = set()
            links = []
            seen_links = set()
            
            for record in rel_results:
                source_id = record.get("source")
                target_id = record.get("target")
                rel_type = record.get("type", "")
                
                if source_id is not None and target_id is not None:
                    all_node_ids.add(source_id)
                    all_node_ids.add(target_id)
                    
                    source_id_str = str(source_id)
                    target_id_str = str(target_id)
                    link_key = f"{source_id_str}-{target_id_str}-{rel_type}"
                    
                    if link_key not in seen_links:
                        seen_links.add(link_key)
                        
                        rel_data = record.get("rel", {})
                        if hasattr(rel_data, 'items'):
                            rel_properties = dict(rel_data)
                        elif isinstance(rel_data, dict):
                            rel_properties = rel_data
                        else:
                            rel_properties = {}
                        
                        links.append({
                            "id": link_key,
                            "source": source_id_str,
                            "target": target_id_str,
                            "type": rel_type,
                            "properties": rel_properties
                        })
            
            # 如果没有关系，则查询节点（但限制数量）
            if len(all_node_ids) == 0:
                if node_type:
                    node_query = f"MATCH (n:{node_type}) RETURN id(n) AS node_id, labels(n) AS labels, n LIMIT {limit}"
                else:
                    node_query = f"MATCH (n) RETURN id(n) AS node_id, labels(n) AS labels, n LIMIT {limit}"
                
                node_results = await neo4j_client.execute_query(node_query)
                
                nodes = []
                for record in node_results:
                    node_id = record.get("node_id")
                    if node_id is None:
                        continue
                    
                    node_id_str = str(node_id)
                    node_data = record.get("n", {})
                    labels = record.get("labels", [])
                    
                    if hasattr(node_data, 'items'):
                        properties = dict(node_data)
                    elif isinstance(node_data, dict):
                        properties = node_data
                    else:
                        properties = {}
                    
                    nodes.append({
                        "id": node_id_str,
                        "label": properties.get("label") or properties.get("name") or node_id_str,
                        "type": labels[0] if labels else "Entity",
                        "properties": properties
                    })
                
                return {"nodes": nodes, "links": []}
            
            # 第二步：根据节点ID查询节点数据
            # 如果节点太多，限制数量
            node_ids_list = list(all_node_ids)[:limit]
            
            if len(node_ids_list) == 0:
                return {"nodes": [], "links": []}
            
            # 构建节点查询（使用参数化查询）
            # 如果指定了node_type，仍然需要包含关系中的其他节点（否则关系无法显示）
            # 但可以优先显示指定类型的节点
            node_query = """
            MATCH (n)
            WHERE id(n) IN $node_ids
            RETURN id(n) AS node_id, labels(n) AS labels, n
            ORDER BY CASE WHEN $node_type IN labels(n) THEN 0 ELSE 1 END
            """
            
            node_results = await neo4j_client.execute_query(
                node_query, 
                {"node_ids": node_ids_list, "node_type": node_type or ""}
            )
            
            # 转换为前端格式
            nodes = []
            node_id_map = {}  # 用于快速查找
            
            for record in node_results:
                node_id = record.get("node_id")
                if node_id is None:
                    continue
                
                node_id_str = str(node_id)
                node_data = record.get("n", {})
                labels = record.get("labels", [])
                
                if hasattr(node_data, 'items'):
                    properties = dict(node_data)
                elif isinstance(node_data, dict):
                    properties = node_data
                else:
                    properties = {}
                
                node_info = {
                    "id": node_id_str,
                    "label": properties.get("label") or properties.get("name") or node_id_str,
                    "type": labels[0] if labels else "Entity",
                    "properties": properties
                }
                
                nodes.append(node_info)
                node_id_map[node_id] = node_info
            
            # 过滤关系：只保留节点已查询到的关系
            filtered_links = []
            for link in links:
                source_id = int(link["source"]) if link["source"].isdigit() else None
                target_id = int(link["target"]) if link["target"].isdigit() else None
                
                if source_id in node_id_map and target_id in node_id_map:
                    filtered_links.append(link)
            
            return {
                "nodes": nodes,
                "links": filtered_links
            }
            
            return {
                "nodes": nodes,
                "links": links
            }
        
        finally:
            await neo4j_client.disconnect()
    
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
        neo4j_client = get_neo4j_client()
        await neo4j_client.connect()
        
        try:
            if labels:
                label_list = [l.strip() for l in labels.split(",")]
                label_str = ":".join(label_list)
                query = f"MATCH (n:{label_str}) RETURN n LIMIT {limit}"
            else:
                query = f"MATCH (n) RETURN n LIMIT {limit}"
            
            results = await neo4j_client.execute_query(query)
            
            nodes = []
            for record in results:
                node_data = record.get("n", {})
                if not node_data:
                    continue
                
                node_id = str(node_data.get("id", ""))
                properties = dict(node_data) if hasattr(node_data, 'items') else {}
                labels_list = properties.pop("labels", []) if "labels" in properties else []
                
                nodes.append({
                    "id": node_id,
                    "labels": labels_list,
                    "properties": properties
                })
            
            return {"nodes": nodes, "count": len(nodes)}
        
        finally:
            await neo4j_client.disconnect()
    
    except Exception as e:
        logger.error(f"Error querying nodes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}", summary="获取节点详情")
async def get_node_details(node_id: str):
    """获取节点详情"""
    try:
        neo4j_client = get_neo4j_client()
        await neo4j_client.connect()
        
        try:
            query = f"MATCH (n) WHERE id(n) = $node_id RETURN n"
            results = await neo4j_client.execute_query(query, {"node_id": int(node_id)})
            
            if not results:
                raise HTTPException(status_code=404, detail="Node not found")
            
            node_data = results[0].get("n", {})
            properties = dict(node_data) if hasattr(node_data, 'items') else {}
            labels = properties.pop("labels", []) if "labels" in properties else []
            
            return {
                "id": node_id,
                "labels": labels,
                "properties": properties
            }
        
        finally:
            await neo4j_client.disconnect()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}/neighbors", summary="获取节点邻居")
async def get_node_neighbors(
    node_id: str,
    depth: int = Query(1, ge=1, le=5, description="遍历深度"),
    relationship_types: Optional[str] = Query(None, description="关系类型过滤"),
    limit: int = Query(50, ge=1, le=200, description="结果数量限制")
):
    """获取节点的邻居节点"""
    try:
        neo4j_client = get_neo4j_client()
        await neo4j_client.connect()
        
        try:
            if relationship_types:
                rel_types = [rt.strip() for rt in relationship_types.split(",")]
                rel_pattern = "|".join(rel_types)
                query = f"""
                MATCH path = (start)-[*1..{depth}:{rel_pattern}]-(neighbor)
                WHERE id(start) = $node_id
                RETURN DISTINCT neighbor, relationships(path) AS rels
                LIMIT {limit}
                """
            else:
                query = f"""
                MATCH path = (start)-[*1..{depth}]-(neighbor)
                WHERE id(start) = $node_id
                RETURN DISTINCT neighbor, relationships(path) AS rels
                LIMIT {limit}
                """
            
            results = await neo4j_client.execute_query(query, {"node_id": int(node_id)})
            
            nodes = []
            links = []
            node_ids = {node_id}
            
            for record in results:
                neighbor = record.get("neighbor", {})
                if not neighbor:
                    continue
                
                neighbor_id = str(neighbor.get("id", ""))
                if neighbor_id and neighbor_id not in node_ids:
                    node_ids.add(neighbor_id)
                    properties = dict(neighbor) if hasattr(neighbor, 'items') else {}
                    labels = properties.pop("labels", []) if "labels" in properties else []
                    
                    nodes.append({
                        "id": neighbor_id,
                        "label": properties.get("label") or properties.get("name") or neighbor_id,
                        "type": labels[0] if labels else "Entity",
                        "properties": properties
                    })
                
                # 添加关系
                rels = record.get("rels", [])
                for rel in rels:
                    if hasattr(rel, 'start_node') and hasattr(rel, 'end_node'):
                        source_id = str(rel.start_node.get("id", ""))
                        target_id = str(rel.end_node.get("id", ""))
                        rel_type = type(rel).__name__ if hasattr(type(rel), '__name__') else "RELATED_TO"
                        
                        if source_id and target_id:
                            links.append({
                                "id": f"{source_id}-{target_id}-{rel_type}",
                                "source": source_id,
                                "target": target_id,
                                "type": rel_type
                            })
            
            # 添加中心节点
            center_node = await get_node_details(node_id)
            if center_node:
                nodes.insert(0, {
                    "id": node_id,
                    "label": center_node.get("properties", {}).get("label") or center_node.get("properties", {}).get("name") or node_id,
                    "type": center_node.get("labels", [])[0] if center_node.get("labels") else "Entity",
                    "properties": center_node.get("properties", {})
                })
            
            return {
                "nodes": nodes,
                "links": links
            }
        
        finally:
            await neo4j_client.disconnect()
    
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
        neo4j_client = get_neo4j_client()
        await neo4j_client.connect()
        
        try:
            query = """
            MATCH (n)
            WHERE n.label CONTAINS $query 
               OR n.name CONTAINS $query
               OR toString(n.uuid) CONTAINS $query
            RETURN n
            LIMIT $limit
            """
            
            results = await neo4j_client.execute_query(query, {"query": q, "limit": limit})
            
            nodes = []
            for record in results:
                node_data = record.get("n", {})
                if not node_data:
                    continue
                
                node_id = str(node_data.get("id", ""))
                properties = dict(node_data) if hasattr(node_data, 'items') else {}
                labels = properties.pop("labels", []) if "labels" in properties else []
                
                nodes.append({
                    "id": node_id,
                    "labels": labels,
                    "properties": properties
                })
            
            return {"nodes": nodes, "count": len(nodes)}
        
        finally:
            await neo4j_client.disconnect()
    
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
        neo4j_client = get_neo4j_client()
        await neo4j_client.connect()
        
        try:
            if types:
                type_list = [t.strip() for t in types.split(",")]
                type_pattern = "|".join(type_list)
                query = f"MATCH ()-[r:{type_pattern}]->() RETURN r LIMIT {limit}"
            else:
                query = f"MATCH ()-[r]->() RETURN r LIMIT {limit}"
            
            results = await neo4j_client.execute_query(query)
            
            relationships = []
            for record in results:
                rel_data = record.get("r", {})
                if not rel_data:
                    continue
                
                rel_id = str(rel_data.get("id", ""))
                properties = dict(rel_data) if hasattr(rel_data, 'items') else {}
                rel_type = properties.pop("type", "RELATED_TO") if "type" in properties else "RELATED_TO"
                
                relationships.append({
                    "id": rel_id,
                    "type": rel_type,
                    "properties": properties
                })
            
            return {"relationships": relationships, "count": len(relationships)}
        
        finally:
            await neo4j_client.disconnect()
    
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
        query = request.get("query")
        params = request.get("params", {})
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        neo4j_client = get_neo4j_client()
        await neo4j_client.connect()
        
        try:
            results = await neo4j_client.execute_query(query, params)
            return {"results": results, "count": len(results)}
        
        finally:
            await neo4j_client.disconnect()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

