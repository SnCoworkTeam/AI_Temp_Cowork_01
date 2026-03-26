# 基于SAP OData元数据的意图识别和交互式澄清分析

## 📋 执行摘要

本报告分析如何基于SAP OData元数据实现意图识别和交互式澄清功能，包括元数据扩展方案和系统代码修改方案。

## 🔍 当前SAP OData元数据结构

### 1. 现有元数据模型

#### 1.1 SAPDataAsset模型（sap-metadata-agent）
```python
class SAPDataAsset(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    asset_type: SAPAssetType
    odata_service: Optional[str] = None      # OData服务名
    odata_entity: Optional[str] = None      # OData实体名
    schema_info: Optional[Dict[str, Any]] = None  # Schema信息（包含properties和key）
    business_terms: List[str] = []          # 业务术语
    semantic_relationships: List[Dict] = [] # 语义关系
    metadata: Dict[str, Any] = {}          # 扩展元数据
```

#### 1.2 ODataEntity类型（sap-odata-to-mcp-server）
```typescript
interface ODataEntity {
  name: string;
  type: string;
  fullType: string;
  isCreatable: boolean;
  isUpdatable: boolean;
  isDeletable: boolean;
  sapLabel?: string;
  properties: EntityProperty[];  // 属性列表
  keys: string[];                // 主键
  navigationProperties?: NavigationProperty[];
}

interface EntityProperty {
  name: string;
  type: string;
  nullable?: boolean;
  maxLength?: number;
  sapLabel?: string;
  sapSemantics?: string;
}
```

#### 1.3 当前存储的Schema信息
```python
schema_info = {
    "properties": [
        {
            "name": "SalesOrder",
            "type": "Edm.String",
            "nullable": False,
            "maxLength": 10
        },
        # ...
    ],
    "key": ["SalesOrder"]  # 主键
}
```

## ❌ 缺失的元数据（用于意图识别和澄清）

### 1. 查询参数元数据 ❌

**缺失信息**:
- 哪些字段可以用于查询（$filter）
- 哪些字段是必需的查询条件
- 字段的查询操作符支持（eq, ne, gt, lt, contains等）
- 字段的数据类型和格式要求
- 字段的业务含义和示例值

**示例场景**:
- 用户说："查询销售订单"
- 系统需要知道：可以按订单号、客户、日期等查询
- 当前：没有这些信息

### 2. 查询能力元数据 ❌

**缺失信息**:
- 实体是否支持分页（$top, $skip）
- 是否支持排序（$orderby）
- 是否支持字段选择（$select）
- 是否支持扩展（$expand）
- 查询限制（最大返回数量等）

### 3. 业务语义元数据 ❌

**缺失信息**:
- 字段的业务含义（中文描述）
- 字段的常见查询模式
- 字段之间的关系（如：客户号 → 客户名称）
- 字段的枚举值或取值范围
- 字段的示例值

### 4. 意图模式元数据 ❌

**缺失信息**:
- 常见的用户查询意图模式
- 意图到参数的映射关系
- 参数组合规则（哪些参数可以组合使用）
- 参数优先级（哪些参数更重要）

## 🔧 元数据扩展方案

### 方案1: 扩展SAPDataAsset模型

#### 1.1 添加查询参数元数据

```python
class SAPDataAsset(BaseModel):
    # ... 现有字段 ...
    
    # 新增：查询参数元数据
    query_parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="查询参数元数据"
    )
    # 结构：
    # {
    #     "filterable_fields": [
    #         {
    #             "name": "SalesOrder",
    #             "type": "Edm.String",
    #             "required": False,
    #             "operators": ["eq", "ne", "contains"],
    #             "business_meaning": "销售订单号",
    #             "example_values": ["1234567890"],
    #             "searchable": True,
    #             "priority": "high"  # high, medium, low
    #         },
    #         {
    #             "name": "Customer",
    #             "type": "Edm.String",
    #             "required": False,
    #             "operators": ["eq", "ne"],
    #             "business_meaning": "客户编号",
    #             "example_values": ["C001"],
    #             "searchable": True,
    #             "priority": "medium"
    #         }
    #     ],
    #     "query_capabilities": {
    #         "supports_filter": True,
    #         "supports_select": True,
    #         "supports_orderby": True,
    #         "supports_top": True,
    #         "supports_skip": True,
    #         "max_top": 1000,
    #         "default_top": 100
    #     },
    #     "common_query_patterns": [
    #         {
    #             "pattern": "按订单号查询",
    #             "required_params": ["SalesOrder"],
    #             "example": "查询订单号为1234567890的销售订单"
    #         },
    #         {
    #             "pattern": "按客户查询",
    #             "required_params": ["Customer"],
    #             "optional_params": ["SalesOrderDate"],
    #             "example": "查询客户C001的销售订单"
    #         }
    #     ]
    # }
```

