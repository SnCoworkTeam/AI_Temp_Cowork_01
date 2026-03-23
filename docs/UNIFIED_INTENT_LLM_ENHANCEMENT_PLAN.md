# 统一意图识别LLM增强方案

**方案版本**: v1.0  
**设计日期**: 2025-12-02  
**目标**: 将LLM作为统一意图识别的入口，增强意图识别能力，为后续企业语义引擎提供输入

---

## 📋 方案概述

### 核心目标

1. **LLM作为统一入口**: 使用DeepSeek LLM作为统一意图识别的第一层入口
2. **增强意图识别**: 提升复杂自然语言意图的理解能力
3. **为语义引擎提供输入**: LLM分析结果作为企业语义引擎的输入，优化向量搜索
4. **复杂意图识别**: 支持多步骤、多实体、上下文相关的复杂意图

### 设计原则

- ✅ **LLM优先**: LLM作为主要意图理解入口
- ✅ **多层融合**: LLM + 向量搜索 + 规则匹配
- ✅ **向后兼容**: 支持降级到现有实现
- ✅ **可配置**: 支持开关和参数配置
- ✅ **高性能**: 缓存机制和超时控制

---

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│              用户输入 (User Input)                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│          LLM意图理解层 (LLM Intent Understanding)        │
│  ┌─────────────────────────────────────────────────┐   │
│  │ DeepSeek LLM                                     │   │
│  │  - 语义理解                                       │   │
│  │  - 意图分类                                       │   │
│  │  - 实体提取                                       │   │
│  │  - 上下文分析                                     │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ LLM分析结果 (LLM Analysis Result)               │   │
│  │  - 意图类型                                       │   │
│  │  - 置信度                                         │   │
│  │  - 提取的实体                                     │   │
│  │  - 查询关键词                                     │   │
│  │  - 业务领域                                       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│      企业语义引擎层 (Enterprise Semantic Engine)         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 使用LLM结果优化查询                               │   │
│  │  - 业务领域过滤 (business_domain)                │   │
│  │  - 查询关键词增强 (enhanced_query)                │   │
│  │  - 向量搜索 (vector_search)                       │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 语义引擎结果 (Semantic Engine Result)            │   │
│  │  - 匹配的业务活动                                 │   │
│  │  - 相似度分数                                     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│          结果融合层 (Result Fusion)                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 融合LLM结果和语义引擎结果                         │   │
│  │  - 加权融合                                       │   │
│  │  - 置信度计算                                     │   │
│  │  - 执行建议生成                                   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│        统一意图结果 (Unified Intent Result)             │
└─────────────────────────────────────────────────────────┘
```

### 数据流设计

```
用户输入: "我需要采购一批原料，供应商是ABC公司，物料编号MAT001，数量100"
  ↓
[LLM层] DeepSeek分析
  ├── 意图类型: tool_execution
  ├── 业务领域: procurement
  ├── 提取实体:
  │   ├── 供应商: ABC公司
  │   ├── 物料: MAT001
  │   └── 数量: 100
  ├── 查询关键词: "采购订单 创建 供应商 物料"
  └── 置信度: 0.92
  ↓
[语义引擎层] 使用LLM结果优化查询
  ├── 业务领域过滤: business_domain = "procurement"
  ├── 查询关键词增强: "采购订单 创建 供应商 物料"
  ├── 向量搜索: 匹配相似活动
  └── 返回: activity:procurement:create_po (相似度: 0.88)
  ↓
[融合层] 融合结果
  ├── LLM置信度: 0.92 (权重: 0.6)
  ├── 向量相似度: 0.88 (权重: 0.4)
  ├── 综合置信度: 0.90
  └── 执行建议: component:sap:create_po
  ↓
[输出] UnifiedIntentResult
  ├── base_intent: "tool_execution"
  ├── confidence: 0.90
  ├── suggested_activities: [...]
  └── execution_suggestions: [...]
```

---

## 🔧 技术实现方案

### 1. LLM集成设计

#### 1.1 LLM客户端初始化

```python
# services/unified_intent_service.py

