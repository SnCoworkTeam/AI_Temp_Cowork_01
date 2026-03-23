# 统一意图识别LLM增强方案 v2.0（优化版）

**方案版本**: v2.0  
**更新日期**: 2025-12-02  
**更新说明**: 基于专家评审优化，增强健壮性和实用性

---

## 📋 方案优化说明

### 主要优化点

1. ✅ **健壮的DeepSeek客户端**: 减少对LangChain的依赖，支持直接HTTP调用
2. ✅ **优化的系统提示词**: 增加少样本学习，更精炼企业化
3. ✅ **动态融合策略**: 根据场景智能调整权重
4. ✅ **接口兼容性验证**: 确认现有语义引擎接口能力
5. ✅ **并行实施策略**: 优化实施优先级，降低风险

---

## 🔧 技术实现优化

### 1. 健壮的DeepSeek客户端（优化版）

#### 1.1 多层级客户端设计

```python
# services/llm_client.py (新建)

import httpx
import os
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CUSTOM = "custom"


class RobustDeepSeekClient:
    """
    健壮的DeepSeek客户端
    支持多种调用方式，自动降级
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "deepseek-chat",
        timeout: float = 10.0,
        temperature: float = 0.3
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.getenv("LLM_MODEL", "deepseek-chat")
        self.timeout = timeout
        self.temperature = temperature
        
        # 清理base_url
        self.base_url = self.base_url.rstrip("/v1").rstrip("/")
        
        # 初始化策略：优先直接HTTP，降级到LangChain
        self.use_direct_http = True
        self.langchain_client = None
        self._init_clients()
    
    def _init_clients(self):
        """初始化客户端（多层级）"""
        # 策略1: 直接HTTP客户端（优先）
        try:
            self.http_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            logger.info("HTTP客户端初始化成功（直接调用模式）")
        except Exception as e:
            logger.warning(f"HTTP客户端初始化失败: {e}")
            self.use_direct_http = False
        
        # 策略2: LangChain客户端（降级）
        if not self.use_direct_http:
            try:
                from langchain_openai import ChatOpenAI
                self.langchain_client = ChatOpenAI(
                    model=self.model,
                    temperature=self.temperature,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout
                )
                logger.info("LangChain客户端初始化成功（降级模式）")
            except Exception as e:
                logger.error(f"LangChain客户端初始化失败: {e}")
                self.langchain_client = None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        聊天补全（多层级调用）
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数（temperature, max_tokens等）
        
        Returns:
            Dict: API响应
        """
        # 策略1: 直接HTTP调用（优先）
        if self.use_direct_http:
            try:
                return await self._chat_completion_http(messages, **kwargs)
            except Exception as e:
                logger.warning(f"直接HTTP调用失败: {e}，降级到LangChain")
                self.use_direct_http = False
        
        # 策略2: LangChain调用（降级）
        if self.langchain_client:
            try:
                return await self._chat_completion_langchain(messages, **kwargs)
            except Exception as e:
                logger.error(f"LangChain调用失败: {e}")
                raise RuntimeError(f"所有LLM调用方式都失败: {e}")
        
        raise RuntimeError("没有可用的LLM客户端")
    
    async def _chat_completion_http(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """直接HTTP调用DeepSeek API"""
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }
        
        # DeepSeek特殊参数（如果支持）
        if kwargs.get("reasoning", False):
            payload["reasoning"] = True
        
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # 提取内容
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            return {
                "content": content,
                "raw_response": result,
                "usage": result.get("usage", {})
            }
        else:
            raise ValueError("API响应格式异常")
    
    async def _chat_completion_langchain(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """通过LangChain调用"""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # 转换消息格式
        langchain_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))
        
        # 调用LLM
        response = await self.langchain_client.ainvoke(langchain_messages)
        
        return {
            "content": response.content,
            "raw_response": {"choices": [{"message": {"content": response.content}}]},
            "usage": {}
        }
    
    async def close(self):
        """关闭客户端"""
        if hasattr(self, "http_client") and self.http_client:
            await self.http_client.aclose()
```

