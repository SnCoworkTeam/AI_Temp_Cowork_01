"""
知识图谱API路由
提供图谱数据获取接口，适配前端需求
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import httpx
import logging
from ..config import settings

router = APIRouter(prefix="/api/knowledge-graph", tags=["Knowledge Graph"])
logger = logging.getLogger(__name__)


def get_metadata_service_url() -> str:
    """获取metadata-service的URL"""
    use_localhost = settings.LOCAL_DEV or settings.USE_LOCALHOST
    if use_localhost:
        return "http://localhost:8005"
    else:
        return "http://metadata-service:8005"


@router.get("/graph", summary="获取知识图谱数据")
async def get_graph(
    limit: int = Query(100, ge=1, le=1000, description="节点数量限制"),
    node_type: Optional[str] = Query(None, description="节点类型过滤")
):
    """
    获取知识图谱数据，用于前端可视化
    
    返回格式：
    {
        "nodes": [...],
        "links": [...]
    }
    """
    try:
        base_url = get_metadata_service_url()
        
        # 构建查询参数
        nodes_params = f"limit={limit}"
        if node_type:
            nodes_params += f"&node_type={node_type}"
        
        # 边的limit：如果节点limit很大，使用固定的大值（1000）来获取所有边
        # 因为边数通常不会超过节点数的2倍，但数据库中有304条边
        edges_limit = min(limit * 2, 1000) if limit < 500 else 1000
        edges_params = f"limit={edges_limit}"
        
        # 调用metadata-service获取节点和边
        async with httpx.AsyncClient(timeout=10.0) as client:
            nodes_response = await client.get(f"{base_url}/api/knowledge-graph/nodes?{nodes_params}")
            edges_response = await client.get(f"{base_url}/api/knowledge-graph/edges?{edges_params}")
            
            nodes_data = nodes_response.json() if nodes_response.status_code == 200 else {"nodes": [], "count": 0}
            edges_data = edges_response.json() if edges_response.status_code == 200 else {"edges": [], "count": 0}
        
        # 提取节点和边
        nodes = nodes_data.get("nodes", []) if isinstance(nodes_data, dict) else []
        edges = edges_data.get("edges", []) if isinstance(edges_data, dict) else []
        
        # 节点类型中文映射
        node_type_map = {
            "sap_module": "SAP模块",
            "sap_sub_module": "SAP子模块",
            "concept": "概念",
            "entity": "实体",
            "agent": "智能体",
            "document": "文档",
            "knowledge_base": "知识库"
        }
        
        # 转换为前端需要的格式，优先使用中文display_name
        formatted_nodes = []
        for i, node in enumerate(nodes):
            properties = node.get("properties", {})
            # 优先使用display_name，其次使用label
            display_name = properties.get("display_name") or node.get("label") or str(node.get("id", f"Node {i}"))
            node_type = node.get("node_type", "unknown")
            
            # 确保ID是字符串格式
            node_id = str(node.get("id", str(i)))
            
            formatted_nodes.append({
                "id": node_id,
                "name": display_name,  # 使用中文名称
                "label": node.get("label", ""),  # 保留原始label
                "type": node_type,
                "type_cn": node_type_map.get(node_type, node_type),  # 中文类型
                "group": node_type,
                "properties": properties,
                "description": properties.get("description", "")
            })
        
        # 创建节点ID集合，用于快速查找（确保所有ID都是字符串）
        node_ids = {str(node["id"]) for node in formatted_nodes}
        
        # 只保留source和target都在节点列表中的边（确保边的ID也是字符串）
        formatted_links = []
        for edge in edges:
            source_id = str(edge.get("source_id", ""))
            target_id = str(edge.get("target_id", ""))
            
            if source_id in node_ids and target_id in node_ids:
                formatted_links.append({
                    "source": source_id,
                    "target": target_id,
                    "type": edge.get("relationship_type", "related"),
                    "properties": edge.get("properties", {})
                })
        
        return {
            "nodes": formatted_nodes,
            "links": formatted_links
        }
        
    except Exception as e:
        logger.error(f"Failed to get graph data: {e}", exc_info=True)
        # 返回空数据而不是抛出异常，让前端可以正常显示
        return {
            "nodes": [],
            "links": []
        }


@router.get("/entities", summary="获取实体列表")
async def get_entities(
    limit: int = Query(100, ge=1, le=1000),
    node_type: Optional[str] = Query(None)
):
    """获取实体列表"""
    try:
        base_url = get_metadata_service_url()
        params = f"limit={limit}"
        if node_type:
            params += f"&node_type={node_type}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/api/knowledge-graph/nodes?{params}")
            if response.status_code == 200:
                return response.json()
            return {"nodes": [], "count": 0}
    except Exception as e:
        logger.error(f"Failed to get entities: {e}", exc_info=True)
        return {"nodes": [], "count": 0}


@router.get("/relations", summary="获取关系列表")
async def get_relations(
    limit: int = Query(100, ge=1, le=1000),
    relationship_type: Optional[str] = Query(None)
):
    """获取关系列表"""
    try:
        base_url = get_metadata_service_url()
        params = f"limit={limit}"
        if relationship_type:
            params += f"&relationship_type={relationship_type}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/api/knowledge-graph/edges?{params}")
            if response.status_code == 200:
                return response.json()
            return {"edges": [], "count": 0}
    except Exception as e:
        logger.error(f"Failed to get relations: {e}", exc_info=True)
        return {"edges": [], "count": 0}


@router.get("/entities/{entity_id}", summary="获取实体详情")
async def get_entity(entity_id: str):
    """获取实体详情"""
    try:
        base_url = get_metadata_service_url()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/api/knowledge-graph/nodes/{entity_id}")
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=404, detail="Entity not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail="Entity not found")


@router.post("/query", summary="查询图谱")
async def query_graph(query: Dict[str, Any]):
    """
    查询图谱
    
    请求体：
    {
        "query": "搜索关键词"
    }
    """
    try:
        # 这里可以实现更复杂的查询逻辑
        # 目前简单返回空结果
        return {
            "nodes": [],
            "links": []
        }
    except Exception as e:
        logger.error(f"Failed to query graph: {e}", exc_info=True)
        return {
            "nodes": [],
            "links": []
        }