#### 1.2 添加意图模式元数据

```python
class SAPDataAsset(BaseModel):
    # ... 现有字段 ...
    
    # 新增：意图模式元数据
    intent_patterns: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="意图识别模式"
    )
    # 结构：
    # [
    #     {
    #         "intent_type": "query_by_id",
    #         "description": "按ID查询",
    #         "keywords": ["查询", "查", "获取", "找"],
    #         "required_parameters": ["SalesOrder"],
    #         "confidence_threshold": 0.8,
    #         "clarification_questions": [
    #             "请提供订单号",
    #             "您要查询哪个订单？"
    #         ]
    #     },
    #     {
    #         "intent_type": "query_by_customer",
    #         "description": "按客户查询",
    #         "keywords": ["客户", "客户的订单"],
    #         "required_parameters": ["Customer"],
    #         "optional_parameters": ["SalesOrderDate"],
    #         "confidence_threshold": 0.7,
    #         "clarification_questions": [
    #             "请提供客户编号或客户名称",
    #             "您要查询哪个客户的订单？"
    #         ]
    #     }
    # ]
```

#### 1.3 添加字段业务语义元数据

```python
class SAPDataAsset(BaseModel):
    # ... 现有字段 ...
    
    # 新增：字段业务语义
    field_semantics: Optional[Dict[str, Dict[str, Any]]] = Field(
        default_factory=dict,
        description="字段业务语义信息"
    )
    # 结构：
    # {
    #     "SalesOrder": {
    #         "business_meaning": "销售订单号",
    #         "business_terms": ["订单号", "订单编号", "SO号"],
    #         "data_type": "string",
    #         "format": "10位数字",
    #         "example_values": ["1234567890", "9876543210"],
    #         "validation_rules": {
    #             "pattern": "^[0-9]{10}$",
    #             "min_length": 10,
    #             "max_length": 10
    #         },
    #         "related_fields": ["Customer", "SalesOrderDate"],
    #         "query_priority": "high"
    #     },
    #     "Customer": {
    #         "business_meaning": "客户编号",
    #         "business_terms": ["客户", "客户号", "客户编号"],
    #         "data_type": "string",
    #         "example_values": ["C001", "C002"],
    #         "related_fields": ["CustomerName"],
    #         "query_priority": "high"
    #     }
    # }
```

### 方案2: 创建专门的查询元数据模型

```python
class ODataQueryMetadata(BaseModel):
    """OData查询元数据"""
    entity_name: str
    service_name: str
    
    # 可查询字段
    filterable_fields: List[FilterableField] = Field(default_factory=list)
    
    # 查询能力
    query_capabilities: QueryCapabilities
    
    # 意图模式
    intent_patterns: List[IntentPattern] = Field(default_factory=list)
    
    # 字段语义
    field_semantics: Dict[str, FieldSemantics] = Field(default_factory=dict)


class FilterableField(BaseModel):
    """可查询字段"""
    name: str
    type: str
    required: bool = False
    operators: List[str] = Field(default_factory=lambda: ["eq", "ne"])
    business_meaning: Optional[str] = None
    example_values: List[str] = Field(default_factory=list)
    searchable: bool = True
    priority: str = "medium"  # high, medium, low
    validation_rules: Optional[Dict[str, Any]] = None


class QueryCapabilities(BaseModel):
    """查询能力"""
    supports_filter: bool = True
    supports_select: bool = True
    supports_orderby: bool = True
    supports_top: bool = True
    supports_skip: bool = True
    max_top: Optional[int] = None
    default_top: int = 100


class IntentPattern(BaseModel):
    """意图模式"""
    intent_type: str
    description: str
    keywords: List[str] = Field(default_factory=list)
    required_parameters: List[str] = Field(default_factory=list)
    optional_parameters: List[str] = Field(default_factory=list)
    confidence_threshold: float = 0.7
    clarification_questions: List[str] = Field(default_factory=list)


class FieldSemantics(BaseModel):
    """字段语义"""
    business_meaning: str
    business_terms: List[str] = Field(default_factory=list)
    data_type: str
    format: Optional[str] = None
    example_values: List[str] = Field(default_factory=list)
    validation_rules: Optional[Dict[str, Any]] = None
    related_fields: List[str] = Field(default_factory=list)
    query_priority: str = "medium"
```