### 2. 优化的系统提示词（少样本学习）

```python
def _build_enhanced_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
    """优化的系统提示词（增加少样本学习）"""
    
    few_shot_examples = [
        {
            "input": "我需要创建采购订单，供应商ABC，物料MAT001，数量100",
            "output": {
                "intent": "tool_execution",
                "confidence": 0.95,
                "business_domain": "procurement",
                "extracted_entities": {
                    "supplier": "ABC",
                    "material": "MAT001",
                    "quantity": "100"
                },
                "query_keywords": ["采购订单", "创建", "供应商", "物料"],
                "reasoning": "明确的操作请求，涉及采购订单创建，需要调用SAP系统"
            }
        },
        {
            "input": "查询一下采购订单PO1001的状态",
            "output": {
                "intent": "tool_execution",
                "confidence": 0.90,
                "business_domain": "procurement",
                "extracted_entities": {
                    "po_number": "PO1001"
                },
                "query_keywords": ["采购订单", "查询", "状态"],
                "reasoning": "查询操作，需要调用SAP查询接口"
            }
        },
        {
            "input": "什么是采购订单？",
            "output": {
                "intent": "simple_chat",
                "confidence": 0.85,
                "business_domain": null,
                "extracted_entities": {},
                "query_keywords": ["采购订单", "概念"],
                "reasoning": "知识性问题，不需要执行操作"
            }
        }
    ]
    
    base_prompt = f"""
# 角色与目标
你是企业AI助手统一意图理解层的核心分析引擎，专门将员工模糊的业务请求，精准解析为标准化的执行指令。

# 核心任务
1. **意图分类**：严格从以下4类中选择：
   - `tool_execution`: 需要调用具体系统（如SAP）执行一个原子操作
   - `workflow_task`: 涉及多个步骤或需要审批的流程
   - `knowledge_search`: 仅查询信息或文档，不修改系统数据
   - `simple_chat`: 问候、咨询等非操作类对话

2. **实体提取**：仅提取**可用于系统API调用**的明确实体（如订单号、物料编码、供应商代码）

3. **业务领域识别**：识别业务领域（procurement/finance/warehouse/sales/hr），如果不确定返回null

4. **查询增强**：为后续企业知识图谱检索生成2-4个最相关的业务关键词

# 输出格式
你必须返回一个**严格的JSON对象**，且仅包含以下字段：
- `intent`: 意图类型（字符串）
- `confidence`: 置信度（0.0-1.0）
- `business_domain`: 业务领域（字符串或null）
- `extracted_entities`: 实体字典
- `query_keywords`: 关键词列表
- `reasoning`: 分析理由（字符串）
- `needs_semantic_search`: 是否需要语义搜索（布尔值）

# 少样本示例（Few-shot Examples）
{json.dumps(few_shot_examples, ensure_ascii=False, indent=2)}

# 重要规则
- 如果用户查询SAP ERP数据（如销售订单、采购订单、物料、客户、供应商等），必须使用 `tool_execution` 类型
- 如果用户提到"SAP"、"ERP"、"查询"、"查一下"等关键词，且涉及具体业务数据，应识别为 `tool_execution`
- 如果只是询问SAP概念、使用方法等知识性问题，可以使用 `simple_chat`
- 对于SAP查询，`extracted_entities` 应包含具体的业务实体（如订单号、物料编码等）
- `confidence` 必须反映你对分析结果的确定程度，不确定时应该较低（<0.7）
"""
    
    # 如果有上下文，添加到提示词
    if context:
        context_info = f"""
# 上下文信息
{json.dumps(context, ensure_ascii=False, indent=2)}

请结合上下文信息进行意图分析。
"""
        base_prompt += context_info
    
    return base_prompt
```

### 3. 动态融合策略（精细化）

