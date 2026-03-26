"""
工作流相关数据模型
集成共享库的模型定义，并扩展工作流设计器特定的模型
"""
import sys
import os
import importlib.util

# 确保 shared_libs 可以被导入（必须在导入 shared_libs 之前）
# 获取项目根目录（workflow-engine的父目录）
_current_file = os.path.abspath(__file__)
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_current_file)))
_shared_libs_path = os.path.join(_project_root, 'shared_libs')

# 添加shared_libs路径（支持Windows和Linux）
if _shared_libs_path not in sys.path:
    sys.path.insert(0, _shared_libs_path)
# 兼容Docker环境路径
for docker_path in ['/shared_libs', '/app/../shared_libs']:
    if os.path.exists(docker_path) and docker_path not in sys.path:
        sys.path.insert(0, docker_path)

from pydantic import BaseModel, Field, validator, model_validator, ConfigDict
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum

# 导入共享库的模型
from shared_libs.luminaos_common.schemas.workflow_schemas import (
    WorkflowStatus,
    ExecutionStatus,
    NodeType,
    WorkflowNode as BaseWorkflowNode,
    WorkflowDefinition as BaseWorkflowDefinition,
    WorkflowInfo as BaseWorkflowInfo,
    WorkflowExecutionRequest as BaseWorkflowExecutionRequest,
    WorkflowExecutionResponse as BaseWorkflowExecutionResponse,
    NodeExecutionResult
)


class NodePosition(BaseModel):
    """节点位置模型"""
    x: float = Field(..., description="X坐标", ge=0)
    y: float = Field(..., description="Y坐标", ge=0)


class NodeSize(BaseModel):
    """节点大小模型"""
    width: float = Field(default=200.0, description="宽度", ge=50)
    height: float = Field(default=100.0, description="高度", ge=50)


class WorkflowNode(BaseWorkflowNode):
    """工作流节点模型（扩展基础节点）"""
    description: Optional[str] = Field(None, description="节点描述")
    position: Optional[NodePosition] = Field(None, description="节点位置（用于UI）")
    size: Optional[NodeSize] = Field(None, description="节点大小（用于UI）")
    style: Dict[str, Any] = Field(default_factory=dict, description="节点样式（用于UI）")
    label: Optional[str] = Field(None, description="节点显示标签")
    type: Optional[str] = Field(None, description="节点类型（前端使用，映射到node_type）")

    @model_validator(mode='before')
    @classmethod
    def map_type_field(cls, values):
        """在验证前将type映射到node_type（Pydantic v2兼容）"""
        if isinstance(values, dict):
            # 如果前端发送了type但没有node_type，进行映射
            if 'type' in values and 'node_type' not in values:
                type_value = values['type']
                # 确保type值是字符串类型，并转换为NodeType枚举可接受的值
                if isinstance(type_value, str):
                    values['node_type'] = type_value
                else:
                    values['node_type'] = str(type_value)
            # 如果前端发送了node_type但没有type，也进行反向映射
            elif 'node_type' in values and 'type' not in values:
                node_type_value = values['node_type']
                # 如果node_type是枚举，获取其值
                if hasattr(node_type_value, 'value'):
                    values['type'] = node_type_value.value
                else:
                    values['type'] = str(node_type_value)
        return values


class ConnectionPoint(BaseModel):
    """连接点模型"""
    node_id: str = Field(..., description="节点ID")
    port: str = Field(default="output", description="端口名称", example="output")
    position: Optional[NodePosition] = Field(None, description="连接点位置")


class WorkflowConnection(BaseModel):
    """工作流连接线定义模型"""
    id: str = Field(..., description="连接线ID")
    source: ConnectionPoint = Field(..., description="源连接点")
    target: ConnectionPoint = Field(..., description="目标连接点")
    condition: Optional[str] = Field(None, description="连接条件（用于条件分支）")
    label: Optional[str] = Field(None, description="连接线标签")
    style: Dict[str, Any] = Field(default_factory=dict, description="连接线样式")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="连接线元数据")
    
    @validator("source", "target")
    def validate_connection_points(cls, v):
        """验证连接点"""
        if not v.node_id:
            raise ValueError("Connection point must have a node_id")
        return v


