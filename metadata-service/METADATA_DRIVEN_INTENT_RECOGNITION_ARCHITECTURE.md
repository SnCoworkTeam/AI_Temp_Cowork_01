# 元数据驱动的意图识别架构设计

## 📋 当前架构分析

### 现有实现

#### 1. 意图识别流程（当前）

```
用户输入 
  ↓
LLM语义分析（使用提示词模板）
  ↓
硬编码分类（TaskType枚举）
  ↓
工具搜索（search_tools）
  ↓
工具执行
```

**问题点**：
- ❌ LLM分析后仍使用硬编码的 `TaskType` 枚举分类
- ❌ 工具搜索是独立的步骤，没有与意图识别深度集成
- ❌ 工具元数据（description、parameters）没有被充分利用
- ❌ 新增工具需要修改硬编码的关键词模式

#### 2. 现有元数据支持

**已实现**：
- ✅ `MetadataEnhancedPromptBuilder` - 使用SAP业务元数据增强提示词
- ✅ `search_tools` - MCP Gateway支持工具搜索
- ✅ `ToolDefinition` - 工具定义包含 `name`、`description`、`parameters`
- ✅ `metadata_driven_executor` - 元数据增强路由决策

**缺失**：
- ❌ 工具元数据没有用于意图识别
- ❌ 没有工具语义索引（向量化）
- ❌ 意图识别和工具匹配是分离的步骤

## 🎯 新架构设计：元数据驱动的意图识别

### 核心思想

```
用户输入 
  ↓
LLM语义理解（无硬编码分类）
  ↓
工具元数据检索（向量搜索）
  ↓
动态意图匹配（基于工具能力）
  ↓
自动工具调用
```

### 架构层次

```
┌─────────────────────────────────────────┐
│  元数据驱动的意图识别器                  │
│  MetadataDrivenIntentRecognizer        │
├─────────────────────────────────────────┤
│  1. 语义理解层                          │
│     - LLM语义分析（无分类标签）          │
│     - 业务上下文提取                    │
│                                         │
│  2. 元数据检索层                        │
│     - 工具元数据向量搜索                │
│     - SAP业务元数据检索                 │
│     - 服务能力匹配                      │
│                                         │
│  3. 动态匹配层                          │
│     - 意图-工具语义匹配                 │
│     - 参数自动提取                      │
│     - 执行策略生成                      │
└─────────────────────────────────────────┘
```

## 🔧 实施步骤

### 阶段1：工具元数据向量化（1周）

#### 1.1 扩展工具元数据模型

```python
# mcp-gateway/src/models/tool_models.py
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]
    
    # 新增字段
    semantic_tags: List[str]  # 语义标签
    business_domain: Optional[str]  # 业务领域
    use_cases: List[str]  # 使用场景
    examples: List[Dict[str, str]]  # 使用示例
    embedding: Optional[List[float]]  # 向量嵌入
```

#### 1.2 工具元数据向量化服务

```python
# mcp-gateway/src/services/tool_metadata_service.py
class ToolMetadataService:
    """工具元数据服务"""
    
    async def index_tool_metadata(self, tool: ToolDefinition):
        """索引工具元数据（向量化）"""
        # 构建工具描述文本
        tool_text = f"""
        工具名称: {tool.name}
        工具描述: {tool.description}
        业务领域: {tool.business_domain}
        使用场景: {', '.join(tool.use_cases)}
        参数说明: {self._format_parameters(tool.parameters)}
        """
        
        # 生成向量嵌入
        embedding = await self.embedding_service.embed(tool_text)
        tool.embedding = embedding
        
        # 存储到向量数据库
        await self.vector_store.upsert(
            collection="tool_metadata",
            id=tool.name,
            vector=embedding,
            metadata={
                "name": tool.name,
                "description": tool.description,
                "business_domain": tool.business_domain,
                "use_cases": tool.use_cases,
                "parameters": tool.parameters
            }
        )
    
    async def search_tools_by_intent(self, intent_description: str, top_k: int = 5):
        """基于意图描述搜索工具"""
        # 生成意图向量
        intent_embedding = await self.embedding_service.embed(intent_description)
        
        # 向量相似度搜索
        results = await self.vector_store.similarity_search(
            collection="tool_metadata",
            query_vector=intent_embedding,
            top_k=top_k
        )
        
        return results
```

