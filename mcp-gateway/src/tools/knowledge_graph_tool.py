"""
知识图谱工具
提供知识图谱查询和扩展功能
"""
from typing import Dict, Any, List, Optional
import logging

from shared_libs.luminaos_common.common.http_client import HTTPClient
from ..config import settings
from ..models.tool_models import ToolDefinition, ToolType, ToolStatus

logger = logging.getLogger(__name__)

# 知识库服务URL
KNOWLEDGE_BASE_URL = getattr(settings, 'KNOWLEDGE_BASE_URL', 'http://knowledge-base:8004')


async def get_related_concepts(concept: str, limit: int = 10) -> Dict[str, Any]:
    """
    获取相关概念
    
    Args:
        concept: 概念名称
        limit: 返回结果数量限制
    
    Returns:
        相关概念列表
    """
    try:
        # 首先在知识图谱中查找概念节点
        async with HTTPClient(base_url=KNOWLEDGE_BASE_URL) as client:
            response = await client.get("/api/knowledge-graph", params={"limit": 100})
        
        nodes = response.get("nodes", [])
        edges = response.get("edges", [])
        
        # 查找匹配的节点
        matching_nodes = [
            node for node in nodes
            if concept.lower() in node.get("label", "").lower()
            or concept.lower() in node.get("id", "").lower()
        ]
        
        if not matching_nodes:
            return {
                "success": True,
                "concept": concept,
                "related_concepts": [],
                "message": f"No concepts found matching: {concept}"
            }
        
        # 查找相关节点（通过边连接）
        related_node_ids = set()
        for node in matching_nodes:
            node_id = node.get("id")
            # 查找与该节点连接的边
            for edge in edges:
                if edge.get("source") == node_id:
                    related_node_ids.add(edge.get("target"))
                elif edge.get("target") == node_id:
                    related_node_ids.add(edge.get("source"))
        
        # 获取相关节点
        related_nodes = [
            node for node in nodes
            if node.get("id") in related_node_ids
        ][:limit]
        
        # 获取连接边
        related_edges = [
            edge for edge in edges
            if edge.get("source") in [n.get("id") for n in matching_nodes]
            or edge.get("target") in [n.get("id") for n in matching_nodes]
        ]
        
        return {
            "success": True,
            "concept": concept,
            "matching_nodes": matching_nodes,
            "related_concepts": related_nodes,
            "relationships": related_edges,
            "total_related": len(related_nodes)
        }
    except Exception as e:
        logger.error(f"Error getting related concepts: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "concept": concept
        }


async def expand_knowledge_graph(seed_concepts: List[str], depth: int = 2) -> Dict[str, Any]:
    """
    扩展知识图谱
    
    Args:
        seed_concepts: 种子概念列表
        depth: 扩展深度
    
    Returns:
        扩展后的知识图谱片段
    """
    try:
        # 获取整个知识图谱
        async with HTTPClient(base_url=KNOWLEDGE_BASE_URL) as client:
            response = await client.get("/api/knowledge-graph", params={"limit": 1000})
        
        all_nodes = response.get("nodes", [])
        all_edges = response.get("edges", [])
        
        # 找到种子节点
        seed_node_ids = set()
        for concept in seed_concepts:
            matching = [
                node for node in all_nodes
                if concept.lower() in node.get("label", "").lower()
                or concept.lower() in node.get("id", "").lower()
            ]
            seed_node_ids.update([node.get("id") for node in matching])
        
        if not seed_node_ids:
            return {
                "success": True,
                "seed_concepts": seed_concepts,
                "expanded_nodes": [],
                "expanded_edges": [],
                "message": "No matching seed concepts found"
            }
        
        # 扩展图谱（BFS方式）
        expanded_node_ids = set(seed_node_ids)
        current_level = seed_node_ids
        
        for _ in range(depth):
            next_level = set()
            for node_id in current_level:
                # 查找连接的节点
                for edge in all_edges:
                    if edge.get("source") == node_id:
                        target_id = edge.get("target")
                        if target_id not in expanded_node_ids:
                            next_level.add(target_id)
                            expanded_node_ids.add(target_id)
                    elif edge.get("target") == node_id:
                        source_id = edge.get("source")
                        if source_id not in expanded_node_ids:
                            next_level.add(source_id)
                            expanded_node_ids.add(source_id)
            current_level = next_level
            if not current_level:
                break
        
        # 获取扩展后的节点和边
        expanded_nodes = [
            node for node in all_nodes
            if node.get("id") in expanded_node_ids
        ]
        
        expanded_edges = [
            edge for edge in all_edges
            if edge.get("source") in expanded_node_ids
            and edge.get("target") in expanded_node_ids
        ]
        
        return {
            "success": True,
            "seed_concepts": seed_concepts,
            "expanded_nodes": expanded_nodes,
            "expanded_edges": expanded_edges,
            "total_nodes": len(expanded_nodes),
            "total_edges": len(expanded_edges),
            "depth": depth
        }
    except Exception as e:
        logger.error(f"Error expanding knowledge graph: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "seed_concepts": seed_concepts
        }


