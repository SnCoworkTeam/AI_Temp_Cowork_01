"""
统一资源模型定义
采用Protocol接口 + 分层设计，避免过度抽象
"""
from enum import Enum
from typing import Protocol, Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


class ResourceType(Enum):
    """资源类型枚举"""
    BUSINESS_OBJECT = "business_object"      # 业务对象（订单、合同、项目等）
    SYSTEM_ENDPOINT = "system_endpoint"     # 系统端点（API、服务、Agent）
    KNOWLEDGE_ITEM = "knowledge_item"       # 知识项（文档、EA节点、规范）
    WORKFLOW = "workflow"                    # 工作流
    DATA_ENTITY = "data_entity"             # 数据实体（表、视图、字段）


class Resource(Protocol):
    """资源接口协议 - 定义统一接口"""
    id: str
    name: str
    description: str
    type: ResourceType
    uri: str  # 统一资源标识符
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取资源元数据"""
        ...
    
    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """执行资源操作"""
        ...
    
    def check_access(self, user: str, operation: str) -> bool:
        """检查访问权限"""
        ...
    
    def get_capabilities(self) -> List[str]:
        """获取资源支持的操作能力列表"""
        ...
    
    def get_relationships(self) -> Dict[str, List[str]]:
        """获取资源关联关系"""
        ...


@dataclass
class BaseResource:
    """资源基类 - 提供通用实现"""
    id: str
    name: str
    description: str
    type: ResourceType = ResourceType.BUSINESS_OBJECT  # 默认值，子类会覆盖
    uri: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取基础元数据"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "uri": self.uri,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def get_capabilities(self) -> List[str]:
        """默认能力列表"""
        return []
    
    def get_relationships(self) -> Dict[str, List[str]]:
        """默认关联关系"""
        return {}
    
    def check_access(self, user: str, operation: str) -> bool:
        """默认访问控制（子类应重写）"""
        return True


@dataclass
class BusinessResource(BaseResource):
    """业务资源专用实现"""
    business_id: str = ""
    owner_department: str = ""
    lifecycle_state: str = "active"
    business_metadata: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=lambda: ["query", "analyze", "update"])
    access_control_rules: Dict[str, List[str]] = field(default_factory=dict)  # {operation: [allowed_roles]}
    
    def __post_init__(self):
        """初始化后设置类型"""
        self.type = ResourceType.BUSINESS_OBJECT
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取业务资源元数据"""
        base_metadata = super().get_metadata()
        return {
            **base_metadata,
            "business_id": self.business_id,
            "owner_department": self.owner_department,
            "lifecycle_state": self.lifecycle_state,
            **self.business_metadata
        }
    
    def get_capabilities(self) -> List[str]:
        """获取业务资源能力"""
        return self.capabilities
    
    def check_access(self, user: str, operation: str) -> bool:
        """检查业务资源访问权限"""
        if operation not in self.access_control_rules:
            return True  # 默认允许
        
        # 这里应该查询用户的角色，简化实现
        # 实际应该从用户服务获取角色信息
        allowed_roles = self.access_control_rules.get(operation, [])
        if not allowed_roles:
            return True
        
        # TODO: 集成用户服务查询用户角色
        return True
    
    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """执行业务资源操作"""
        if action not in self.capabilities:
            raise ValueError(f"操作 {action} 不被支持")
        
        # 实际实现应该调用对应的业务服务
        return {"status": "success", "action": action, "resource_id": self.id}