### 阶段2：元数据驱动的意图识别器（2周）

#### 2.1 实现核心识别器

```python
# agent-service/src/core/metadata_driven_intent_recognizer.py
class MetadataDrivenIntentRecognizer:
    """元数据驱动的意图识别器"""
    
    def __init__(self, llm_service, metadata_service, tool_metadata_service):
        self.llm = llm_service
        self.metadata = metadata_service
        self.tool_metadata = tool_metadata_service
    
    async def recognize_intent(self, user_input: str, context: Dict[str, Any] = None):
        """
        基于元数据的意图识别
        
        流程：
        1. LLM语义理解（无硬编码分类）
        2. 工具元数据检索
        3. 动态匹配和参数提取
        """
        
        # 步骤1: LLM语义理解
        semantic_analysis = await self._llm_semantic_understanding(user_input, context)
        
        # 步骤2: 工具元数据检索
        tool_candidates = await self._search_tool_metadata(semantic_analysis)
        
        # 步骤3: 动态匹配
        matched_tools = await self._match_tools_to_intent(semantic_analysis, tool_candidates)
        
        # 步骤4: 参数提取
        execution_plan = await self._extract_parameters(semantic_analysis, matched_tools)
        
        return {
            "semantic_understanding": semantic_analysis,
            "matched_tools": matched_tools,
            "execution_plan": execution_plan,
            "confidence": self._calculate_confidence(semantic_analysis, matched_tools)
        }
    
    async def _llm_semantic_understanding(self, user_input: str, context: Dict):
        """LLM语义理解 - 不使用硬编码分类"""
        
        prompt = f"""
        分析用户输入的语义意图，不要使用预定义的分类标签。
        
        用户输入: "{user_input}"
        上下文: {context}
        
        请分析：
        1. 用户想要做什么？（用自然语言描述）
        2. 涉及哪些业务实体或概念？
        3. 需要什么类型的操作？（查询、创建、更新、分析等）
        4. 有哪些约束条件或参数？
        
        返回JSON格式：
        {{
            "intent_description": "用户意图的自然语言描述",
            "entities": ["实体1", "实体2"],
            "operation_type": "操作类型（自然语言）",
            "parameters": {{"参数名": "参数值或描述"}},
            "business_context": "业务上下文描述"
        }}
        """
        
        response = await self.llm.chat(messages=[{"role": "user", "content": prompt}])
        return json.loads(response)
    
    async def _search_tool_metadata(self, semantic_analysis: Dict):
        """基于语义分析搜索工具元数据"""
        
        # 构建搜索查询
        intent_text = f"""
        {semantic_analysis['intent_description']}
        操作类型: {semantic_analysis['operation_type']}
        业务上下文: {semantic_analysis.get('business_context', '')}
        """
        
        # 向量搜索工具
        tool_candidates = await self.tool_metadata.search_tools_by_intent(
            intent_text,
            top_k=5
        )
        
        return tool_candidates
    
    async def _match_tools_to_intent(self, semantic_analysis: Dict, tool_candidates: List):
        """动态匹配工具到意图"""
        
        matched_tools = []
        
        for tool in tool_candidates:
            # 计算匹配度
            match_score = await self._calculate_match_score(
                semantic_analysis,
                tool
            )
            
            if match_score > 0.7:  # 阈值可配置
                matched_tools.append({
                    "tool": tool,
                    "match_score": match_score,
                    "reasoning": self._generate_match_reasoning(semantic_analysis, tool)
                })
        
        # 按匹配度排序
        matched_tools.sort(key=lambda x: x["match_score"], reverse=True)
        
        return matched_tools
    
    async def _extract_parameters(self, semantic_analysis: Dict, matched_tools: List):
        """从语义分析中提取工具参数"""
        
        if not matched_tools:
            return None
        
        best_tool = matched_tools[0]["tool"]
        tool_params = best_tool.get("parameters", {})
        
        # 使用LLM提取参数
        prompt = f"""
        从用户输入中提取工具参数。
        
        用户输入: "{semantic_analysis.get('user_input', '')}"
        工具参数定义: {json.dumps(tool_params, ensure_ascii=False)}
        已识别的实体: {semantic_analysis.get('entities', [])}
        
        请提取并填充工具参数，返回JSON格式。
        """
        
        response = await self.llm.chat(messages=[{"role": "user", "content": prompt}])
        extracted_params = json.loads(response)
        
        return {
            "tool_name": best_tool["name"],
            "parameters": extracted_params,
            "confidence": matched_tools[0]["match_score"]
        }
```

