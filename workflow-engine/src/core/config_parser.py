"""
工作流配置解析器
解析前端传来的JSON工作流配置，验证合法性，构建LangGraph图
"""
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field, validator
import logging
from collections import defaultdict

from ..models.workflow_models import WorkflowDefinition, WorkflowNode, WorkflowConnection

logger = logging.getLogger(__name__)


class WorkflowConfig(BaseModel):
    """工作流配置模型"""
    name: str = Field(..., description="工作流名称", min_length=1)
    description: str = Field(default="", description="工作流描述")
    version: str = Field(default="1.0.0", description="版本号")
    nodes: List[Dict[str, Any]] = Field(..., description="节点列表", min_items=1)
    connections: List[Dict[str, Any]] = Field(default_factory=list, description="连接线列表")
    start_node_id: str = Field(..., description="起始节点ID")
    end_node_ids: List[str] = Field(default_factory=list, description="结束节点ID列表")
    variables: Dict[str, Any] = Field(default_factory=dict, description="工作流变量")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @validator("nodes")
    def validate_nodes(cls, v):
        """验证节点配置"""
        if not v:
            raise ValueError("Workflow must have at least one node")
        
        node_ids = set()
        for node in v:
            node_id = node.get("id")
            if not node_id:
                raise ValueError("Each node must have an 'id' field")
            if node_id in node_ids:
                raise ValueError(f"Duplicate node id: {node_id}")
            node_ids.add(node_id)
        
        return v
    
    @validator("start_node_id")
    def validate_start_node(cls, v, values):
        """验证起始节点"""
        if "nodes" in values:
            node_ids = {node.get("id") for node in values["nodes"]}
            if v not in node_ids:
                raise ValueError(f"Start node '{v}' not found in nodes")
        return v
    
    @validator("connections")
    def validate_connections(cls, v, values):
        """验证连接线"""
        if "nodes" not in values:
            return v
        
        node_ids = {node.get("id") for node in values["nodes"]}
        
        for conn in v:
            source_id = conn.get("source", {}).get("node_id") if isinstance(conn.get("source"), dict) else conn.get("source")
            target_id = conn.get("target", {}).get("node_id") if isinstance(conn.get("target"), dict) else conn.get("target")
            
            if not source_id:
                raise ValueError("Connection must have source node_id")
            if not target_id:
                raise ValueError("Connection must have target node_id")
            
            if source_id not in node_ids:
                raise ValueError(f"Connection source node '{source_id}' not found")
            if target_id not in node_ids:
                raise ValueError(f"Connection target node '{target_id}' not found")
        
        return v