## 🔨 系统代码修改方案

### 修改1: 增强OData元数据发现

**文件**: `sap-metadata-agent/src/core/sap_data_asset_discoverer.py`

#### 1.1 增强_discover_from_odata方法

```python
async def _discover_from_odata(
    self, 
    limit: Optional[int] = None, 
    offset: int = 0
) -> List[SAPDataAsset]:
    """从OData服务发现数据资产（增强版）"""
    assets = []
    
    try:
        if not self.mcp_client:
            logger.warning("MCP client not available, skipping OData discovery")
            return assets
        
        # 获取OData服务列表
        services = await self.mcp_client.discover_services()
        
        # 处理服务（分批）
        services_to_process = services[offset:offset + limit] if limit else services[offset:]
        
        for service in services_to_process:
            service_name = service.get('name', '')
            service_id = service.get('id', '')
            
            # 获取服务的实体列表
            entities = await self.mcp_client.get_service_entities(service_id)
            
            for entity in entities:
                entity_name = entity.get('name', '')
                
                # 增强：获取实体的详细元数据
                entity_metadata = await self._get_enhanced_entity_metadata(
                    service_id, entity_name, entity
                )
                
                # 构建查询参数元数据
                query_metadata = self._build_query_metadata(entity_metadata)
                
                # 构建意图模式
                intent_patterns = self._build_intent_patterns(entity_metadata, query_metadata)
                
                # 构建字段语义
                field_semantics = self._build_field_semantics(entity_metadata)
                
                asset = SAPDataAsset(
                    name=f"sap_odata_{service_name.lower()}_{entity_name.lower()}",
                    display_name=f"{service_name} - {entity_name}",
                    description=f"SAP OData实体: {service_name}/{entity_name}",
                    asset_type=SAPAssetType.BUSINESS_OBJECT,
                    odata_service=service_name,
                    odata_entity=entity_name,
                    schema_info={
                        "properties": entity_metadata.get('properties', []),
                        "key": entity_metadata.get('keys', [])
                    },
                    # 新增：查询参数元数据
                    query_parameters=query_metadata,
                    # 新增：意图模式
                    intent_patterns=intent_patterns,
                    # 新增：字段语义
                    field_semantics=field_semantics,
                    tags=["SAP", "OData", "API", service_name, entity_name],
                    classification=self._classify_odata_entity(entity_name, service_name),
                    metadata={
                        "service_id": service_id,
                        "service_url": service.get('url'),
                        "discovery_method": "odata"
                    }
                )
                assets.append(asset)
    
    except Exception as e:
        logger.error(f"Error discovering assets from OData: {e}", exc_info=True)
    
    return assets


async def _get_enhanced_entity_metadata(
    self,
    service_id: str,
    entity_name: str,
    entity: Dict[str, Any]
) -> Dict[str, Any]:
    """获取增强的实体元数据"""
    try:
        # 从MCP客户端获取完整的实体元数据
        # 包括：属性、主键、导航属性、SAP标签等
        full_metadata = await self.mcp_client.get_entity_metadata(service_id, entity_name)
        
        return {
            "properties": full_metadata.get('properties', []),
            "keys": full_metadata.get('keys', []),
            "navigation_properties": full_metadata.get('navigation_properties', []),
            "sap_label": full_metadata.get('sap_label'),
            "is_creatable": full_metadata.get('isCreatable', False),
            "is_updatable": full_metadata.get('isUpdatable', False),
            "is_deletable": full_metadata.get('isDeletable', False)
        }
    except Exception as e:
        logger.warning(f"Failed to get enhanced metadata for {entity_name}: {e}")
        return entity


def _build_query_metadata(self, entity_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """构建查询参数元数据"""
    properties = entity_metadata.get('properties', [])
    keys = entity_metadata.get('keys', [])
    
    filterable_fields = []
    
    for prop in properties:
        prop_name = prop.get('name', '')
        prop_type = prop.get('type', '')
        
        # 判断是否可查询
        is_key = prop_name in keys
        is_string = 'String' in prop_type or 'Guid' in prop_type
        is_numeric = 'Int' in prop_type or 'Decimal' in prop_type or 'Double' in prop_type
        is_date = 'DateTime' in prop_type or 'Date' in prop_type
        
        # 确定支持的查询操作符
        operators = []
        if is_string:
            operators = ["eq", "ne", "contains", "startswith", "endswith"]
        elif is_numeric:
            operators = ["eq", "ne", "gt", "ge", "lt", "le"]
        elif is_date:
            operators = ["eq", "ne", "gt", "ge", "lt", "le"]
        else:
            operators = ["eq", "ne"]
        
        # 确定优先级
        priority = "high" if is_key else "medium"
        
        filterable_fields.append({
            "name": prop_name,
            "type": prop_type,
            "required": is_key,  # 主键通常是必需的
            "operators": operators,
            "business_meaning": prop.get('sapLabel') or prop_name,
            "example_values": [],
            "searchable": True,
            "priority": priority
        })
    
    return {
        "filterable_fields": filterable_fields,
        "query_capabilities": {
            "supports_filter": True,
            "supports_select": True,
            "supports_orderby": True,
            "supports_top": True,
            "supports_skip": True,
            "max_top": 1000,
            "default_top": 100
        },
        "common_query_patterns": self._build_common_patterns(filterable_fields, keys)
    }


def _build_common_patterns(
    self,
    filterable_fields: List[Dict],
    keys: List[str]
) -> List[Dict[str, Any]]:
    """构建常见查询模式"""
    patterns = []
    
    # 模式1: 按主键查询
    if keys:
        key_field = next((f for f in filterable_fields if f['name'] in keys), None)
        if key_field:
            patterns.append({
                "pattern": f"按{key_field['business_meaning']}查询",
                "required_params": keys,
                "example": f"查询{key_field['business_meaning']}为XXX的记录"
            })
    
    # 模式2: 按高优先级字段查询
    high_priority_fields = [f for f in filterable_fields if f['priority'] == 'high']
    if high_priority_fields:
        field_names = [f['name'] for f in high_priority_fields[:3]]  # 取前3个
        patterns.append({
            "pattern": "按关键字段查询",
            "required_params": field_names[:1],  # 至少需要一个
            "optional_params": field_names[1:],
            "example": f"查询{high_priority_fields[0]['business_meaning']}为XXX的记录"
        })
    
    return patterns


def _build_intent_patterns(
    self,
    entity_metadata: Dict[str, Any],
    query_metadata: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """构建意图模式"""
    patterns = []
    filterable_fields = query_metadata.get('filterable_fields', [])
    keys = entity_metadata.get('keys', [])
    
    # 模式1: 按ID查询
    if keys:
        key_field = next((f for f in filterable_fields if f['name'] in keys), None)
        if key_field:
            patterns.append({
                "intent_type": "query_by_id",
                "description": f"按{key_field['business_meaning']}查询",
                "keywords": ["查询", "查", "获取", "找", key_field['business_meaning']],
                "required_parameters": keys,
                "confidence_threshold": 0.8,
                "clarification_questions": [
                    f"请提供{key_field['business_meaning']}",
                    f"您要查询哪个{key_field['business_meaning']}？"
                ]
            })
    
    # 模式2: 按业务字段查询
    high_priority_fields = [f for f in filterable_fields if f['priority'] == 'high' and f['name'] not in keys]
    for field in high_priority_fields[:5]:  # 取前5个
        patterns.append({
            "intent_type": f"query_by_{field['name'].lower()}",
            "description": f"按{field['business_meaning']}查询",
            "keywords": [field['business_meaning'], field['name']],
            "required_parameters": [field['name']],
            "confidence_threshold": 0.7,
            "clarification_questions": [
                f"请提供{field['business_meaning']}",
                f"您要查询哪个{field['business_meaning']}？"
            ]
        })
    
    return patterns


def _build_field_semantics(
    self,
    entity_metadata: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """构建字段语义"""
    semantics = {}
    properties = entity_metadata.get('properties', [])
    
    for prop in properties:
        prop_name = prop.get('name', '')
        prop_type = prop.get('type', '')
        sap_label = prop.get('sapLabel', '')
        
        # 提取业务术语（从字段名和SAP标签）
        business_terms = []
        if sap_label:
            business_terms.append(sap_label)
        
        # 从字段名推断业务术语
        if 'Order' in prop_name:
            business_terms.extend(["订单", "订单号"])
        if 'Customer' in prop_name:
            business_terms.extend(["客户", "客户号"])
        if 'Date' in prop_name:
            business_terms.extend(["日期", "时间"])
        
        semantics[prop_name] = {
            "business_meaning": sap_label or prop_name,
            "business_terms": list(set(business_terms)),  # 去重
            "data_type": prop_type,
            "format": None,
            "example_values": [],
            "validation_rules": None,
            "related_fields": [],
            "query_priority": "high" if prop_name in entity_metadata.get('keys', []) else "medium"
        }
    
    return semantics
```