### 阶段3：集成到现有系统（1周）

#### 3.1 替换意图识别逻辑

```python
# agent-service/src/core/conversation_agent.py
class ConversationAgent:
    def __init__(self):
        # 初始化元数据驱动的识别器
        self.metadata_recognizer = MetadataDrivenIntentRecognizer(
            llm_service=deepseek_llm,
            metadata_service=metadata_client,
            tool_metadata_service=tool_metadata_service
        )
        # 保留硬编码规则作为降级方案
        self.keyword_patterns = {...}  # 仅用于降级
    
    async def understand_conversation(self, message: str, context: Dict = None):
        """新的意图理解流程"""
        
        try:
            # 优先使用元数据驱动识别
            intent_result = await self.metadata_recognizer.recognize_intent(
                message, context
            )
            
            # 转换为IntentAnalysis格式（保持兼容性）
            return self._convert_to_intent_analysis(intent_result)
            
        except Exception as e:
            logger.warning(f"Metadata-driven recognition failed: {e}, falling back")
            # 降级到LLM+硬编码（不是纯硬编码）
            return await self._analyze_with_llm(message, context)
    
    def _convert_to_intent_analysis(self, intent_result: Dict) -> IntentAnalysis:
        """转换为IntentAnalysis格式"""
        
        matched_tools = intent_result.get("matched_tools", [])
        execution_plan = intent_result.get("execution_plan")
        
        # 动态确定任务类型
        if execution_plan and matched_tools:
            task_type = TaskType.TOOL_EXECUTION
            required_tools = [execution_plan["tool_name"]]
        else:
            task_type = TaskType.SIMPLE_QUERY
            required_tools = []
        
        return IntentAnalysis(
            task_type=task_type,
            confidence=intent_result.get("confidence", 0.5),
            extracted_context={
                "semantic_understanding": intent_result.get("semantic_understanding"),
                "parameters": execution_plan.get("parameters", {}) if execution_plan else {}
            },
            required_tools=required_tools,
            required_services=["mcp-gateway"] if required_tools else [],
            reasoning=intent_result.get("execution_plan", {}).get("reasoning", "")
        )
```

#### 3.2 工具执行集成

```python
# agent-service/src/core/orchestration_engine.py
async def _handle_tool_execution(self, user_input: str, context: Dict, decision: RoutingDecision, intent_analysis: IntentAnalysis):
    """处理工具执行 - 使用元数据驱动的参数提取"""
    
    # 从intent_analysis中获取已提取的参数
    execution_plan = intent_analysis.extracted_context.get("execution_plan")
    
    if execution_plan:
        # 使用元数据驱动识别的结果
        tool_id = execution_plan["tool_name"]
        parameters = execution_plan["parameters"]
    else:
        # 降级到原有逻辑
        tool_id = decision.required_tools[0] if decision.required_tools else None
        parameters = decision.execution_params.get("context", {}).get("parameters", {})
    
    # 执行工具
    result = await self.service_clients.mcp_gateway.execute_tool(
        tool_id, parameters, context
    )
    
    return result
```

## 📊 实际工作流程示例

### 场景：用户说"发送邮件给yubin.liu@pcitc.com"

