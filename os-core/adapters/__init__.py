"""
资源适配器层
将现有服务/数据源适配为统一资源
"""

try:
    from .business_object_adapter import BusinessObjectAdapter
    from .system_endpoint_adapter import SystemEndpointAdapter
    from .knowledge_adapter import KnowledgeAdapter
    from .workflow_adapter import WorkflowAdapter
except ImportError:
    from business_object_adapter import BusinessObjectAdapter
    from system_endpoint_adapter import SystemEndpointAdapter
    from knowledge_adapter import KnowledgeAdapter
    from workflow_adapter import WorkflowAdapter

__all__ = [
    "BusinessObjectAdapter",
    "SystemEndpointAdapter",
    "KnowledgeAdapter",
    "WorkflowAdapter",
]

