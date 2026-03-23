"""
资源操作定义
"""
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class ResourceOperationType(Enum):
    """资源操作类型"""
    QUERY = "query"              # 查询
    ANALYZE = "analyze"          # 分析
    EXECUTE = "execute"          # 执行
    CREATE = "create"            # 创建
    UPDATE = "update"            # 更新
    DELETE = "delete"            # 删除
    INVOKE = "invoke"            # 调用
    SEARCH = "search"            # 搜索
    OPTIMIZE = "optimize"        # 优化
    EXPORT = "export"            # 导出


@dataclass
class ResourceOperation:
    """资源操作"""
    operation_type: ResourceOperationType
    resource_id: str
    resource_type: str
    action: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "operation_type": self.operation_type.value,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "action": self.action,
            "parameters": self.parameters,
            "context": self.context or {}
        }
