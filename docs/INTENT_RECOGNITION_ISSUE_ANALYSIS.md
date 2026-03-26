# 意图识别问题分析：采购订单查询失败

## 问题描述

用户反馈：
1. 查询"分析一下采购订单"时，系统识别为 `tool_execution`，但查询失败
2. 质疑意图识别机制：为什么还是硬编码分类，而不是基于元数据？

## 问题分析

### 1. 意图识别流程

当前系统确实使用了**元数据前置意图识别**，流程如下：

```
用户输入: "分析一下采购订单"
    ↓
MetadataFirstIntentRecognizer.recognize_intent()
    ↓
1. 快速关键词匹配 (_quick_keyword_match)
   - 检测到 "采购订单" 关键词
   - 返回: {"sap_services": [{"name": "SAP查询", "type": "sap_query"}]}
    ↓
2. LLM理解 (_llm_understanding_with_metadata)
   - 基于元数据上下文理解用户意图
   - 应该返回: {"operation": "sap_query", "table": "I_PurchaseOrder", ...}
    ↓
3. 动态分类 (_dynamic_classification)
   - 基于LLM理解结果分类为 tool_execution
    ↓
4. 工具执行
   - 调用 sap_query 工具
   - 传递参数: {"table": "I_PurchaseOrder", "query": "分析一下采购订单"}
```

### 2. 问题根源

#### 问题1：快速关键词匹配过于简单

**位置**：`agent-service/src/core/metadata_first_intent_recognizer.py` 第334-362行

```python
async def _quick_keyword_match(self, user_input: str) -> Optional[Dict[str, Any]]:
    """快速关键词匹配"""
    user_lower = user_input.lower()
    
    # 检查是否是SAP相关
    sap_keywords = ["sap", "销售订单", "采购订单", "物料", "客户", "供应商"]
    is_sap = any(kw in user_lower for kw in sap_keywords)
    
    if is_sap:
        metadata["sap_services"] = [{"name": "SAP查询", "type": "sap_query"}]
```

**问题**：
- 只返回了通用的 `sap_query` 工具，没有具体的表名信息
- 没有区分"销售订单"和"采购订单"
- 没有从元数据服务检索具体的SAP实体信息

#### 问题2：LLM理解可能不准确

**位置**：`agent-service/src/core/metadata_first_intent_recognizer.py` 第529-600行

**问题**：
- LLM可能没有正确识别出需要查询 `I_PurchaseOrder` 表
- 或者识别出了，但参数传递不正确

#### 问题3：工具执行时参数缺失

**位置**：`agent-service/src/core/orchestration_engine.py` 第560-600行

**问题**：
- 如果LLM没有正确提取表名，工具执行时会使用默认表 `I_SalesOrder`
- 导致查询采购订单时实际查询了销售订单表

### 3. 硬编码 vs 元数据驱动

**当前状态**：
- ✅ 使用了元数据前置识别器
- ❌ 但快速匹配仍使用硬编码关键词
- ❌ 没有从元数据服务检索具体的业务实体信息

**用户期望**：
- 完全基于元数据驱动
- 从元数据服务检索"采购订单"相关的实体
- 自动识别对应的SAP表名（如 `I_PurchaseOrder`）

## 解决方案

### 方案1：改进快速关键词匹配（短期）

**修改**：`agent-service/src/core/metadata_first_intent_recognizer.py`

```python
async def _quick_keyword_match(self, user_input: str) -> Optional[Dict[str, Any]]:
    """快速关键词匹配（改进版）"""
    user_lower = user_input.lower()
    
    # 检查是否是SAP相关
    sap_keywords = ["sap", "销售订单", "采购订单", "物料", "客户", "供应商"]
    is_sap = any(kw in user_lower for kw in sap_keywords)
    
    if not is_sap:
        return None
    
    # 尝试从元数据服务快速检索业务实体
    try:
        # 并行检索工具和业务实体
        tools_task = self.metadata_retriever._search_tools(user_input, limit=3)
        entities_task = self.metadata_retriever._search_business_entities(user_input, limit=3)
        
        tools, entities = await asyncio.gather(tools_task, entities_task, return_exceptions=True)
        
        tools = tools if not isinstance(tools, Exception) else []
        entities = entities if not isinstance(entities, Exception) else []
        
        # 如果找到了具体的业务实体，返回更详细的元数据
        if entities:
            return {
                "tools": tools or [{"name": "sap_query", "type": "sap"}],
                "sap_services": [{"name": "SAP查询", "type": "sap_query"}],
                "business_entities": entities,  # 包含具体的表名信息
                "workflows": [],
                "retrieved_at": datetime.now().isoformat(),
                "query": user_input
            }
    except Exception as e:
        logger.debug(f"Quick metadata retrieval failed: {e}")
    
    # 降级到简单匹配
    return {
        "tools": [{"name": "sap_query", "type": "sap"}],
        "sap_services": [{"name": "SAP查询", "type": "sap_query"}],
        "business_entities": [],
        "workflows": [],
        "retrieved_at": datetime.now().isoformat(),
        "query": user_input
    }
```

