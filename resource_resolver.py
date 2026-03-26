"""
资源解析器
将用户意图解析为资源操作
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

try:
    from .resource_model import Resource, ResourceType
    from .resource_registry import ResourceRegistry
    from .resource_operations import ResourceOperation, ResourceOperationType
except ImportError:
    from resource_model import Resource, ResourceType
    from resource_registry import ResourceRegistry
    from resource_operations import ResourceOperation, ResourceOperationType

logger = logging.getLogger(__name__)


@dataclass
class IntentResolutionResult:
    """意图解析结果"""
    objects: List[Resource]  # 涉及的业务对象
    systems: List[Resource]  # 涉及的系统端点
    knowledge: List[Resource]  # 涉及的知识项
    workflows: List[Resource]  # 涉及的工作流
    data_entities: List[Resource]  # 涉及的数据实体
    operations: List[ResourceOperation]  # 要执行的操作
    confidence: float  # 解析置信度


class ResourceResolver:
    """将用户意图解析为资源操作"""
    
    def __init__(self, registry: ResourceRegistry):
        """
        初始化资源解析器
        
        Args:
            registry: 资源注册表实例
        """
        self.registry = registry
        logger.info("资源解析器初始化完成")
    
    def resolve_intent_to_resources(
        self, 
        intent_result: Dict[str, Any]
    ) -> IntentResolutionResult:
        """
        解析意图到资源
        
        Args:
            intent_result: 统一意图识别结果（UnifiedIntentResult的字典形式）
            
        Returns:
            IntentResolutionResult: 解析后的资源结果
        """
        logger.debug(f"开始解析意图: {intent_result.get('base_intent', 'unknown')}")
        
        # 提取意图信息
        base_intent = intent_result.get("base_intent", "simple_chat")
        user_input = intent_result.get("user_input", "")
        suggested_activities = intent_result.get("suggested_activities", [])
        confidence = intent_result.get("confidence", 0.5)
        
        # 初始化结果
        result = IntentResolutionResult(
            objects=[],
            systems=[],
            knowledge=[],
            workflows=[],
            data_entities=[],
            operations=[],
            confidence=confidence
        )
        
        # 1. 从建议的活动解析业务对象
        result.objects = self._resolve_business_objects(suggested_activities, user_input)
        
        # 2. 解析系统端点
        result.systems = self._resolve_system_endpoints(suggested_activities, user_input)
        
        # 3. 解析知识项
        result.knowledge = self._resolve_knowledge_items(user_input, intent_result)
        
        # 4. 解析工作流
        result.workflows = self._resolve_workflows(base_intent, user_input)
        
        # 5. 解析数据实体
        result.data_entities = self._resolve_data_entities(user_input, intent_result)
        
        # 6. 生成资源操作
        result.operations = self._generate_operations(
            base_intent,
            result,
            intent_result
        )
        
        logger.info(
            f"意图解析完成: "
            f"业务对象={len(result.objects)}, "
            f"系统端点={len(result.systems)}, "
            f"知识项={len(result.knowledge)}, "
            f"工作流={len(result.workflows)}, "
            f"数据实体={len(result.data_entities)}, "
            f"操作={len(result.operations)}"
        )
        
        return result
    
    def _resolve_business_objects(
        self, 
        activities: List[Dict[str, Any]], 
        user_input: str
    ) -> List[Resource]:
        """解析业务对象"""
        objects = []
        
        # 从活动中提取业务对象关键词
        keywords = []
        for activity in activities:
            # 从业务域提取
            if "business_domain" in activity:
                keywords.append(activity["business_domain"])
            # 从活动名称提取
            if "name" in activity:
                activity_name = activity["name"]
                keywords.append(activity_name)
                # 提取活动名称中的关键词
                if "订单" in activity_name:
                    keywords.append("订单")
                if "采购" in activity_name:
                    keywords.append("采购")
        
        # 从用户输入提取业务对象关键词
        # 简单实现：查找常见的业务对象关键词
        business_keywords = ["订单", "合同", "项目", "客户", "供应商", "产品", "库存", "采购"]
        for keyword in business_keywords:
            if keyword in user_input:
                keywords.append(keyword)
        
        # 在注册表中查找匹配的业务对象
        if keywords:
            # 尝试多个查询策略
            queries = [
                " ".join(set(keywords)),  # 所有关键词
                keywords[0] if keywords else "",  # 第一个关键词
                user_input  # 用户输入本身
            ]
            
            for query in queries:
                if query:
                    objects = self.registry.discover(
                        query=query,
                        resource_type=ResourceType.BUSINESS_OBJECT,
                        limit=10
                    )
                    if objects:
                        break
        
        return objects
    
    def _resolve_system_endpoints(
        self, 
        activities: List[Dict[str, Any]], 
        user_input: str
    ) -> List[Resource]:
        """解析系统端点"""
        systems = []
        
        # 从活动中提取系统关键词
        keywords = []
        for activity in activities:
            # 查找能力单元，可能包含系统信息
            if "capability_id" in activity:
                capability_id = activity["capability_id"]
                keywords.append(capability_id)
                # 提取能力ID中的系统名（如"api:sap_create_po" -> "sap"）
                if ":" in capability_id:
                    parts = capability_id.split(":")
                    if len(parts) > 1:
                        keywords.append(parts[1].split("_")[0])  # 提取"sap"
        
        # 从用户输入提取系统关键词
        system_keywords = ["SAP", "API", "服务", "系统", "接口", "mcp", "endpoint"]
        for keyword in system_keywords:
            if keyword.lower() in user_input.lower():
                keywords.append(keyword)
        
        # 在注册表中查找匹配的系统端点
        if keywords:
            # 尝试多个查询策略
            queries = [
                " ".join(set(keywords)),  # 所有关键词
                keywords[0] if keywords else "",  # 第一个关键词
                user_input  # 用户输入本身
            ]
            
            for query in queries:
                if query:
                    systems = self.registry.discover(
                        query=query,
                        resource_type=ResourceType.SYSTEM_ENDPOINT,
                        limit=10
                    )
                    if systems:
                        break
        
        return systems
    
    def _resolve_knowledge_items(
        self, 
        user_input: str, 
        intent_result: Dict[str, Any]
    ) -> List[Resource]:
        """解析知识项"""
        knowledge = []
        
        # 从用户输入提取知识查询关键词
        knowledge_keywords = ["文档", "规范", "知识", "帮助", "说明", "如何", "查看", "文档"]
        has_knowledge_intent = any(kw in user_input for kw in knowledge_keywords)
        
        if has_knowledge_intent or intent_result.get("base_intent") == "knowledge_search":
            # 尝试多个查询策略
            queries = [
                user_input,  # 用户输入本身
                user_input.replace("如何", "").replace("？", "").replace("?", "").strip(),  # 移除疑问词
            ]
            
            for query in queries:
                if query:
                    knowledge = self.registry.discover(
                        query=query,
                        resource_type=ResourceType.KNOWLEDGE_ITEM,
                        limit=10
                    )
                    if knowledge:
                        break
        
        return knowledge
    
    def _resolve_workflows(
        self, 
        base_intent: str, 
        user_input: str
    ) -> List[Resource]:
        """解析工作流"""
        workflows = []
        
        # 如果意图是工作流相关
        if base_intent in ["workflow_task", "workflow_execution"]:
            # 从用户输入提取工作流关键词
            workflow_keywords = ["流程", "工作流", "自动化", "执行", "审批"]
            keywords = [kw for kw in workflow_keywords if kw in user_input]
            
            # 尝试多个查询策略
            queries = []
            if keywords:
                queries.append(" ".join(keywords))
            queries.append(user_input)  # 用户输入本身
            
            for query in queries:
                if query:
                    workflows = self.registry.discover(
                        query=query,
                        resource_type=ResourceType.WORKFLOW,
                        limit=5
                    )
                    if workflows:
                        break
        
        return workflows
    
    def _resolve_data_entities(
        self, 
        user_input: str, 
        intent_result: Dict[str, Any]
    ) -> List[Resource]:
        """解析数据实体"""
        entities = []
        
        # 从用户输入提取数据实体关键词
        data_keywords = ["表", "数据", "字段", "数据库", "查询", "分析"]
        has_data_intent = any(kw in user_input for kw in data_keywords)
        
        if has_data_intent:
            # 使用用户输入作为查询
            entities = self.registry.discover(
                query=user_input,
                resource_type=ResourceType.DATA_ENTITY,
                limit=10
            )
        
        return entities
    
    def _generate_operations(
        self,
        base_intent: str,
        resolution_result: IntentResolutionResult,
        intent_result: Dict[str, Any]
    ) -> List[ResourceOperation]:
        """生成资源操作"""
        operations = []
        
        # 根据意图类型生成操作
        if base_intent == "tool_execution":
            # 工具执行：为每个系统端点生成调用操作
            for system in resolution_result.systems:
                operations.append(ResourceOperation(
                    operation_type=ResourceOperationType.INVOKE,
                    resource_id=system.id,
                    resource_type=system.type.value,
                    action="invoke",
                    parameters=intent_result.get("extracted_entities", {}),
                    context={"intent": base_intent}
                ))
        
        elif base_intent == "knowledge_search":
            # 知识搜索：为每个知识项生成查询操作
            for knowledge in resolution_result.knowledge:
                operations.append(ResourceOperation(
                    operation_type=ResourceOperationType.SEARCH,
                    resource_id=knowledge.id,
                    resource_type=knowledge.type.value,
                    action="search",
                    parameters={"query": intent_result.get("user_input", "")},
                    context={"intent": base_intent}
                ))
        
        elif base_intent == "workflow_task":
            # 工作流任务：为每个工作流生成执行操作
            for workflow in resolution_result.workflows:
                operations.append(ResourceOperation(
                    operation_type=ResourceOperationType.EXECUTE,
                    resource_id=workflow.id,
                    resource_type=workflow.type.value,
                    action="execute",
                    parameters=intent_result.get("extracted_entities", {}),
                    context={"intent": base_intent}
                ))
        
        elif base_intent in ["query", "analyze"]:
            # 查询/分析：为业务对象生成查询操作
            for obj in resolution_result.objects:
                operations.append(ResourceOperation(
                    operation_type=ResourceOperationType.QUERY,
                    resource_id=obj.id,
                    resource_type=obj.type.value,
                    action=base_intent,
                    parameters=intent_result.get("extracted_entities", {}),
                    context={"intent": base_intent}
                ))
        
        return operations
    
    def _get_ea_relationships(self, resource: Resource) -> Dict[str, List[Resource]]:
        """
        从EA图谱获取资源关系（增强）
        
        Args:
            resource: 资源对象
            
        Returns:
            Dict: EA关系字典 {relation_type: [Resource]}
        """
        # 从资源元数据中提取EA实体ID
        metadata = resource.get_metadata()
        ea_entity_id = metadata.get("ea_entity_id") or metadata.get("ea_id")
        
        if not ea_entity_id:
            return {}
        
        # TODO: 调用EA知识图谱服务查询关系
        # 这里需要访问EA服务，可以通过依赖注入或服务发现
        # 简化实现：返回空字典
        logger.debug(f"资源 {resource.id} 有EA实体ID: {ea_entity_id}，但EA服务未集成")
        return {}
