# 参数验证和消息显示修复

## 问题描述

### 问题1：参数类型验证错误
```
Parameter 'to_emails' must be of type '['string', 'array']', got 'list'
```

**根本原因**：
- `to_emails` 参数的JSON Schema定义为 `"type": ["string", "array"]`（联合类型）
- 但 `_validate_parameter_value` 方法只支持单个类型，不支持联合类型
- 当传入列表时，验证失败

### 问题2：AI回复丢失
- 流式内容没有正确累积
- 消息更新可能没有触发React重新渲染
- complete事件的内容可能没有正确追加

## 修复方案

### 1. 修复参数类型验证（支持联合类型）

**修复前**：
```python
expected_type = schema.get("type")
if expected_type:
    type_valid = False
    if expected_type == "string" and isinstance(value, str):
        type_valid = True
    elif expected_type == "array" and isinstance(value, list):
        type_valid = True
    # ... 只支持单个类型
```

**修复后**：
```python
expected_type = schema.get("type")
if expected_type:
    type_valid = False
    
    # 处理联合类型（数组形式）
    allowed_types = expected_type if isinstance(expected_type, list) else [expected_type]
    
    for allowed_type in allowed_types:
        if allowed_type == "string" and isinstance(value, str):
            type_valid = True
            break
        elif allowed_type == "array" and isinstance(value, list):
            type_valid = True
            break
        # ... 支持多个类型
```

**效果**：
- 现在可以正确处理 `"type": ["string", "array"]`
- 列表类型会被正确识别为 `array` 类型

### 2. 改进流式消息处理

#### 2.1 立即添加初始消息到React state

**修复前**：
```typescript
if (currentSessionId) {
  saveMessage(currentSessionId, aiMessage)
  switchSession(currentSessionId)  // 可能不会立即更新UI
}
```

**修复后**：
```typescript
if (currentSessionId) {
  saveMessage(currentSessionId, aiMessage)
  // 立即添加到React state，确保消息显示
  setMessages(prev => {
    if (prev.find(m => m.id === aiMessageId)) {
      return prev  // 避免重复
    }
    return [...prev, aiMessage]
  })
  switchSession(currentSessionId)
}
```

#### 2.2 改进chunk处理（添加日志）

```typescript
case 'chunk':
  if (data.data?.chunk) {
    aiMessageContent += data.data.chunk
    console.log('[Chat] Appended chunk, current content length:', aiMessageContent.length)
  }
  break
```

#### 2.3 改进complete事件处理（更宽松的检查）

**修复前**：
```typescript
const responseKey = finalResponse.substring(0, Math.min(50, finalResponse.length))
if (finalResponse && !aiMessageContent.includes(responseKey)) {
  // 可能因为内容太长而检查失败
}
```

**修复后**：
```typescript
// 检查开头和结尾，更准确
const responseStart = finalResponse.substring(0, Math.min(100, finalResponse.length))
const responseEnd = finalResponse.length > 100 ? finalResponse.substring(finalResponse.length - 100) : ''
const alreadyIncluded = responseStart && aiMessageContent.includes(responseStart) && 
                      (responseEnd ? aiMessageContent.includes(responseEnd) : true)

if (finalResponse && !alreadyIncluded) {
  aiMessageContent += finalResponse
  console.log('[Chat] Appended final response, new content length:', aiMessageContent.length)
}
```

#### 2.4 改进消息更新逻辑

**修复前**：
```typescript
setMessages(prev => {
  const updated = prev.map(msg => 
    msg.id === aiMessageId 
      ? { ...msg, content: aiMessageContent }
      : msg
  )
  // 如果消息不存在，添加它
  if (!updated.find(m => m.id === aiMessageId)) {
    updated.push({...})
  }
  return updated
})
```

**修复后**：
```typescript
setMessages(prev => {
  const existingIndex = prev.findIndex(m => m.id === aiMessageId)
  
  if (existingIndex >= 0) {
    // 消息已存在，更新它（使用展开运算符创建新数组，触发React更新）
    const updated = [...prev]
    updated[existingIndex] = {
      ...updated[existingIndex],
      content: aiMessageContent,  // 直接使用最新的完整内容
      status: data.type === 'complete' || data.type === 'error' ? 'sent' : 'sending'
    }
    console.log('[Chat] Updated existing message, content length:', aiMessageContent.length)
    return updated
  } else {
    // 消息不存在，添加它
    const newMessage = {...}
    console.log('[Chat] Added new message, content length:', aiMessageContent.length)
    return [...prev, newMessage]
  }
})
```

## 修改的文件

- `mcp-gateway/src/tools/tool_registry.py`
  - `_validate_parameter_value` 方法：支持联合类型验证

- `web-ui/src/components/ChatInterface.tsx`
  - `handleSendMessage` 方法：改进流式消息处理和React state更新

## 预期效果

1. **参数验证通过**：`to_emails` 参数无论是字符串还是列表都能通过验证
2. **消息连续显示**：AI回复会连续显示，不会丢失任何内容
3. **实时更新**：每次收到chunk都会立即更新UI
4. **错误保留**：即使有错误，之前的内容也会保留

## 测试场景

### 场景1：正常流式响应
```
用户：发送邮件
AI：🔄 开始处理...
     📋 意图分析: 完成
     📋 任务分类: 完成
     邮件已发送成功
```
✅ 所有内容都应该连续显示

### 场景2：错误响应
```
用户：发送邮件
AI：🔄 开始处理...
     📋 意图分析: 完成
     📋 任务分类: 完成
     ❌ 错误: Missing required parameter: body
```
✅ 即使有错误，之前的步骤信息也应该保留

### 场景3：参数类型
```
to_emails = ["yubin.liu@pcitc.com"]  # 列表
to_emails = "yubin.liu@pcitc.com"     # 字符串
```
✅ 两种类型都应该通过验证

## 调试日志

添加了详细的日志，方便调试：
- `[Chat] Appended chunk, current content length: X`
- `[Chat] Appended final response, new content length: X`
- `[Chat] Updated existing message, content length: X`
- `[Chat] Added new message, content length: X`

可以通过浏览器控制台查看这些日志，确认内容是否正确累积。


