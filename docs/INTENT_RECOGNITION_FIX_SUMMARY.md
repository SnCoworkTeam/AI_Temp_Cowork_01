# 意图识别修复总结：采购订单查询问题

## 修复内容

### 1. 改进快速关键词匹配（`metadata_first_intent_recognizer.py`）

**问题**：快速匹配只返回通用的 `sap_query` 工具，没有检索业务实体元数据，导致无法获取表名信息。

**修复**：
- 在快速匹配时，并行检索业务实体元数据（2秒超时）
- 如果找到业务实体，将其包含在元数据中，供LLM使用

```python
# 如果是SAP相关，尝试快速检索业务实体（获取表名信息）
if is_sap:
    try:
        entities = await asyncio.wait_for(
            self.metadata_retriever._search_business_entities(user_input, limit=5),
            timeout=2.0
        )
        if entities:
            metadata["business_entities"] = entities
    except (asyncio.TimeoutError, Exception) as e:
        logger.debug(f"Quick business entity search failed: {e}")
```

### 2. 增强LLM提示词（`metadata_first_intent_recognizer.py`）

**问题**：LLM提示词没有明确说明如何从业务实体元数据中提取SAP表名。

**修复**：
- 在系统提示词中添加SAP查询规则
- 明确说明如何从业务实体元数据中提取表名
- 提供默认映射规则（采购订单→I_PurchaseOrder等）

```python
# 重要规则（SAP查询）：
如果用户查询SAP数据，必须从业务实体元数据中提取表名：
- 如果业务实体元数据中包含 "sap_table_name" 字段，使用该值作为表名
- 如果没有元数据，根据实体名称推断：
  * "采购订单" / "purchase order" → 表名: "I_PurchaseOrder"
  * "销售订单" / "sales order" → 表名: "I_SalesOrder"
  ...
```

### 3. 改进参数提取逻辑（`orchestration_engine.py`）

**问题**：SAP查询时硬编码了 `"table": "I_SalesOrder"`，没有根据用户输入动态识别表名。

**修复**：
- 优先从意图分析的 `extracted_context.parameters` 中提取表名
- 如果没有，根据用户输入中的关键词推断表名
- 支持采购订单、销售订单、物料、客户、供应商等

```python
# 优先从意图分析中提取表名
extracted_params = intent_analysis.extracted_context.get("parameters", {})
table = extracted_params.get("table")

# 如果没有表名，尝试从用户输入中推断
if not table:
    user_lower = user_input.lower()
    if "采购订单" in user_input or "purchase" in user_lower:
        table = "I_PurchaseOrder"
    elif "销售订单" in user_input or "sales" in user_lower:
        table = "I_SalesOrder"
    ...
```

### 4. 改进元数据上下文格式化（`metadata_first_intent_recognizer.py`）

**问题**：格式化元数据上下文时，没有包含业务实体的表名信息。

**修复**：
- 在格式化业务实体时，包含表名信息
- 如果没有业务实体元数据，提供默认映射规则提示

```python
# 业务实体元数据（重要：包含表名信息）
for e in business_entities[:5]:
    name = e.get("name", "") or e.get("display_name", "")
    table_name = e.get("sap_table_name") or e.get("table_name") or e.get("metadata", {}).get("sap_table_name")
    if table_name:
        entity_info.append(f"{name} (表: {table_name})")
```

## 修复效果

### 修复前
- ❌ 查询"采购订单"时，硬编码使用 `I_SalesOrder` 表
- ❌ 快速匹配没有检索业务实体元数据
- ❌ LLM提示词没有明确表名提取规则
- ❌ 参数提取逻辑过于简单

### 修复后
- ✅ 查询"采购订单"时，自动识别为 `I_PurchaseOrder` 表
- ✅ 快速匹配会检索业务实体元数据（如果可用）
- ✅ LLM提示词明确说明如何提取表名
- ✅ 参数提取支持多种推断方式（元数据→关键词→默认值）

## 测试验证

### 测试场景1：查询采购订单
```
用户输入: "分析一下采购订单"

预期流程:
1. 快速匹配检测到"采购订单"关键词
2. 检索业务实体元数据（如果可用）
3. LLM理解：识别为sap_query，提取表名I_PurchaseOrder
4. 工具执行：调用sap_query，参数{"table": "I_PurchaseOrder", "query": "分析一下采购订单"}
```

### 测试场景2：查询销售订单
```
用户输入: "查询销售订单"

预期流程:
1. 快速匹配检测到"销售订单"关键词
2. LLM理解：识别为sap_query，提取表名I_SalesOrder
3. 工具执行：调用sap_query，参数{"table": "I_SalesOrder", "query": "查询销售订单"}
```

### 测试场景3：查询物料
```
用户输入: "查看物料信息"

预期流程:
1. 快速匹配检测到"物料"关键词
2. LLM理解：识别为sap_query，提取表名I_Material
3. 工具执行：调用sap_query，参数{"table": "I_Material", "query": "查看物料信息"}
```

## 元数据驱动 vs 硬编码

### 当前实现（混合模式）
- ✅ **元数据优先**：优先从元数据服务检索业务实体
- ✅ **智能降级**：如果元数据不可用，使用关键词推断
- ✅ **默认映射**：提供默认映射规则作为最后保障

### 未来改进方向
1. **完全元数据驱动**：
   - 所有业务实体都注册到元数据服务
   - 业务实体元数据包含完整的表名映射
   - 不再需要硬编码的关键词推断

2. **语义搜索增强**：
   - 使用向量化搜索找到最相关的业务实体
   - 支持同义词和模糊匹配

3. **动态学习**：
   - 从用户查询中学习新的实体映射
   - 自动更新元数据服务

## 相关文件

- `agent-service/src/core/metadata_first_intent_recognizer.py` - 元数据前置意图识别器
- `agent-service/src/core/orchestration_engine.py` - 编排引擎（参数提取）
- `agent-service/src/core/conversation_agent.py` - 对话理解智能体

## 部署说明

修复已完成，服务已重启。请测试以下场景：
1. "分析一下采购订单"
2. "查询销售订单"
3. "查看物料信息"

如果仍有问题，请检查：
1. 元数据服务是否正常运行
2. 业务实体是否已注册到元数据服务
3. 日志中是否有错误信息