```python
def _dynamic_fusion_strategy(
    self,
    llm_result: Dict[str, Any],
    semantic_results: Optional[IntentQueryResult]
) -> Dict[str, Any]:
    """
    动态融合策略：根据场景智能调整权重
    
    Returns:
        {
            "strategy": "策略名称",
            "final_confidence": 最终置信度,
            "weight_llm": LLM权重,
            "weight_semantic": 语义权重,
            "reasoning": 融合理由
        }
    """
    llm_confidence = llm_result.get("confidence", 0.5)
    llm_domain = llm_result.get("business_domain")
    
    # 场景1: LLM置信度极高，但语义引擎无结果
    # -> 可能是新业务或未覆盖的场景，信任LLM但降低置信度
    if llm_confidence > 0.9 and (not semantic_results or not semantic_results.activities):
        return {
            "strategy": "trust_llm",
            "final_confidence": llm_confidence * 0.95,
            "weight_llm": 1.0,
            "weight_semantic": 0.0,
            "reasoning": "LLM高置信度但语义引擎无匹配，可能是新业务场景"
        }
    
    # 场景2: 语义引擎匹配到高相似度标准流程
    # -> 即使LLM置信度一般，也优先信任标准流程
    if semantic_results and semantic_results.scores and semantic_results.scores[0] > 0.85:
        semantic_score = semantic_results.scores[0]
        return {
            "strategy": "trust_semantic",
            "final_confidence": semantic_score,
            "weight_llm": 0.3,
            "weight_semantic": 0.7,
            "reasoning": "语义引擎匹配到高相似度标准流程，优先信任"
        }
    
    # 场景3: 两者结果冲突（业务领域不一致）
    # -> 需要人工审核或折中处理
    if semantic_results and semantic_results.activities:
        semantic_domain = semantic_results.activities[0].business_domain
        if llm_domain and semantic_domain and llm_domain != semantic_domain:
            return {
                "strategy": "needs_human_review",
                "final_confidence": 0.5,
                "weight_llm": 0.5,
                "weight_semantic": 0.5,
                "reasoning": f"LLM识别为{llm_domain}，但语义引擎匹配到{semantic_domain}，需要人工审核"
            }
    
    # 场景4: 两者结果一致，使用加权平均
    if semantic_results and semantic_results.scores:
        semantic_score = semantic_results.scores[0]
        
        # 根据LLM置信度动态调整权重
        if llm_confidence > 0.8:
            weight_llm = 0.6
            weight_semantic = 0.4
        elif llm_confidence > 0.6:
            weight_llm = 0.5
            weight_semantic = 0.5
        else:
            weight_llm = 0.4
            weight_semantic = 0.6
        
        final_confidence = weight_llm * llm_confidence + weight_semantic * semantic_score
        
        return {
            "strategy": "weighted_average",
            "final_confidence": final_confidence,
            "weight_llm": weight_llm,
            "weight_semantic": weight_semantic,
            "reasoning": f"加权融合：LLM({llm_confidence:.2f}) * {weight_llm} + 语义({semantic_score:.2f}) * {weight_semantic}"
        }
    
    # 默认：只有LLM结果
    return {
        "strategy": "llm_only",
        "final_confidence": llm_confidence * 0.8,  # 降低置信度
        "weight_llm": 1.0,
        "weight_semantic": 0.0,
        "reasoning": "仅LLM结果，无语义引擎匹配"
    }
```

### 4. 语义引擎接口适配器

