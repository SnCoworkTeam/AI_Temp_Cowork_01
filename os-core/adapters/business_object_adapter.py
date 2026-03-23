"""
业务对象适配器
从PostgreSQL/元数据服务适配业务对象为统一资源
"""
from typing import List, Dict, Any, Optional
import logging

try:
    from ..resource_model import BusinessResource, ResourceType
    from ..resource_registry import ResourceRegistry
except ImportError:
    from resource_model import BusinessResource, ResourceType
    from resource_registry import ResourceRegistry

logger = logging.getLogger(__name__)


class BusinessObjectAdapter:
    """业务对象适配器"""
    
    def __init__(self, registry: ResourceRegistry):
        """
        初始化业务对象适配器
        
        Args:
            registry: 资源注册表
        """
        self.registry = registry
        logger.info("业务对象适配器初始化完成")
    
    def adapt_from_metadata(
        self,
        metadata: Dict[str, Any]
    ) -> BusinessResource:
        """
        从元数据服务的数据适配为业务资源
        
        Args:
            metadata: 元数据字典，包含业务对象信息
            
        Returns:
            BusinessResource: 业务资源对象
        """
        resource = BusinessResource(
            id=metadata.get("id", metadata.get("business_id", "")),
            name=metadata.get("name", metadata.get("business_name", "未知业务对象")),
            description=metadata.get("description", ""),
            uri=f"business://{metadata.get('id', 'unknown')}",
            business_id=metadata.get("business_id", metadata.get("id", "")),
            owner_department=metadata.get("owner_department", metadata.get("department", "")),
            lifecycle_state=metadata.get("lifecycle_state", metadata.get("status", "active")),
            business_metadata={
                "source": "metadata_service",
                "original_metadata": metadata
            },
            capabilities=self._extract_capabilities(metadata),
            access_control_rules=self._extract_access_control(metadata)
        )
        
        return resource
    
    def adapt_from_database(
        self,
        table_name: str,
        record: Dict[str, Any]
    ) -> BusinessResource:
        """
        从数据库记录适配为业务资源
        
        Args:
            table_name: 表名
            record: 数据库记录
            
        Returns:
            BusinessResource: 业务资源对象
        """
        # 根据表名推断业务对象类型
        business_type = self._infer_business_type(table_name)
        
        resource = BusinessResource(
            id=f"{table_name}:{record.get('id', 'unknown')}",
            name=record.get("name", record.get("title", f"{business_type}_{record.get('id', '')}")),
            description=record.get("description", ""),
            uri=f"db://{table_name}/{record.get('id', 'unknown')}",
            business_id=str(record.get("id", "")),
            owner_department=record.get("department", ""),
            lifecycle_state=record.get("status", "active"),
            business_metadata={
                "source": "database",
                "table_name": table_name,
                "business_type": business_type,
                "original_record": record
            },
            capabilities=["query", "analyze", "update"],
            access_control_rules={}
        )
        
        return resource
    
    def register_business_objects(
        self,
        objects: List[Dict[str, Any]],
        source: str = "metadata"
    ) -> int:
        """
        批量注册业务对象
        
        Args:
            objects: 业务对象列表
            source: 数据源类型（"metadata" | "database"）
            
        Returns:
            int: 成功注册的数量
        """
        registered_count = 0
        
        for obj in objects:
            try:
                if source == "metadata":
                    resource = self.adapt_from_metadata(obj)
                else:
                    # 假设是数据库记录
                    table_name = obj.get("_table", "unknown")
                    resource = self.adapt_from_database(table_name, obj)
                
                if self.registry.register(resource):
                    registered_count += 1
                    
            except Exception as e:
                logger.error(f"注册业务对象失败: {e}")
        
        logger.info(f"批量注册业务对象完成: {registered_count}/{len(objects)}")
        return registered_count
    
    def _extract_capabilities(self, metadata: Dict[str, Any]) -> List[str]:
        """从元数据中提取能力列表"""
        capabilities = ["query", "analyze"]
        
        # 根据业务对象类型添加特定能力
        business_type = metadata.get("business_type", "").lower()
        if "order" in business_type or "订单" in business_type:
            capabilities.extend(["create", "update", "cancel"])
        elif "contract" in business_type or "合同" in business_type:
            capabilities.extend(["create", "update", "approve"])
        
        return capabilities
    
    def _extract_access_control(self, metadata: Dict[str, Any]) -> Dict[str, List[str]]:
        """从元数据中提取访问控制规则"""
        # 默认访问控制规则
        rules = {}
        
        # 如果有访问控制配置，提取它
        if "access_control" in metadata:
            rules = metadata["access_control"]
        elif "permissions" in metadata:
            # 转换权限格式
            for operation, roles in metadata["permissions"].items():
                rules[operation] = roles
        
        return rules
    
    def _infer_business_type(self, table_name: str) -> str:
        """从表名推断业务对象类型"""
        table_lower = table_name.lower()
        
        if "order" in table_lower or "订单" in table_name:
            return "订单"
        elif "contract" in table_lower or "合同" in table_name:
            return "合同"
        elif "project" in table_lower or "项目" in table_name:
            return "项目"
        elif "customer" in table_lower or "客户" in table_name:
            return "客户"
        elif "supplier" in table_lower or "供应商" in table_name:
            return "供应商"
        else:
            return "业务对象"