### 方案2：增强LLM提示词（中期）

**修改**：`agent-service/src/core/metadata_first_intent_recognizer.py` 第529-600行

在LLM提示词中明确说明：
- 如果用户查询"采购订单"，应该使用 `I_PurchaseOrder` 表
- 如果用户查询"销售订单"，应该使用 `I_SalesOrder` 表
- 从业务实体元数据中提取表名信息

### 方案3：完善元数据服务（长期）

**目标**：
1. 确保所有SAP业务实体都注册到元数据服务
2. 业务实体元数据包含：
   - 中文名称（如"采购订单"）
   - 英文名称（如"Purchase Order"）
   - SAP表名（如 `I_PurchaseOrder`）
   - 相关工具（如 `sap_query`）

**实现**：
- 在 `sap-metadata-agent` 中自动发现并注册业务实体
- 在 `metadata-service` 中提供业务实体的语义搜索
- 在 `metadata-first-intent-recognizer` 中优先使用业务实体元数据

## 立即修复

### 修复1：改进快速匹配，包含业务实体检索

修改 `agent-service/src/core/metadata_first_intent_recognizer.py`：

```python
async def _quick_keyword_match(self, user_input: str) -> Optional[Dict[str, Any]]:
    """快速关键词匹配（改进版：包含业务实体检索）"""
    user_lower = user_input.lower()
    
    # 检查是否是SAP相关
    sap_keywords = ["sap", "销售订单", "采购订单", "物料", "客户", "供应商", "erp"]
    is_sap = any(kw in user_lower for kw in sap_keywords)
    
    # 检查是否是工具相关
    tool_keywords = ["发送邮件", "发邮件", "邮件", "email", "send"]
    is_tool = any(kw in user_lower for kw in tool_keywords)
    
    if not (is_sap or is_tool):
        return None
    
    metadata = {
        "tools": [],
        "sap_services": [],
        "business_entities": [],
        "workflows": [],
        "retrieved_at": datetime.now().isoformat(),
        "query": user_input
    }
    
    # 如果是SAP相关，尝试快速检索业务实体
    if is_sap:
        try:
            # 快速检索业务实体（带超时）
            entities = await asyncio.wait_for(
                self.metadata_retriever._search_business_entities(user_input, limit=5),
                timeout=2.0  # 2秒超时
            )
            if entities:
                metadata["business_entities"] = entities
                logger.debug(f"Found {len(entities)} business entities for quick match")
        except (asyncio.TimeoutError, Exception) as e:
            logger.debug(f"Quick business entity search failed: {e}")
        
        metadata["sap_services"] = [{"name": "SAP查询", "type": "sap_query"}]
    
    if is_tool:
        metadata["tools"] = [{"name": "send_email", "type": "email"}]
    
    return metadata
```

### 修复2：增强LLM提示词，明确表名映射

修改 `agent-service/src/core/metadata_first_intent_recognizer.py` 第542-600行：

在系统提示词中添加：

```python
# 业务实体映射规则：
- "采购订单" / "purchase order" → SAP表: I_PurchaseOrder
- "销售订单" / "sales order" → SAP表: I_SalesOrder
- "物料" / "material" → SAP表: I_Material
- "客户" / "customer" → SAP表: I_Customer
- "供应商" / "vendor" → SAP表: I_Vendor

如果业务实体元数据中包含 sap_table_name 字段，优先使用该字段的值。
```

### 修复3：改进参数提取逻辑

修改 `agent-service/src/core/orchestration_engine.py` 第560-600行：

在 `_handle_tool_execution` 中，如果工具是 `sap_query`，从 `intent_analysis.extracted_context` 中提取表名：

```python
if tool_id == "sap_query" or "sap" in tool_id.lower():
    # 从意图分析中提取表名
    extracted_params = intent_analysis.extracted_context.get("parameters", {})
    table = extracted_params.get("table")
    
    # 如果没有表名，尝试从业务实体元数据中获取
    if not table:
        # 从metadata中查找业务实体
        # ...
    
    # 如果仍然没有，使用默认值
    if not table:
        table = "I_SalesOrder"  # 默认查询销售订单表
```

## 验证步骤

1. **重启服务**：
   ```bash
   docker-compose restart agent-service
   ```

2. **测试查询**：
   - "分析一下采购订单"
   - "查询销售订单"
   - "查看物料信息"

3. **检查日志**：
   - 确认元数据检索成功
   - 确认LLM正确识别表名
   - 确认工具执行参数正确

## 预期效果

修复后：
1. ✅ 查询"采购订单"时，自动识别为 `I_PurchaseOrder` 表
2. ✅ 查询"销售订单"时，自动识别为 `I_SalesOrder` 表
3. ✅ 完全基于元数据驱动，减少硬编码
4. ✅ 支持更多业务实体类型