@dataclass
class SystemEndpointResource(BaseResource):
    """系统端点资源"""
    endpoint_url: str = ""
    endpoint_type: str = "api"  # "api" | "service" | "agent" | "mcp"
    protocol: str = "http"  # "http" | "https" | "grpc" | "mcp"
    authentication_required: bool = True
    capabilities: List[str] = field(default_factory=lambda: ["invoke", "query"])
    service_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后设置类型"""
        self.type = ResourceType.SYSTEM_ENDPOINT
        if not self.uri:
            self.uri = f"{self.protocol}://{self.endpoint_url}"
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取系统端点元数据"""
        base_metadata = super().get_metadata()
        return {
            **base_metadata,
            "endpoint_url": self.endpoint_url,
            "endpoint_type": self.endpoint_type,
            "protocol": self.protocol,
            "authentication_required": self.authentication_required,
            **self.service_metadata
        }
    
    def get_capabilities(self) -> List[str]:
        """获取系统端点能力"""
        return self.capabilities
    
    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """执行系统端点调用"""
        if action not in self.capabilities:
            raise ValueError(f"操作 {action} 不被支持")
        
        # 实际实现应该调用对应的系统端点
        return {"status": "success", "action": action, "endpoint": self.endpoint_url}


@dataclass
class KnowledgeItemResource(BaseResource):
    """知识项资源"""
    content: str = ""
    content_type: str = "document"  # "document" | "ea_node" | "specification" | "knowledge_base"
    source: str = ""
    vector_id: Optional[str] = None  # 向量数据库中的ID
    knowledge_metadata: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=lambda: ["query", "search", "analyze"])
    
    def __post_init__(self):
        """初始化后设置类型"""
        self.type = ResourceType.KNOWLEDGE_ITEM
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取知识项元数据"""
        base_metadata = super().get_metadata()
        return {
            **base_metadata,
            "content_type": self.content_type,
            "source": self.source,
            "vector_id": self.vector_id,
            "content_length": len(self.content),
            **self.knowledge_metadata
        }
    
    def get_capabilities(self) -> List[str]:
        """获取知识项能力"""
        return self.capabilities
    
    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """执行知识项操作"""
        if action not in self.capabilities:
            raise ValueError(f"操作 {action} 不被支持")
        
        if action == "query":
            # 语义搜索
            return {"status": "success", "action": action, "results": []}
        elif action == "search":
            # 全文搜索
            return {"status": "success", "action": action, "results": []}
        else:
            return {"status": "success", "action": action}


@dataclass
class WorkflowResource(BaseResource):
    """工作流资源"""
    workflow_definition: Dict[str, Any] = field(default_factory=dict)
    workflow_type: str = "static"  # "static" | "dynamic"
    status: str = "active"  # "active" | "inactive" | "deprecated"
    execution_count: int = 0
    success_rate: float = 0.0
    capabilities: List[str] = field(default_factory=lambda: ["execute", "analyze", "optimize"])
    workflow_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后设置类型"""
        self.type = ResourceType.WORKFLOW
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取工作流元数据"""
        base_metadata = super().get_metadata()
        return {
            **base_metadata,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "execution_count": self.execution_count,
            "success_rate": self.success_rate,
            **self.workflow_metadata
        }
    
    def get_capabilities(self) -> List[str]:
        """获取工作流能力"""
        return self.capabilities
    
    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """执行工作流操作"""
        if action not in self.capabilities:
            raise ValueError(f"操作 {action} 不被支持")
        
        if action == "execute":
            # 实际应该调用工作流引擎
            return {"status": "success", "action": action, "workflow_id": self.id}
        else:
            return {"status": "success", "action": action}


@dataclass
class DataEntityResource(BaseResource):
    """数据实体资源"""
    entity_type: str = "table"  # "table" | "view" | "field" | "schema"
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    table_name: Optional[str] = None
    capabilities: List[str] = field(default_factory=lambda: ["query", "analyze", "export"])
    data_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后设置类型"""
        self.type = ResourceType.DATA_ENTITY
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取数据实体元数据"""
        base_metadata = super().get_metadata()
        return {
            **base_metadata,
            "entity_type": self.entity_type,
            "database_name": self.database_name,
            "schema_name": self.schema_name,
            "table_name": self.table_name,
            **self.data_metadata
        }
    
    def get_capabilities(self) -> List[str]:
        """获取数据实体能力"""
        return self.capabilities
    
    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """执行数据实体操作"""
        if action not in self.capabilities:
            raise ValueError(f"操作 {action} 不被支持")
        
        return {"status": "success", "action": action, "entity_id": self.id}