### 修改2: 创建意图验证器

**新文件**: `agent-service/src/core/intent_validator.py`

```python
"""
意图验证器
基于元数据验证用户意图的完整性和参数有效性
"""
import logging
from typing import Dict, Any, Optional, List
from ..core.conversation_agent import IntentAnalysis, TaskType

logger = logging.getLogger(__name__)


class ValidationResult:
    """验证结果"""
    def __init__(
        self,
        is_complete: bool,
        missing_parameters: List[str] = None,
        ambiguous_parameters: List[str] = None,
        clarification_questions: List[str] = None,
        confidence_threshold_met: bool = True,
        suggested_intents: List[Dict[str, Any]] = None
    ):
        self.is_complete = is_complete
        self.missing_parameters = missing_parameters or []
        self.ambiguous_parameters = ambiguous_parameters or []
        self.clarification_questions = clarification_questions or []
        self.confidence_threshold_met = confidence_threshold_met
        self.suggested_intents = suggested_intents or []


class IntentValidator:
    """意图验证器"""
    
    def __init__(self, metadata_client=None):
        """
        初始化意图验证器
        
        Args:
            metadata_client: 元数据服务客户端（可选）
        """
        self.metadata_client = metadata_client
        
        # 任务类型的必需参数定义
        self.required_params_by_task = {
            TaskType.TOOL_EXECUTION: {
                "sap_query": {
                    "required": ["entity_name"],  # 至少需要实体名
                    "optional": ["filters", "select", "top", "skip", "orderby"]
                },
                "general": {
                    "required": ["tool_name"]
                }
            },
            TaskType.KNOWLEDGE_SEARCH: {
                "required": ["query"]
            },
            TaskType.WORKFLOW_TASK: {
                "required": ["workflow_id"]
            }
        }
    
    async def validate_intent(
        self,
        intent_analysis: IntentAnalysis,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        验证意图分析结果
        
        Args:
            intent_analysis: 意图分析结果
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            验证结果
        """
        # 1. 检查置信度
        if intent_analysis.confidence < 0.7:
            return ValidationResult(
                is_complete=False,
                confidence_threshold_met=False,
                clarification_questions=[
                    "您的意图不够明确，请提供更多信息",
                    "您想要执行什么操作？"
                ]
            )
        
        # 2. 根据任务类型验证参数
        if intent_analysis.task_type == TaskType.TOOL_EXECUTION:
            return await self._validate_tool_execution_intent(
                intent_analysis, user_input, context
            )
        elif intent_analysis.task_type == TaskType.KNOWLEDGE_SEARCH:
            return await self._validate_knowledge_search_intent(
                intent_analysis, user_input, context
            )
        elif intent_analysis.task_type == TaskType.WORKFLOW_TASK:
            return await self._validate_workflow_intent(
                intent_analysis, user_input, context
            )
        
        # 其他任务类型默认通过
        return ValidationResult(is_complete=True)
    
    async def _validate_tool_execution_intent(
        self,
        intent_analysis: IntentAnalysis,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> ValidationResult:
        """验证工具执行意图"""
        required_tools = intent_analysis.required_tools
        extracted_params = intent_analysis.extracted_context.get("parameters", {})
        
        # 检查是否是SAP查询
        if "sap_query" in required_tools or any("sap" in tool.lower() for tool in required_tools):
            return await self._validate_sap_query_intent(
                intent_analysis, user_input, extracted_params, context
            )
        
        # 通用工具验证
        if not extracted_params.get("tool_name"):
            return ValidationResult(
                is_complete=False,
                missing_parameters=["tool_name"],
                clarification_questions=["请指定要使用的工具名称"]
            )
        
        return ValidationResult(is_complete=True)
    
    async def _validate_sap_query_intent(
        self,
        intent_analysis: IntentAnalysis,
        user_input: str,
        extracted_params: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> ValidationResult:
        """验证SAP查询意图（基于元数据）"""
        # 1. 从用户输入中提取实体名
        entity_name = extracted_params.get("entity_name")
        if not entity_name:
            # 尝试从required_tools或reasoning中提取
            # 或者从元数据服务搜索匹配的实体
            entity_name = await self._infer_entity_name(user_input, context)
        
        if not entity_name:
            return ValidationResult(
                is_complete=False,
                missing_parameters=["entity_name"],
                clarification_questions=[
                    "请指定要查询的SAP实体（如：销售订单、客户、物料等）",
                    "您想要查询什么数据？"
                ]
            )
        
        # 2. 从元数据服务获取实体的查询元数据
        entity_metadata = await self._get_entity_query_metadata(entity_name)
        if not entity_metadata:
            # 如果找不到元数据，至少需要实体名
            return ValidationResult(is_complete=True)
        
        # 3. 检查必需参数
        query_params = entity_metadata.get("query_parameters", {})
        filterable_fields = query_params.get("filterable_fields", [])
        
        # 检查是否有主键字段但没有提供值
        key_fields = [f for f in filterable_fields if f.get("required", False)]
        missing_keys = []
        for key_field in key_fields:
            field_name = key_field.get("name")
            if field_name not in extracted_params:
                missing_keys.append(field_name)
        
        if missing_keys:
            clarification_questions = []
            for key_field in key_fields:
                if key_field.get("name") in missing_keys:
                    business_meaning = key_field.get("business_meaning", key_field.get("name"))
                    clarification_questions.append(
                        f"请提供{business_meaning}（{key_field.get('name')}）"
                    )
            
            return ValidationResult(
                is_complete=False,
                missing_parameters=missing_keys,
                clarification_questions=clarification_questions
            )
        
        # 4. 检查是否有高优先级字段但没有提供值（可选，用于建议）
        high_priority_fields = [f for f in filterable_fields if f.get("priority") == "high"]
        suggested_params = []
        for field in high_priority_fields:
            if field.get("name") not in extracted_params:
                suggested_params.append({
                    "name": field.get("name"),
                    "business_meaning": field.get("business_meaning"),
                    "reason": "这是常用的查询字段"
                })
        
        if suggested_params and len(extracted_params) == 0:
            # 如果完全没有参数，建议提供一些
            questions = [
                f"您想要按什么条件查询？可以按{suggested_params[0]['business_meaning']}等条件查询"
            ]
            return ValidationResult(
                is_complete=False,
                missing_parameters=[s.get("name") for s in suggested_params],
                clarification_questions=questions
            )
        
        return ValidationResult(is_complete=True)
    
    async def _infer_entity_name(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """从用户输入推断实体名"""
        # 1. 从用户输入中提取关键词
        keywords = self._extract_keywords(user_input)
        
        # 2. 从元数据服务搜索匹配的实体
        if self.metadata_client:
            try:
                # 搜索包含关键词的数据资产
                assets = await self.metadata_client.search_data_assets(
                    keywords=keywords,
                    source_system="SAP",
                    asset_type="api"  # OData实体通常是API类型
                )
                
                if assets:
                    # 返回最匹配的实体的odata_entity
                    best_match = assets[0]
                    return best_match.get("metadata", {}).get("odata_entity")
            except Exception as e:
                logger.warning(f"Failed to search metadata for entity inference: {e}")
        
        return None
    
    def _extract_keywords(self, user_input: str) -> List[str]:
        """从用户输入提取关键词"""
        # 简单的关键词提取（可以增强）
        keywords = []
        
        # SAP常见实体关键词映射
        entity_keywords = {
            "销售订单": ["SalesOrder", "销售订单", "订单"],
            "客户": ["Customer", "客户"],
            "物料": ["Material", "物料", "产品"],
            "供应商": ["Vendor", "供应商"],
            "采购订单": ["PurchaseOrder", "采购订单"]
        }
        
        user_lower = user_input.lower()
        for keyword, entities in entity_keywords.items():
            if keyword in user_lower:
                keywords.extend(entities)
        
        return keywords
    
    async def _get_entity_query_metadata(
        self,
        entity_name: str
    ) -> Optional[Dict[str, Any]]:
        """从元数据服务获取实体的查询元数据"""
        if not self.metadata_client:
            return None
        
        try:
            # 搜索包含该实体的数据资产
            assets = await self.metadata_client.list_data_assets(
                limit=10,
                offset=0,
                source_system="SAP"
            )
            
            # 查找匹配的实体
            for asset in assets:
                metadata = asset.get("metadata", {})
                if metadata.get("odata_entity") == entity_name:
                    # 返回查询参数元数据
                    return {
                        "query_parameters": metadata.get("query_parameters", {}),
                        "intent_patterns": metadata.get("intent_patterns", []),
                        "field_semantics": metadata.get("field_semantics", {})
                    }
        except Exception as e:
            logger.warning(f"Failed to get entity query metadata: {e}")
        
        return None
    
    async def _validate_knowledge_search_intent(
        self,
        intent_analysis: IntentAnalysis,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> ValidationResult:
        """验证知识搜索意图"""
        extracted_params = intent_analysis.extracted_context.get("parameters", {})
        
        if not extracted_params.get("query") and len(user_input.strip()) < 3:
            return ValidationResult(
                is_complete=False,
                missing_parameters=["query"],
                clarification_questions=[
                    "请提供搜索关键词",
                    "您想要搜索什么内容？"
                ]
            )
        
        return ValidationResult(is_complete=True)
    
    async def _validate_workflow_intent(
        self,
        intent_analysis: IntentAnalysis,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> ValidationResult:
        """验证工作流意图"""
        extracted_params = intent_analysis.extracted_context.get("parameters", {})
        
        if not extracted_params.get("workflow_id"):
            return ValidationResult(
                is_complete=False,
                missing_parameters=["workflow_id"],
                clarification_questions=[
                    "请指定要执行的工作流ID或名称",
                    "您想要执行哪个工作流？"
                ]
            )
        
        return ValidationResult(is_complete=True)
```