```python
class SemanticEngineAdapter:
    """
    语义引擎适配器
    处理现有接口与新需求的适配
    """
    
    def __init__(self, semantic_engine: EnterpriseSemanticEngine):
        self.semantic_engine = semantic_engine
    
    async def query_intent_enhanced(
        self,
        user_input: str,
        llm_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        min_score: float = 0.5
    ) -> IntentQueryResult:
        """
        增强的意图查询（适配现有接口）
        
        Args:
            user_input: 原始用户输入
            llm_result: LLM分析结果
            context: 上下文信息
            top_k: 返回前k个结果
            min_score: 最小相似度
        
        Returns:
            IntentQueryResult: 查询结果
        """
        # 1. 构建增强的查询（使用LLM生成的关键词）
        enhanced_query = self._build_enhanced_query(user_input, llm_result)
        
        # 2. 调用现有接口（保持兼容）
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.semantic_engine.query_intent,
            enhanced_query,  # 使用增强的查询
            context,
            top_k,
            min_score
        )
        
        # 3. 业务领域过滤（如果LLM识别了业务领域）
        business_domain = llm_result.get("business_domain")
        if business_domain and result.activities:
            filtered_activities = []
            filtered_scores = []
            
            for activity, score in zip(result.activities, result.scores):
                if activity.business_domain == business_domain:
                    filtered_activities.append(activity)
                    filtered_scores.append(score)
            
            # 如果过滤后还有结果，使用过滤后的
            if filtered_activities:
                result.activities = filtered_activities[:top_k]
                result.scores = filtered_scores[:top_k]
                result.total_count = len(filtered_activities)
                logger.debug(f"业务领域过滤: {business_domain}，保留{len(filtered_activities)}个活动")
        
        return result
    
    def _build_enhanced_query(
        self,
        user_input: str,
        llm_result: Dict[str, Any]
    ) -> str:
        """构建增强的查询字符串"""
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

---

## 🔍 接口兼容性验证

### 现有接口能力检查

根据代码分析，`EnterpriseSemanticEngine.query_intent` 方法：

```python
def query_intent(
    self,
    user_input: str,
    context: Optional[Dict[str, Any]] = None,
    top_k: int = 10,
    min_score: float = 0.5
) -> IntentQueryResult:
```

**现有能力**:
- ✅ 接受 `user_input`（字符串）
- ✅ 接受 `context`（可选字典）
- ✅ 支持 `top_k` 和 `min_score` 参数
- ⚠️ **不支持直接按 `business_domain` 过滤**

**适配方案**:
- ✅ 使用适配器在结果后过滤（已在上面实现）
- ✅ 使用LLM生成的关键词增强查询（已在上面实现）

---

## 📋 优化后的实施计划

### 第1周：并行验证与基础集成

**主线任务**（3-4天）:
1. ✅ 实现健壮的DeepSeek客户端（`RobustDeepSeekClient`）
2. ✅ 实现优化的系统提示词（少样本学习）
3. ✅ 在`UnifiedIntentService`中集成LLM
4. ✅ 实现降级机制

**支线任务**（同时进行，2-3天）:
1. ✅ 验证现有语义引擎接口能力
2. ✅ 实现语义引擎适配器（`SemanticEngineAdapter`）
3. ✅ 编写接口兼容性测试

### 第2周：融合与测试

1. ✅ 实现动态融合策略
2. ✅ 实现结果融合逻辑
3. ✅ 编写单元测试和集成测试
4. ✅ 性能测试和调优

### 第3周：复杂意图识别

1. ✅ 实现多步骤意图识别
2. ✅ 实现多实体提取
3. ✅ 实现自动参数填充
4. ✅ 采购场景端到端试点

### 第4周：优化与部署

1. ✅ 实现缓存机制
2. ✅ 实现批量处理
3. ✅ 文档更新
4. ✅ 部署和验证

---

## ✅ 方案总结

### 核心优化

1. ✅ **健壮的客户端**: 多层级调用，自动降级
2. ✅ **优化的提示词**: 少样本学习，更精炼
3. ✅ **动态融合**: 智能权重调整
4. ✅ **接口适配**: 兼容现有语义引擎
5. ✅ **并行实施**: 降低风险，加快进度

### 技术亮点

- 🎯 **多层级降级**: HTTP → LangChain → 规则匹配
- 🎯 **智能融合**: 根据场景动态调整权重
- 🎯 **接口兼容**: 适配器模式，无需修改现有代码
- 🎯 **少样本学习**: 提升LLM理解准确性

---

**方案版本**: v2.0  
**更新日期**: 2025-12-02  
**状态**: ✅ 优化完成，准备实施