async def execute_knowledge_graph(parameters: Dict[str, Any]) -> Any:
    """
    执行知识图谱工具
    
    Args:
        parameters: 工具参数
            - operation: 操作类型（get_related/expand）
            - concept: 概念名称（get_related时必需）
            - seed_concepts: 种子概念列表（expand时必需）
            - limit: 结果数量限制（get_related时可选）
            - depth: 扩展深度（expand时可选）
    
    Returns:
        操作结果
    """
    operation = parameters.get("operation", "get_related")
    
    if operation == "get_related":
        concept = parameters.get("concept")
        if not concept:
            raise ValueError("concept is required for get_related operation")
        
        limit = parameters.get("limit", 10)
        return await get_related_concepts(concept, limit=limit)
    
    elif operation == "expand":
        seed_concepts = parameters.get("seed_concepts")
        if not seed_concepts:
            raise ValueError("seed_concepts is required for expand operation")
        
        if isinstance(seed_concepts, str):
            seed_concepts = [c.strip() for c in seed_concepts.split(',') if c.strip()]
        
        depth = parameters.get("depth", 2)
        return await expand_knowledge_graph(seed_concepts, depth=depth)
    
    else:
        raise ValueError(f"Unsupported operation: {operation}. Supported operations: get_related, expand")


# 工具定义
KNOWLEDGE_GRAPH_TOOL = ToolDefinition(
    name="knowledge_graph",
    description="查询和扩展企业知识图谱，获取概念之间的关系和相关信息。",
    version="1.0.0",
    tool_type=ToolType.FUNCTION,
    status=ToolStatus.ACTIVE,
    parameters={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "操作类型",
                "enum": ["get_related", "expand"],
                "required": True
            },
            "concept": {
                "type": "string",
                "description": "概念名称（get_related时必需）",
                "required": False
            },
            "seed_concepts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "种子概念列表（expand时必需，可以是数组或逗号分隔的字符串）",
                "required": False
            },
            "limit": {
                "type": "integer",
                "description": "结果数量限制（get_related时可选）",
                "minimum": 1,
                "maximum": 50,
                "default": 10
            },
            "depth": {
                "type": "integer",
                "description": "扩展深度（expand时可选）",
                "minimum": 1,
                "maximum": 5,
                "default": 2
            }
        },
        "required": ["operation"]
    },
    required_parameters=["operation"],
    returns={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "concept": {"type": "string"},
            "related_concepts": {"type": "array"},
            "expanded_nodes": {"type": "array"},
            "expanded_edges": {"type": "array"},
            "relationships": {"type": "array"},
            "error": {"type": "string"}
        }
    },
    metadata={
        "category": "knowledge_base",
        "author": "system",
        "service": "knowledge-base"
    }
)