**旧方式（硬编码）**：
```
1. 匹配关键词 "发送邮件" → tool_execution
2. 硬编码识别 send_email 工具
3. 手动提取参数
```

**新方式（元数据驱动）**：
```
1. LLM语义理解：
   {
     "intent_description": "用户想要发送一封电子邮件",
     "operation_type": "发送",
     "entities": ["yubin.liu@pcitc.com"],
     "parameters": {"to_emails": "yubin.liu@pcitc.com"}
   }

2. 工具元数据检索：
   - 向量搜索 "发送邮件" → 找到 send_email 工具
   - 匹配度: 0.95

3. 动态匹配：
   - send_email 工具描述: "发送电子邮件"
   - 参数自动提取: {"to_emails": "yubin.liu@pcitc.com"}

4. 自动执行：
   - 调用 send_email 工具
   - 使用提取的参数
```

## 🎯 优势对比

| 方面 | 当前架构 | 新架构（元数据驱动） |
|------|---------|-------------------|
| **工具发现** | 硬编码关键词匹配 | 向量语义搜索 |
| **参数提取** | 手动正则表达式 | LLM自动提取 |
| **扩展性** | 需要修改代码 | 添加工具元数据即可 |
| **准确性** | 关键词可能误判 | 语义理解更准确 |
| **维护成本** | 高（代码维护） | 低（元数据维护） |

## 🚀 实施优先级

### 高优先级（立即实施）

1. **工具元数据向量化**
   - 为现有工具添加语义描述
   - 实现工具元数据向量索引
   - 支持向量搜索

2. **元数据驱动识别器核心功能**
   - 实现 `MetadataDrivenIntentRecognizer`
   - 集成工具元数据搜索
   - 实现动态匹配逻辑

### 中优先级（1-2周内）

3. **参数自动提取**
   - LLM参数提取
   - 参数验证和补全
   - 错误处理和降级

4. **性能优化**
   - 向量搜索缓存
   - 识别结果缓存
   - 批量处理优化

### 低优先级（持续优化）

5. **高级功能**
   - 多工具组合推荐
   - 工具链自动编排
   - 用户偏好学习

## 💡 关键技术点

### 1. 工具元数据设计

```python
# 示例：send_email 工具的元数据
{
    "name": "send_email",
    "description": "发送电子邮件，支持文本和HTML格式，可以添加附件",
    "semantic_tags": ["邮件", "发送", "通知", "通信"],
    "business_domain": "communication",
    "use_cases": [
        "发送会议通知",
        "发送报告",
        "发送提醒邮件"
    ],
    "examples": [
        {
            "user_input": "发送邮件给张三",
            "parameters": {"to_emails": "zhangsan@example.com"}
        }
    ]
}
```

### 2. 向量搜索策略

- **混合搜索**：结合关键词和向量搜索
- **重排序**：使用LLM对搜索结果重排序
- **上下文增强**：考虑对话历史和用户上下文

### 3. 降级策略

- **元数据驱动失败** → LLM+硬编码
- **LLM失败** → 纯硬编码规则
- **工具搜索失败** → 使用默认工具

## 📝 实施检查清单

- [ ] 扩展 `ToolDefinition` 模型，添加语义字段
- [ ] 实现工具元数据向量化服务
- [ ] 实现 `MetadataDrivenIntentRecognizer` 核心类
- [ ] 集成到 `ConversationAgent`
- [ ] 更新工具执行逻辑，使用元数据驱动的参数
- [ ] 为现有工具添加元数据（send_email、sap_query等）
- [ ] 实现向量搜索和匹配逻辑
- [ ] 添加降级策略和错误处理
- [ ] 性能测试和优化
- [ ] 文档和示例更新

## 🔄 迁移路径

### 渐进式迁移

1. **阶段1**：并行运行（元数据驱动 + 原有逻辑）
2. **阶段2**：逐步切换（新工具使用元数据驱动）
3. **阶段3**：完全迁移（所有工具使用元数据驱动）

这样可以确保系统稳定性，同时逐步提升智能化水平。


