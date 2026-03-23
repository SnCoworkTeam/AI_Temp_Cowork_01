# 邮件发送问题分析报告

## 问题描述

**用户输入**：`发送测试邮件给yubin.liu@pcitc.com`

**执行结果**：
- ❌ 邮件发送失败
- 错误：`Missing required parameter: to_emails`
- HTTP 400 错误

## 问题分析

### 1. 执行流程

```
用户输入: "发送测试邮件给yubin.liu@pcitc.com"
    ↓
动态工作流设计器 → 设计智能体网络
    ↓
MCP工具智能体 → 分析任务并提取参数
    ↓
LLM分析 → 生成execution_plan
    ↓
工具执行 → send_email工具
    ↓
参数验证 → ❌ 缺少to_emails参数
```

### 2. 根本原因

**LLM参数提取不完整**：
- MCP工具智能体使用LLM分析任务并提取参数
- LLM应该从"发送测试邮件给yubin.liu@pcitc.com"中提取：
  - `to_emails`: "yubin.liu@pcitc.com" ✅ 应该提取到
  - `subject`: "测试邮件" ✅ 应该提取到
  - `body`: "这是一封测试邮件" ✅ 应该提取到
- **但实际执行时，`optimized_parameters`中没有`to_emails`参数**

**可能的原因**：
1. LLM在分析时没有正确识别邮箱地址
2. LLM识别了但没有正确格式化为工具参数
3. 参数在传递过程中丢失
4. 缺少参数验证和补充机制

### 3. 代码问题点

#### 问题1：参数提取完全依赖LLM，没有fallback机制

在 `mcp_tool_agent.py` 的 `analyze_task` 方法中：
- 完全依赖LLM从任务描述中提取参数
- 如果LLM提取失败，没有正则表达式fallback
- 没有参数验证和补充逻辑

#### 问题2：缺少参数验证和默认值

在 `execute` 方法中：
- 直接使用LLM提取的`optimized_parameters`
- 没有验证必需参数是否存在
- 没有为缺失参数提供默认值

#### 问题3：邮箱地址提取不完整

虽然有 `_extract_email_parameters` 方法在 `orchestration_engine.py` 中，但：
- MCP工具智能体没有使用这个方法
- 两个地方都有参数提取逻辑，但互不关联

## 解决方案

### ✅ 已实施的修复

在 `mcp_tool_agent.py` 中添加了 `_enhance_tool_parameters` 方法：

1. **邮箱地址提取**（正则表达式fallback）：
   - 使用正则表达式 `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b` 提取邮箱
   - 支持"给XXX发"、"发送给XXX"等中文模式
   - 确保 `to_emails` 参数存在

2. **主题提取**：
   - 从"主题："、"标题："等关键词提取
   - 如果没有，使用默认值（"测试邮件"、"通知"等）

3. **正文提取**：
   - 从"内容："、"正文："等关键词提取
   - 如果没有，使用默认值

4. **参数验证**：
   - 在执行工具前检查所有必需参数
   - 记录缺失参数以便调试

### 修复代码位置

**文件**：`agent-service/src/core/agents/mcp_tool_agent.py`

**修改**：
- 在 `execute` 方法中，执行工具前调用 `_enhance_tool_parameters`
- 新增 `_enhance_tool_parameters` 方法，专门处理参数增强

## 测试验证

### 测试用例

**输入**：`发送测试邮件给yubin.liu@pcitc.com`

**预期结果**：
```json
{
  "to_emails": "yubin.liu@pcitc.com",
  "subject": "测试邮件",
  "body": "这是一封测试邮件。"
}
```

### 验证步骤

1. **检查参数提取**：
   - 查看日志中是否有 "Extracted to_emails from task description"
   - 确认 `to_emails` 参数存在

2. **检查工具执行**：
   - 查看MCP Gateway日志
   - 确认工具被正确调用
   - 确认参数格式正确

3. **检查邮件发送**：
   - 查看SMTP发送日志
   - 确认邮件实际发送

## 其他改进建议

### 1. 改进LLM提示词

在 `analyze_task` 的prompt中：
- 强调必需参数的重要性
- 提供更清晰的参数提取示例
- 要求LLM明确列出所有必需参数

### 2. 统一参数提取逻辑

- 将 `_extract_email_parameters` 方法提取为公共方法
- 在多个地方复用，避免重复代码

### 3. 添加参数验证中间件

- 在执行工具前统一验证参数
- 提供清晰的错误信息
- 支持参数自动补充

## 总结

**问题**：LLM参数提取不完整，导致 `to_emails` 参数缺失

**修复**：添加参数增强方法，使用正则表达式作为fallback，确保必需参数存在

**状态**：✅ 已修复，等待测试验证