class UnifiedIntentService:
    def __init__(self):
        # ... 现有初始化代码 ...
        
        # ✅ 新增：LLM配置
        self.use_llm = os.getenv("UNIFIED_INTENT_USE_LLM", "true").lower() == "true"
        self.llm_model = os.getenv("LLM_MODEL", "deepseek-chat")
        self.llm_base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        self.llm_api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.llm_timeout = float(os.getenv("LLM_TIMEOUT", "10.0"))
        
        # 初始化LLM客户端
        if self.use_llm:
            self._init_llm()
    
    def _init_llm(self):
        """初始化DeepSeek LLM客户端"""
        try:
            from langchain_openai import ChatOpenAI
            
            llm_kwargs = {
                "model": self.llm_model,
                "temperature": self.llm_temperature,
                "api_key": self.llm_api_key,
                "timeout": self.llm_timeout,
            }
            
            # 处理base_url
            if self.llm_base_url:
                base_url_clean = self.llm_base_url.rstrip("/v1").rstrip("/")
                llm_kwargs["base_url"] = base_url_clean
            
            self.llm_client = ChatOpenAI(**llm_kwargs)
            logger.info(f"DeepSeek LLM客户端已初始化: model={self.llm_model}")
            
        except Exception as e:
            logger.warning(f"LLM初始化失败: {e}，将降级到规则匹配")
            self.use_llm = False
            self.llm_client = None
