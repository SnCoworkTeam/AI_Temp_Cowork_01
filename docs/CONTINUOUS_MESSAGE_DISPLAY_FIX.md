# 连续消息显示修复

## 问题描述

用户反馈：两个问题之间的AI回复还是没有，要保证AI的回复也要连续，哪怕是错的。

**问题表现**：
- AI回复在错误时可能不显示
- 流式内容可能丢失
- 错误信息覆盖了之前的内容，而不是追加

## 修复方案

### 1. 改进错误处理（追加而非替换）

**修复前**：
```typescript
// 错误时直接替换整个消息内容
const errorMessage = `❌ 处理失败: ${error?.message}`
updateMessage(currentSessionId, aiMessageId, {
  content: errorMessage,  // ❌ 替换了之前的所有内容
  status: 'failed',
})
```

**修复后**：
```typescript
// 获取当前消息内容（保留之前的所有内容）
const currentMessages = messages.filter(m => m.id === aiMessageId)
const currentContent = currentMessages.length > 0 
  ? currentMessages[0].content 
  : aiMessageContent || '🤔 正在分析您的请求...'

// 追加错误信息，不替换
let finalContent = currentContent
const errorMessage = `❌ 处理失败: ${error?.message || '网络错误，请稍后重试'}`

if (!finalContent.includes(errorMessage)) {
  if (finalContent && finalContent !== '🤔 正在分析您的请求...' && !finalContent.endsWith('\n\n')) {
    finalContent += '\n\n'
  }
  finalContent += errorMessage
}

updateMessage(currentSessionId, aiMessageId, {
  content: finalContent,  // ✅ 保留之前的内容 + 错误信息
  status: 'sent',  // ✅ 标记为sent，确保显示
})
```

### 2. 改进流式错误事件处理

**修复前**：
```typescript
case 'error':
  const errorMsg = `\n\n❌ 错误: ${data.data?.error || '未知错误'}`
  if (!aiMessageContent.includes(errorMsg)) {
    aiMessageContent += errorMsg
  }
  break
```

**修复后**：
```typescript
case 'error':
  const errorMsg = data.data?.error || data.data?.message || '未知错误'
  // 检查是否已经包含这个错误信息（避免重复）
  if (!aiMessageContent.includes(errorMsg)) {
    // 如果当前内容不为空且不是初始状态，添加换行
    if (aiMessageContent && aiMessageContent !== '🤔 正在分析您的请求...' && !aiMessageContent.endsWith('\n\n')) {
      aiMessageContent += '\n\n'
    }
    aiMessageContent += `❌ 错误: ${errorMsg}`
  }
  // 确保消息状态更新为sent，即使有错误也要显示
  break
```

### 3. 改进complete事件处理

**修复前**：
```typescript
case 'complete':
  // 只检查是否有response，如果没有就不做任何处理
  if (data.data?.result?.response) {
    // ... 添加响应
  }
  break
```

**修复后**：
```typescript
case 'complete':
  let hasNewContent = false
  
  // 尝试添加最终响应
  if (data.data?.result?.response) {
    // ... 添加响应
    hasNewContent = true
  } else if (data.data?.result) {
    // ... 尝试从其他字段获取
    hasNewContent = true
  }
  
  // 如果complete事件没有提供新内容，但当前内容仍然是初始状态，至少保留步骤信息
  if (!hasNewContent && aiMessageContent === '🤔 正在分析您的请求...') {
    aiMessageContent = '🔄 处理完成'
  }
  
  break
```

### 4. 确保消息状态正确

**关键改进**：
- 错误时也标记为 `status: 'sent'`，而不是 `'failed'`
- 确保消息类型为 `'text'`，而不是 `'error'`
- 这样消息会正常显示在消息列表中

## 修改的文件

- `web-ui/src/components/ChatInterface.tsx`
  - `handleSendMessage` 方法：改进错误处理和流式事件处理

## 预期效果

1. **连续显示**：AI回复会连续显示，即使有错误也不会丢失
2. **内容保留**：错误信息会追加到之前的内容后面，而不是替换
3. **状态正确**：消息状态标记为 `sent`，确保显示在消息列表中
4. **无重复**：检查避免重复添加相同的内容

## 测试场景

### 场景1：正常流程
```
用户：发送邮件
AI：🔄 开始处理...
     📋 意图分析: 完成
     📋 任务分类: 完成
     邮件已发送成功
```
✅ 所有内容都应该连续显示

### 场景2：错误流程
```
用户：发送邮件
AI：🔄 开始处理...
     📋 意图分析: 完成
     📋 任务分类: 完成
     ❌ 错误: Missing required parameter: body
```
✅ 即使有错误，之前的步骤信息也应该保留

### 场景3：网络错误
```
用户：发送邮件
AI：🔄 开始处理...
     📋 意图分析: 完成
     
     ❌ 处理失败: 网络错误，请稍后重试
```
✅ 网络错误时，之前的内容也应该保留

## 注意事项

1. **消息状态**：错误时也使用 `status: 'sent'`，确保消息显示
2. **内容检查**：使用 `includes()` 检查避免重复添加
3. **换行处理**：确保在追加内容前添加适当的换行
4. **初始状态**：如果内容仍然是初始状态，至少显示"处理完成"