class WorkflowDefinition(BaseWorkflowDefinition):
    """工作流定义模型（扩展基础定义）"""
    nodes: List[WorkflowNode] = Field(..., description="工作流节点列表")
    connections: List[WorkflowConnection] = Field(
        default_factory=list,
        description="节点连接线列表"
    )
    canvas_size: Optional[Dict[str, float]] = Field(
        None,
        description="画布大小（用于UI）",
        example={"width": 1920, "height": 1080}
    )
    viewport: Optional[Dict[str, float]] = Field(
        None,
        description="视口位置和缩放（用于UI）",
        example={"x": 0, "y": 0, "zoom": 1.0}
    )
    # 覆盖基类的 start_node_id，使其可选（在验证时自动推断）
    start_node_id: Optional[str] = Field(None, description="起始节点ID（如果未提供将自动推断）")
    
    @validator("connections")
    def validate_connections(cls, v, values):
        """验证连接线是否有效"""
        if "nodes" not in values:
            return v
        
        node_ids = {node.id for node in values["nodes"]}
        
        for conn in v:
            if conn.source.node_id not in node_ids:
                raise ValueError(
                    f"Connection source node '{conn.source.node_id}' not found in nodes"
                )
            if conn.target.node_id not in node_ids:
                raise ValueError(
                    f"Connection target node '{conn.target.node_id}' not found in nodes"
                )
        
        return v
    
    @model_validator(mode='after')
    def validate_and_set_start_node(self):
        """验证并设置起始节点（如果未提供则自动推断）"""
        # 如果没有提供 start_node_id，自动推断
        if not self.start_node_id and self.nodes:
            # 查找类型为 "start" 的节点
            start_nodes = [
                node for node in self.nodes 
                if (node.node_type.value == "start" if hasattr(node.node_type, 'value') else str(node.node_type) == "start")
            ]
            if start_nodes:
                self.start_node_id = start_nodes[0].id
            else:
                # 如果没有 start 节点，使用第一个节点
                self.start_node_id = self.nodes[0].id
        
        # 验证起始节点是否存在
        if self.start_node_id:
            node_ids = {node.id for node in self.nodes}
            if self.start_node_id not in node_ids:
                raise ValueError(f"Start node '{self.start_node_id}' not found in nodes")
        
        return self


class WorkflowSaveRequest(BaseModel):
    """保存工作流请求模型"""
    workflow: WorkflowDefinition = Field(..., description="工作流定义")
    overwrite: bool = Field(default=False, description="是否覆盖已存在的工作流")


class WorkflowSaveResponse(BaseModel):
    """保存工作流响应模型"""
    success: bool = Field(..., description="保存是否成功")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: str = Field(..., description="工作流名称")
    message: str = Field(..., description="响应消息")
    saved_at: datetime = Field(default_factory=datetime.now, description="保存时间")
    version: str = Field(..., description="工作流版本")


class WorkflowDetailResponse(BaseModel):
    """工作流详情响应模型"""
    workflow: WorkflowDefinition = Field(..., description="工作流定义")
    workflow_id: str = Field(..., description="工作流ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    version: str = Field(..., description="工作流版本")
    execution_count: int = Field(default=0, ge=0, description="执行次数")
    last_executed_at: Optional[datetime] = Field(None, description="最后执行时间")


class WorkflowListResponse(BaseModel):
    """工作流列表响应模型"""
    workflows: List[Dict[str, Any]] = Field(..., description="工作流列表")
    total: int = Field(..., ge=0, description="工作流总数")
    page: int = Field(default=1, ge=1, description="当前页码")
    page_size: int = Field(default=20, ge=1, description="每页大小")


class WorkflowExecutionRequest(BaseWorkflowExecutionRequest):
    """工作流执行请求模型（继承共享库模型）"""
    # 覆盖基类的必需字段，使其可选（因为路径参数中已有 workflow_id）
    workflow_id: Optional[str] = Field(default=None, description="工作流ID（如果提供则优先使用，路径参数中已有时可为空）")
    workflow_name: Optional[str] = Field(default=None, description="工作流名称（如果workflow_id未提供）")
    # 覆盖 input_data，允许空字典
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据（允许空字典）")
    
    # Pydantic v2 配置：允许字段覆盖和额外字段
    model_config = ConfigDict(extra='allow')
    
    @model_validator(mode='before')
    @classmethod
    def make_fields_optional(cls, data):
        """在验证前将 workflow_name 设为可选（如果未提供）"""
        if isinstance(data, dict):
            # 如果 workflow_name 未提供，设为 None（而不是必需）
            if 'workflow_name' not in data:
                data['workflow_name'] = None
            # 如果 input_data 未提供，设为空字典
            if 'input_data' not in data:
                data['input_data'] = {}
        return data
    
    # 注意：移除了验证器，因为 workflow_id 在路径参数中已经提供了
    # 如果路径参数中有 workflow_id，请求体中的 workflow_id 和 workflow_name 都可以为空
    # 路由处理函数会将路径参数中的 workflow_id 设置到请求对象中


class WorkflowExecutionResponse(BaseWorkflowExecutionResponse):
    """工作流执行响应模型（继承共享库模型）"""
    workflow_id: Optional[str] = Field(None, description="工作流ID")
    workflow_name: str = Field(..., description="工作流名称")


class WorkflowDesignerMetadata(BaseModel):
    """工作流设计器元数据"""
    canvas_version: str = Field(default="1.0", description="画布版本")
    editor_version: str = Field(default="1.0", description="编辑器版本")
    last_edited_by: Optional[str] = Field(None, description="最后编辑者")
    last_edited_at: Optional[datetime] = Field(None, description="最后编辑时间")
    design_metadata: Dict[str, Any] = Field(default_factory=dict, description="设计元数据")