### 修改3: 修改编排引擎以支持澄清

**文件**: `agent-service/src/core/orchestration_engine.py`

```python
async def orchestrate_request(
    self,
    user_input: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """编排请求（增强版：支持意图澄清）"""
    # 1. 意图分析
    intent_analysis = await self.conversation_agent.understand_conversation(
        user_input, 
        context.get('history'), 
        {k: v for k, v in context.items() if k not in ['history', 'available_agents']}
    )
    
    # 2. 意图验证（新增）
    from ..core.intent_validator import IntentValidator
    intent_validator = IntentValidator(metadata_client=self.metadata_client)
    validation_result = await intent_validator.validate_intent(
        intent_analysis, user_input, context
    )
    
    # 3. 如果需要澄清，返回澄清请求
    if not validation_result.is_complete:
        return {
            "requires_clarification": True,
            "clarification_questions": validation_result.clarification_questions,
            "missing_parameters": validation_result.missing_parameters,
            "ambiguous_parameters": validation_result.ambiguous_parameters,
            "partial_intent": {
                "task_type": intent_analysis.task_type.value,
                "confidence": intent_analysis.confidence,
                "extracted_context": intent_analysis.extracted_context
            },
            "suggested_intents": validation_result.suggested_intents
        }
    
    # 4. 继续正常流程
    # ... 现有代码 ...
```