class WorkflowConfigParser:
    """工作流配置解析器"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def parse(self, config: Dict[str, Any]) -> WorkflowDefinition:
        """
        解析工作流配置
        
        Args:
            config: JSON配置字典
        
        Returns:
            WorkflowDefinition对象
        
        Raises:
            ValueError: 如果配置无效
        """
        self.errors.clear()
        self.warnings.clear()
        
        try:
            # 验证配置
            workflow_config = WorkflowConfig(**config)
        except Exception as e:
            raise ValueError(f"Invalid workflow config: {str(e)}")
        
        # 构建节点列表
        nodes = []
        for node_config in workflow_config.nodes:
            try:
                node = self._parse_node(node_config)
                nodes.append(node)
            except Exception as e:
                self.errors.append(f"Failed to parse node {node_config.get('id')}: {str(e)}")
                raise
        
        # 构建连接线列表
        connections = []
        for conn_config in workflow_config.connections:
            try:
                connection = self._parse_connection(conn_config)
                connections.append(connection)
            except Exception as e:
                self.warnings.append(f"Failed to parse connection: {str(e)}")
        
        # 验证工作流结构
        self._validate_workflow_structure(nodes, connections, workflow_config.start_node_id)
        
        if self.errors:
            raise ValueError(f"Workflow validation failed: {', '.join(self.errors)}")
        
        # 构建WorkflowDefinition
        workflow_def = WorkflowDefinition(
            name=workflow_config.name,
            description=workflow_config.description,
            version=workflow_config.version,
            nodes=nodes,
            connections=connections,
            start_node_id=workflow_config.start_node_id,
            end_node_ids=workflow_config.end_node_ids or self._find_end_nodes(nodes, connections),
            variables=workflow_config.variables,
            metadata=workflow_config.metadata
        )
        
        logger.info(f"Parsed workflow config: {workflow_config.name} ({len(nodes)} nodes, {len(connections)} connections)")
        
        return workflow_def
    
    def _parse_node(self, node_config: Dict[str, Any]) -> WorkflowNode:
        """解析单个节点配置"""
        from ..models.workflow_models import NodePosition, NodeSize
        
        node_id = node_config.get("id")
        node_type = node_config.get("type", "task")
        
        # 解析位置和大小
        position = None
        if "position" in node_config:
            pos_config = node_config["position"]
            position = NodePosition(x=pos_config.get("x", 0), y=pos_config.get("y", 0))
        
        size = None
        if "size" in node_config:
            size_config = node_config["size"]
            size = NodeSize(
                width=size_config.get("width", 200),
                height=size_config.get("height", 100)
            )
        
        return WorkflowNode(
            id=node_id,
            name=node_config.get("name", node_id),
            node_type=node_type,
            config=node_config.get("config", {}),
            inputs=node_config.get("inputs", []),
            outputs=node_config.get("outputs", []),
            next_nodes=node_config.get("next_nodes", []),
            condition=node_config.get("condition"),
            position=position,
            size=size,
            style=node_config.get("style", {}),
            label=node_config.get("label")
        )
    
    def _parse_connection(self, conn_config: Dict[str, Any]) -> WorkflowConnection:
        """解析连接线配置"""
        from ..models.workflow_models import ConnectionPoint
        
        # 处理不同格式的连接配置
        if isinstance(conn_config.get("source"), dict):
            source_point = ConnectionPoint(
                node_id=conn_config["source"].get("node_id"),
                port=conn_config["source"].get("port", "output")
            )
        else:
            source_point = ConnectionPoint(
                node_id=conn_config["source"],
                port="output"
            )
        
        if isinstance(conn_config.get("target"), dict):
            target_point = ConnectionPoint(
                node_id=conn_config["target"].get("node_id"),
                port=conn_config["target"].get("port", "input")
            )
        else:
            target_point = ConnectionPoint(
                node_id=conn_config["target"],
                port="input"
            )
        
        return WorkflowConnection(
            id=conn_config.get("id", f"{source_point.node_id}-{target_point.node_id}"),
            source=source_point,
            target=target_point,
            condition=conn_config.get("condition"),
            label=conn_config.get("label"),
            style=conn_config.get("style", {}),
            metadata=conn_config.get("metadata", {})
        )
    
    def _validate_workflow_structure(
        self,
        nodes: List[WorkflowNode],
        connections: List[WorkflowConnection],
        start_node_id: str
    ):
        """验证工作流结构"""
        node_ids = {node.id for node in nodes}
        
        # 检查起始节点
        if start_node_id not in node_ids:
            self.errors.append(f"Start node '{start_node_id}' not found")
        
        # 检查所有节点是否可达
        reachable_nodes = self._find_reachable_nodes(nodes, connections, start_node_id)
        unreachable_nodes = node_ids - reachable_nodes
        
        if unreachable_nodes:
            self.warnings.append(f"Unreachable nodes: {', '.join(unreachable_nodes)}")
        
        # 检查是否有循环依赖（简单检查）
        if self._has_cycle(nodes, connections):
            self.warnings.append("Workflow may have cycles")
    
    def _find_reachable_nodes(
        self,
        nodes: List[WorkflowNode],
        connections: List[WorkflowConnection],
        start_node_id: str
    ) -> Set[str]:
        """查找从起始节点可达的所有节点"""
        reachable = set()
        to_visit = [start_node_id]
        
        # 构建连接图
        graph = defaultdict(list)
        for conn in connections:
            graph[conn.source.node_id].append(conn.target.node_id)
        
        while to_visit:
            node_id = to_visit.pop()
            if node_id in reachable:
                continue
            
            reachable.add(node_id)
            to_visit.extend(graph[node_id])
        
        return reachable
    
    def _has_cycle(
        self,
        nodes: List[WorkflowNode],
        connections: List[WorkflowConnection]
    ) -> bool:
        """检查是否有循环（简单DFS实现）"""
        from collections import defaultdict
        
        graph = defaultdict(list)
        for conn in connections:
            graph[conn.source.node_id].append(conn.target.node_id)
        
        visited = set()
        rec_stack = set()
        
        def has_cycle_dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node in nodes:
            if node.id not in visited:
                if has_cycle_dfs(node.id):
                    return True
        
        return False
    
    def _find_end_nodes(
        self,
        nodes: List[WorkflowNode],
        connections: List[WorkflowConnection]
    ) -> List[str]:
        """查找结束节点（没有出边的节点）"""
        from collections import defaultdict
        
        has_outgoing = set()
        for conn in connections:
            has_outgoing.add(conn.source.node_id)
        
        end_nodes = [node.id for node in nodes if node.id not in has_outgoing]
        return end_nodes if end_nodes else [nodes[-1].id] if nodes else []