```

#### 1.2 LLM意图分析

```python
async def _analyze_intent_with_llm(
    self,
    user_input: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    使用DeepSeek LLM进行意图分析
    
    Returns:
        {
            "intent": "意图类型",
            "confidence": 0.0-1.0,
            "business_domain": "业务领域",
            "extracted_entities": {...},
            "query_keywords": ["关键词1", "关键词2"],
            "reasoning": "分析理由",
            "needs_semantic_search": True/False
        }
    """
    system_prompt = self._build_llm_system_prompt(context)
    
    user_prompt = f"""
    用户输入: {user_input}
    
    请分析用户意图，返回JSON格式：
    {{
        "intent": "意图类型（tool_execution/workflow_task/knowledge_search/simple_chat）",
        "confidence": 0.0-1.0,
        "business_domain": "业务领域（procurement/finance/warehouse等，如果不确定则为null）",
        "extracted_entities": {{
            "supplier": "供应商名称或代码",
            "material": "物料编号或名称",
            "quantity": "数量",
            "po_number": "采购订单号",
            "date": "日期",
            ...
        }},
        "query_keywords": ["关键词1", "关键词2", ...],
        "reasoning": "分析理由",
        "needs_semantic_search": true/false
    }}
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = await asyncio.wait_for(
            self.llm_client.ainvoke(messages),
            timeout=self.llm_timeout
        )
        
        # 解析LLM响应
        result = self._parse_llm_response(response.content)
        return result
        
    except asyncio.TimeoutError:
        logger.warning("LLM分析超时，降级到规则匹配")
        return self._analyze_intent_base(user_input)
    except Exception as e:
        logger.error(f"LLM分析失败: {e}，降级到规则匹配")
        return self._analyze_intent_base(user_input)
```

#### 1.3 LLM系统提示词设计

```python
def _build_llm_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
    """构建LLM系统提示词"""
    
    base_prompt = """
    你是一个企业意图理解助手，专门分析用户的业务意图。
    
    ## 意图类型
    
    1. **tool_execution** - 需要执行工具或调用API
       - 特征: 用户明确要求执行某个操作（创建、查询、更新、删除等）
       - 示例: "创建采购订单"、"查询销售订单"、"发送邮件"
    
    2. **workflow_task** - 工作流相关任务
       - 特征: 涉及多个步骤的流程或自动化任务
       - 示例: "创建一个审批流程"、"设计一个自动化工作流"
    
    3. **knowledge_search** - 知识库搜索
       - 特征: 用户想要查找信息、文档或知识
       - 示例: "查找采购流程文档"、"搜索SAP配置说明"
    
    4. **simple_chat** - 简单对话
       - 特征: 一般性问答，不需要执行操作
       - 示例: "你好"、"什么是采购订单"
    
    ## 业务领域识别
    
    根据用户输入识别业务领域：
    - **procurement**: 采购相关（采购订单、供应商、物料等）
    - **finance**: 财务相关（发票、付款、成本等）
    - **warehouse**: 仓储相关（库存、入库、出库等）
    - **sales**: 销售相关（销售订单、客户等）
    - **hr**: 人力资源相关（员工、考勤等）
    - 如果不确定，返回null
    
    ## 实体提取
    
    从用户输入中提取关键实体：
    - supplier: 供应商
    - material: 物料
    - quantity: 数量
    - po_number: 采购订单号
    - customer: 客户
    - order_number: 订单号
    - date: 日期
    - amount: 金额
    - ... (根据业务领域动态识别)
    
    ## 查询关键词生成
    
    生成3-5个关键词，用于后续的向量搜索：
    - 使用业务术语
    - 包含动作和对象
    - 示例: ["采购订单", "创建", "供应商", "物料"]
    
    ## 输出要求
    
    1. 必须返回有效的JSON格式
    2. confidence范围: 0.0-1.0
    3. 如果不确定，confidence应较低（<0.7）
    4. needs_semantic_search: 如果意图需要匹配业务活动，设为true
    """
    
    # 如果有上下文，添加到提示词
    if context:
        context_info = f"""
    ## 上下文信息
    
    {json.dumps(context, ensure_ascii=False, indent=2)}
    
    请结合上下文信息进行意图分析。
    """
        base_prompt += context_info
    
    return base_prompt
```

### 2. LLM与语义引擎协作设计

#### 2.1 优化语义引擎查询

```python
async def understand_intent(
    self,
    user_input: str,
    context: Optional[Dict[str, Any]] = None
) -> UnifiedIntentResult:
    """理解用户意图（统一入口 - LLM增强版）"""
    
    # 1. LLM意图分析（优先）
    if self.use_llm and self.llm_client:
        llm_result = await self._analyze_intent_with_llm(user_input, context)
    else:
        # 降级到规则匹配
        llm_result = self._analyze_intent_base(user_input)
        llm_result["needs_semantic_search"] = True
    
    # 2. 如果LLM建议进行语义搜索，查询企业语义引擎
    semantic_results = None
    if llm_result.get("needs_semantic_search", True):
        semantic_results = await self._query_semantic_engine_enhanced(
            user_input=user_input,
            llm_result=llm_result,  # ✅ 使用LLM结果优化查询
            context=context
        )
    
    # 3. 融合LLM结果和语义引擎结果
    merged_result = self._fuse_llm_and_semantic_results(
        llm_result=llm_result,
        semantic_results=semantic_results
    )
    
    # 4. 构建执行建议
    execution_suggestions = await self._build_execution_suggestions(
        merged_result.suggested_activities,
        llm_result.get("extracted_entities", {})  # ✅ 使用LLM提取的实体
    )
    
    # 5. 返回统一结果
    return UnifiedIntentResult(...)
```

#### 2.2 增强的语义引擎查询

```python
async def _query_semantic_engine_enhanced(
    self,
    user_input: str,
    llm_result: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> IntentQueryResult:
    """
    使用LLM结果增强的语义引擎查询
    
    Args:
        user_input: 原始用户输入
        llm_result: LLM分析结果
        context: 上下文信息
    """
    # 1. 构建增强的查询
    enhanced_query = self._build_enhanced_query(user_input, llm_result)
    
    # 2. 业务领域过滤（如果LLM识别了业务领域）
    business_domain = llm_result.get("business_domain")
    
    # 3. 查询语义引擎
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        self.semantic_engine.query_intent,
        enhanced_query,  # ✅ 使用增强的查询
        context,
        10,  # top_k
        0.5  # min_score
    )
    
    # 4. 如果指定了业务领域，进行二次过滤
    if business_domain and result.activities:
        filtered_activities = [
            act for act in result.activities
            if act.business_domain == business_domain
        ]
        result.activities = filtered_activities[:10]
    
    return result

def _build_enhanced_query(
    self,
    user_input: str,
    llm_result: Dict[str, Any]
) -> str:
    """
    构建增强的查询字符串
    
    策略:
    1. 如果LLM生成了query_keywords，优先使用
    2. 否则使用原始输入
    3. 可以结合实体信息
    """
    query_keywords = llm_result.get("query_keywords", [])
    
    if query_keywords:
        # 使用LLM生成的关键词
        enhanced_query = " ".join(query_keywords)
        logger.debug(f"使用LLM生成的关键词: {enhanced_query}")
        return enhanced_query
    else:
        # 使用原始输入
        return user_input
```

### 3. 结果融合设计

#### 3.1 融合策略

```python
def _fuse_llm_and_semantic_results(
    self,
    llm_result: Dict[str, Any],
    semantic_results: Optional[IntentQueryResult]
) -> Dict[str, Any]:
    """
    融合LLM结果和语义引擎结果
    
    融合策略:
    - LLM置信度权重: 0.6
    - 向量相似度权重: 0.4
    - 如果语义引擎有结果，提升综合置信度
    """
    # 基础信息来自LLM
    base_intent = llm_result.get("intent", "simple_chat")
    llm_confidence = llm_result.get("confidence", 0.5)
    
    # 语义引擎结果
    semantic_activities = []
    semantic_scores = []
    if semantic_results and semantic_results.activities:
        semantic_activities = semantic_results.activities
        semantic_scores = semantic_results.scores
    
    # 计算综合置信度
    if semantic_scores:
        # 有语义引擎结果，加权融合
        semantic_score = semantic_scores[0] if semantic_scores else 0.5
        fused_confidence = 0.6 * llm_confidence + 0.4 * semantic_score
    else:
        # 没有语义引擎结果，使用LLM置信度（降低）
        fused_confidence = llm_confidence * 0.8
    
    # 构建建议活动列表
    suggested_activities = []
    for activity, score in zip(semantic_activities, semantic_scores):
        suggested_activities.append({
            "id": activity.id,
            "name": activity.name,
            "description": activity.description,
            "activity_type": activity.activity_type,
            "business_domain": activity.business_domain,
            "similarity_score": score,
            "llm_boost": True  # 标记为LLM增强
        })
    
    return {
        "base_intent": base_intent,
        "confidence": fused_confidence,
        "suggested_activities": suggested_activities,
        "llm_result": llm_result,
        "semantic_results": semantic_results
    }
```

### 4. 复杂意图识别设计

#### 4.1 多步骤意图识别

```python
async def _analyze_complex_intent(
    self,
    user_input: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    复杂意图识别
    
    支持:
    - 多步骤任务识别
    - 多实体提取
    - 上下文关联
    """
    system_prompt = """
    你是一个复杂意图理解助手。
    
    请识别用户输入中的复杂意图：
    
    1. **多步骤任务**: 识别任务是否包含多个步骤
       - 示例: "先查询供应商信息，然后创建采购订单"
       - 返回: {"is_multi_step": true, "steps": [...]}
    
    2. **多实体关联**: 识别多个实体及其关系
       - 示例: "为供应商ABC创建采购订单，物料MAT001数量100"
       - 返回: {"entities": {...}, "relations": [...]}
    
    3. **上下文依赖**: 识别是否需要上下文信息
       - 示例: "查询刚才创建的订单"
       - 返回: {"needs_context": true, "context_keys": [...]}
    """
    
    # LLM分析
    # ...
```

#### 4.2 执行建议增强

```python
async def _build_execution_suggestions(
    self,
    suggested_activities: List[Dict[str, Any]],
    extracted_entities: Dict[str, Any] = None
) -> List[ExecutionSuggestion]:
    """
    构建执行建议（增强版）
    
    使用LLM提取的实体信息，自动填充参数
    """
    suggestions = []
    
    for activity in suggested_activities:
        # 获取能力单元
        capabilities = await self.get_capabilities_for_activity(activity["id"])
        
        for capability in capabilities:
            # ✅ 使用LLM提取的实体，自动填充参数
            input_schema = capability.get("input_schema", {})
            auto_filled_params = self._auto_fill_parameters(
                input_schema=input_schema,
                extracted_entities=extracted_entities
            )
            
            suggestion = ExecutionSuggestion(
                activity_id=activity["id"],
                activity_name=activity["name"],
                capability_id=capability["id"],
                capability_name=capability["name"],
                input_schema=input_schema,
                estimated_time=activity.get("estimated_time"),
                confidence=activity.get("similarity_score", 0.5),
                auto_filled_params=auto_filled_params  # ✅ 新增：自动填充的参数
            )
            suggestions.append(suggestion)
    
    return suggestions

def _auto_fill_parameters(
    self,
    input_schema: Dict[str, Any],
    extracted_entities: Dict[str, Any]
) -> Dict[str, Any]:
    """
    根据LLM提取的实体，自动填充参数
    
    映射规则:
    - supplier -> supplier_code
    - material -> material_code
    - quantity -> quantity
    - ...
    """
    auto_filled = {}
    
    # 实体映射表
    entity_mapping = {
        "supplier": ["supplier_code", "supplier", "vendor_code"],
        "material": ["material_code", "material", "item_code"],
        "quantity": ["quantity", "qty", "amount"],
        "po_number": ["po_number", "purchase_order_number"],
        "customer": ["customer_code", "customer"],
        "date": ["date", "delivery_date", "order_date"],
    }
    
    for entity_key, entity_value in extracted_entities.items():
        if entity_value:
            # 查找匹配的参数名
            param_names = entity_mapping.get(entity_key, [])
            for param_name in param_names:
                if param_name in input_schema:
                    auto_filled[param_name] = entity_value
                    break
    
    return auto_filled
```

---

## 📊 配置设计

### 环境变量配置

```bash
# LLM配置
UNIFIED_INTENT_USE_LLM=true                    # 是否使用LLM（默认true）
LLM_MODEL=deepseek-chat                        # LLM模型
LLM_BASE_URL=https://api.deepseek.com          # LLM API地址
DEEPSEEK_API_KEY=your_api_key                  # DeepSeek API密钥
LLM_TEMPERATURE=0.3                            # LLM温度参数
LLM_TIMEOUT=10.0                               # LLM超时时间（秒）

# 融合权重配置
LLM_CONFIDENCE_WEIGHT=0.6                      # LLM置信度权重
SEMANTIC_SCORE_WEIGHT=0.4                      # 向量相似度权重

# 缓存配置
LLM_CACHE_ENABLED=true                         # 是否启用LLM结果缓存
LLM_CACHE_TTL=3600                             # 缓存TTL（秒）

# 降级配置
LLM_FALLBACK_TO_RULES=true                     # LLM失败时降级到规则匹配
```

### 配置类设计

```python
from pydantic import BaseSettings

class UnifiedIntentLLMConfig(BaseSettings):
    """统一意图识别LLM配置"""
    
    # LLM基础配置
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: Optional[str] = None
    llm_temperature: float = 0.3
    llm_timeout: float = 10.0
    
    # 融合权重
    llm_confidence_weight: float = 0.6
    semantic_score_weight: float = 0.4
    
    # 缓存配置
    llm_cache_enabled: bool = True
    llm_cache_ttl: int = 3600
    
    # 降级配置
    fallback_to_rules: bool = True
    
    class Config:
        env_prefix = "UNIFIED_INTENT_"
```

---

## 🔄 降级策略

### 降级流程

```
LLM分析
  ↓ (成功)
使用LLM结果
  ↓ (失败/超时)
降级到规则匹配
  ↓ (成功)
使用规则匹配结果
  ↓ (失败)
返回默认结果
```

### 降级实现

```python
async def _analyze_intent_with_fallback(
    self,
    user_input: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """带降级的意图分析"""
    
    # 1. 尝试LLM分析
    if self.use_llm and self.llm_client:
        try:
            result = await asyncio.wait_for(
                self._analyze_intent_with_llm(user_input, context),
                timeout=self.llm_timeout
            )
            if result.get("confidence", 0) > 0.5:
                return result
        except Exception as e:
            logger.warning(f"LLM分析失败: {e}，降级到规则匹配")
    
    # 2. 降级到规则匹配
    if self.fallback_to_rules:
        return self._analyze_intent_base(user_input)
    
    # 3. 返回默认结果
    return {
        "intent": "simple_chat",
        "confidence": 0.3,
        "business_domain": None,
        "extracted_entities": {},
        "query_keywords": [],
        "reasoning": "降级到默认结果",
        "needs_semantic_search": False
    }
```

---

## 📈 性能优化

### 1. 缓存策略

```python
class LLMResultCache:
    """LLM结果缓存"""
    
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存"""
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item["timestamp"] < self.ttl:
                return item["result"]
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, result: Dict[str, Any]):
        """设置缓存"""
        self.cache[key] = {
            "result": result,
            "timestamp": time.time()
        }
```

### 2. 批量处理

```python
async def batch_analyze_intents(
    self,
    user_inputs: List[str],
    context: Optional[Dict[str, Any]] = None
) -> List[UnifiedIntentResult]:
    """批量分析意图（优化性能）"""
    
    # 并行处理
    tasks = [
        self.understand_intent(input_text, context)
        for input_text in user_inputs
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理异常
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"批量分析失败: {result}")
            processed_results.append(None)
        else:
            processed_results.append(result)
    
    return processed_results
```

---

## 🧪 测试方案

### 1. 单元测试

```python
# tests/test_unified_intent_llm.py

class TestUnifiedIntentLLM:
    """统一意图识别LLM测试"""
    
    @pytest.mark.asyncio
    async def test_llm_intent_analysis(self):
        """测试LLM意图分析"""
        service = UnifiedIntentService()
        
        result = await service._analyze_intent_with_llm(
            "我需要创建采购订单"
        )
        
        assert result["intent"] == "tool_execution"
        assert result["confidence"] > 0.7
        assert result["business_domain"] == "procurement"
    
    @pytest.mark.asyncio
    async def test_llm_entity_extraction(self):
        """测试LLM实体提取"""
        service = UnifiedIntentService()
        
        result = await service._analyze_intent_with_llm(
            "为供应商ABC创建采购订单，物料MAT001数量100"
        )
        
        entities = result["extracted_entities"]
        assert entities["supplier"] == "ABC"
        assert entities["material"] == "MAT001"
        assert entities["quantity"] == "100"
    
    @pytest.mark.asyncio
    async def test_llm_fallback(self):
        """测试LLM降级"""
        service = UnifiedIntentService()
        service.use_llm = False  # 禁用LLM
        
        result = await service.understand_intent("测试输入")
        
        # 应该降级到规则匹配
        assert result.fallback_mode is True
```

### 2. 集成测试

```python
@pytest.mark.asyncio
async def test_end_to_end_llm_enhanced_flow():
    """端到端LLM增强流程测试"""
    service = UnifiedIntentService()
    
    # 复杂意图
    user_input = "我需要采购一批原料，供应商是ABC公司，物料编号MAT001，数量100"
    
    result = await service.understand_intent(user_input)
    
    # 验证结果
    assert result.base_intent == "tool_execution"
    assert result.confidence > 0.8
    assert len(result.suggested_activities) > 0
    assert len(result.execution_suggestions) > 0
    
    # 验证自动填充的参数
    suggestion = result.execution_suggestions[0]
    assert suggestion.auto_filled_params["supplier_code"] == "ABC"
    assert suggestion.auto_filled_params["material_code"] == "MAT001"
```

---

## 📋 实施计划

### 阶段1: 基础LLM集成（1-2天）

1. ✅ 添加LLM客户端初始化
2. ✅ 实现`_analyze_intent_with_llm`方法
3. ✅ 实现LLM系统提示词
4. ✅ 添加降级机制
5. ✅ 单元测试

### 阶段2: 语义引擎协作（1-2天）

1. ✅ 实现`_query_semantic_engine_enhanced`方法
2. ✅ 实现查询增强逻辑
3. ✅ 实现结果融合
4. ✅ 集成测试

### 阶段3: 复杂意图识别（2-3天）

1. ✅ 实现多步骤意图识别
2. ✅ 实现多实体提取
3. ✅ 实现自动参数填充
4. ✅ 端到端测试

### 阶段4: 性能优化（1-2天）

1. ✅ 实现缓存机制
2. ✅ 实现批量处理
3. ✅ 性能测试和调优

### 阶段5: 文档和部署（1天）

1. ✅ 更新API文档
2. ✅ 更新配置文档
3. ✅ 部署和验证

---

## ✅ 方案总结

### 核心特性

1. ✅ **LLM作为统一入口**: DeepSeek LLM作为第一层意图理解
2. ✅ **增强意图识别**: 支持复杂自然语言理解
3. ✅ **为语义引擎提供输入**: LLM结果优化向量搜索
4. ✅ **复杂意图识别**: 多步骤、多实体、上下文相关
5. ✅ **向后兼容**: 支持降级到现有实现
6. ✅ **高性能**: 缓存机制和批量处理

### 技术亮点

- 🎯 **多层融合**: LLM + 向量搜索 + 规则匹配
- 🎯 **智能降级**: 自动降级保证可用性
- 🎯 **自动填充**: 使用LLM提取的实体自动填充参数
- 🎯 **可配置**: 灵活的环境变量配置

### 预期效果

- 📈 **意图识别准确率**: 提升20-30%
- 📈 **复杂意图支持**: 支持多步骤、多实体意图
- 📈 **用户体验**: 更自然的交互，自动参数填充
- 📈 **系统可用性**: 降级机制保证高可用

---

**方案版本**: v1.0  
**设计日期**: 2025-12-02  
**状态**: ✅ 方案设计完成，待实施