### 修改4: 增强对话理解智能体

**文件**: `agent-service/src/core/conversation_agent.py`

```python
async def _analyze_with_llm(
    self,
    message: str,
    conversation_history: Optional[List[Dict[str, str]]],
    user_context: Optional[Dict[str, Any]],
    enhanced_system_prompt: Optional[str] = None
) -> IntentAnalysis:
    """使用LLM分析意图（增强版：检测缺失参数）"""
    # ... 现有代码 ...
    
    # 增强系统提示词，要求检测缺失参数
    system_prompt = """你是一个对话理解智能体，负责分析用户意图并提取关键信息。

重要：如果检测到用户意图不完整或缺少必需参数，请在返回JSON中添加：
{
    ...
    "requires_clarification": true,
    "missing_parameters": ["参数1", "参数2"],
    "clarification_questions": ["问题1", "问题2"]
}

任务类型和必需参数：
1. tool_execution (SAP查询):
   - 必需: entity_name (实体名，如：SalesOrder, Customer)
   - 可选: filters (查询条件), select (字段选择), top (数量限制)
   
2. knowledge_search:
   - 必需: query (搜索关键词)
   
3. workflow_task:
   - 必需: workflow_id (工作流ID或名称)

请分析用户消息，返回JSON格式：
{
    "task_type": "任务类型",
    "confidence": 0.0-1.0之间的置信度,
    "extracted_context": {
        "entities": ["实体1", "实体2"],
        "parameters": {"参数名": "参数值"},
        "intent": "用户意图描述"
    },
    "required_tools": ["需要的工具列表"],
    "required_services": ["需要的服务列表"],
    "requires_clarification": false,  // 是否需要澄清
    "missing_parameters": [],  // 缺失的参数列表
    "clarification_questions": [],  // 澄清问题列表
    "reasoning": "分析理由"
}"""
    
    # ... 调用LLM ...
    
    # 解析响应时处理澄清字段
    analysis_data = json.loads(response_text)
    
    intent_analysis = IntentAnalysis(
        task_type=TaskType(analysis_data.get("task_type", "unknown")),
        confidence=float(analysis_data.get("confidence", 0.5)),
        extracted_context=analysis_data.get("extracted_context", {}),
        required_tools=analysis_data.get("required_tools", []),
        required_services=analysis_data.get("required_services", []),
        reasoning=analysis_data.get("reasoning", "LLM analysis")
    )
    
    # 添加澄清信息（如果LLM检测到）
    if analysis_data.get("requires_clarification"):
        intent_analysis.requires_clarification = True
        intent_analysis.missing_parameters = analysis_data.get("missing_parameters", [])
        intent_analysis.clarification_questions = analysis_data.get("clarification_questions", [])
    
    return intent_analysis
```

### 修改5: 扩展IntentAnalysis模型

**文件**: `agent-service/src/core/conversation_agent.py`

```python
class IntentAnalysis:
    """意图分析结果（增强版）"""
    def __init__(
        self,
        task_type: TaskType,
        confidence: float,
        extracted_context: Dict[str, Any],
        required_tools: List[str],
        required_services: List[str],
        reasoning: str,
        requires_clarification: bool = False,  # 新增
        missing_parameters: List[str] = None,  # 新增
        clarification_questions: List[str] = None  # 新增
    ):
        self.task_type = task_type
        self.confidence = confidence
        self.extracted_context = extracted_context
        self.required_tools = required_tools
        self.required_services = required_services
        self.reasoning = reasoning
        # 新增字段
        self.requires_clarification = requires_clarification
        self.missing_parameters = missing_parameters or []
        self.clarification_questions = clarification_questions or []
```

## 📊 元数据扩展总结

### 需要扩展的元数据字段

| 字段 | 类型 | 说明 | 优先级 |
|------|------|------|--------|
| `query_parameters` | Dict | 查询参数元数据（filterable_fields, query_capabilities, common_query_patterns） | 高 |
| `intent_patterns` | List[Dict] | 意图识别模式（intent_type, keywords, required_parameters, clarification_questions） | 高 |
| `field_semantics` | Dict[str, Dict] | 字段业务语义（business_meaning, business_terms, example_values, validation_rules） | 中 |
| `query_capabilities` | Dict | 查询能力（supports_filter, supports_select, max_top等） | 中 |

### 元数据来源

1. **从OData XML元数据提取**:
   - EntityType的属性定义
   - Key字段定义
   - SAP标签（sap:label）
   - 数据类型和约束

2. **从业务规则推断**:
   - 主键字段通常是必需的
   - 字符串字段支持contains查询
   - 数值字段支持范围查询

3. **从使用模式学习**:
   - 记录常用查询模式
   - 分析参数组合频率
   - 优化意图识别模式

## 🔨 代码修改总结

### 需要修改的文件

1. **sap-metadata-agent/src/models/sap_metadata_models.py**
   - 扩展 `SAPDataAsset` 模型，添加查询元数据字段

2. **sap-metadata-agent/src/core/sap_data_asset_discoverer.py**
   - 增强 `_discover_from_odata` 方法
   - 添加 `_get_enhanced_entity_metadata` 方法
   - 添加 `_build_query_metadata` 方法
   - 添加 `_build_intent_patterns` 方法
   - 添加 `_build_field_semantics` 方法

3. **agent-service/src/core/intent_validator.py** (新建)
   - 创建意图验证器类
   - 实现参数完整性验证
   - 实现基于元数据的澄清问题生成

4. **agent-service/src/core/conversation_agent.py**
   - 扩展 `IntentAnalysis` 类
   - 增强系统提示词，要求检测缺失参数

5. **agent-service/src/core/orchestration_engine.py**
   - 在意图分析后添加验证步骤
   - 处理澄清请求并返回给用户

6. **metadata-service/src/models/data_asset.py**
   - 扩展 `DataAsset` 模型，支持新的元数据字段（如果使用数据库存储）

## 🎯 实施优先级

### 阶段1: 核心功能（高优先级）

1. **扩展SAPDataAsset模型** - 添加查询参数元数据字段
2. **增强OData元数据发现** - 提取和构建查询元数据
3. **创建意图验证器** - 实现参数验证逻辑
4. **修改编排引擎** - 集成验证和澄清流程

### 阶段2: 增强功能（中优先级）

5. **增强字段语义** - 提取业务术语和示例值
6. **构建意图模式** - 定义常见查询模式
7. **优化澄清问题** - 基于元数据生成更智能的问题

### 阶段3: 优化功能（低优先级）

8. **学习查询模式** - 从历史查询中学习
9. **智能参数推断** - 从上下文推断参数值
10. **多轮对话管理** - 支持多轮澄清对话

## 📝 实施建议

1. **先实现核心功能**：扩展元数据模型和基本的验证逻辑
2. **逐步增强**：先支持简单的参数验证，再添加复杂的意图模式匹配
3. **测试驱动**：为每个功能编写测试用例
4. **向后兼容**：确保新字段为可选，不影响现有功能


