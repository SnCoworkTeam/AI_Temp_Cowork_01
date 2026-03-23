# 消息持久化修复

## 问题描述

用户反馈：连续两次问题之间的内容会消失，刷新页面以后又有了。

**根本原因**：
- 消息确实被保存到了localStorage（刷新后还在）
- 但是在连续发送两次消息时，`useEffect` 会完全替换本地的 `messages` state
- 这导致正在流式更新的第一条AI回复被覆盖

**问题流程**：
1. 用户发送第一条消息，AI开始流式回复
2. 用户发送第二条消息，`sendMessage` 被调用
3. `sendMessage` 更新 `messagesFromHook`（在 useChat hook 中）
4. 触发 `useEffect(() => { setMessages(messagesFromHook) }, [messagesFromHook])`
5. 这会**完全替换**本地正在流式更新的消息，导致第一条AI回复丢失

## 修复方案

### 1. 智能消息合并策略

**修复前**：
```typescript
useEffect(() => {
  setMessages(messagesFromHook)  // ❌ 完全替换，丢失流式更新中的消息
}, [messagesFromHook])
```

**修复后**：
```typescript
// 跟踪正在流式更新的消息ID
const streamingMessageIdsRef = useRef<Set<string>>(new Set())

useEffect(() => {
  setMessages(prev => {
    const streamingIds = streamingMessageIdsRef.current
    
    if (streamingIds.size === 0) {
      // 没有流式更新，直接使用hook的消息
      return messagesFromHook
    }
    
    // 有流式更新，需要智能合并
    const merged: Message[] = []
    const hookMessageMap = new Map(messagesFromHook.map(m => [m.id, m]))
    const prevMessageMap = new Map(prev.map(m => [m.id, m]))
    
    // 合并策略：
    // 1. 对于流式更新中的消息，使用本地state的最新内容
    // 2. 对于其他消息，使用hook的消息（可能更新了状态等）
    // 3. 保持消息顺序（按timestamp排序）
    
    const allMessageIds = new Set([
      ...messagesFromHook.map(m => m.id),
      ...prev.map(m => m.id)
    ])
    
    const sortedIds = Array.from(allMessageIds).sort((a, b) => {
      const msgA = prevMessageMap.get(a) || hookMessageMap.get(a)
      const msgB = prevMessageMap.get(b) || hookMessageMap.get(b)
      return (msgA?.timestamp || 0) - (msgB?.timestamp || 0)
    })
    
    for (const id of sortedIds) {
      if (streamingIds.has(id)) {
        // 流式更新中的消息，使用本地state的最新内容
        const localMsg = prevMessageMap.get(id)
        if (localMsg) {
          merged.push(localMsg)
        }
      } else {
        // 其他消息，使用hook的消息
        const hookMsg = hookMessageMap.get(id)
        if (hookMsg) {
          merged.push(hookMsg)
        }
      }
    }
    
    return merged
  })
}, [messagesFromHook])
```

### 2. 流式更新状态跟踪

**在开始流式更新时**：
```typescript
// 标记为流式更新中
streamingMessageIdsRef.current.add(aiMessageId)
```

**在流式更新完成时**：
```typescript
case 'complete':
  // 标记流式更新完成
  streamingMessageIdsRef.current.delete(aiMessageId)
  break

case 'error':
  // 标记流式更新完成（即使有错误）
  streamingMessageIdsRef.current.delete(aiMessageId)
  break
```

**在错误处理中**：
```typescript
catch (error) {
  // 标记流式更新完成
  streamingMessageIdsRef.current.delete(aiMessageId)
  // ... 错误处理
}
```

## 修改的文件

- `web-ui/src/components/ChatInterface.tsx`
  - 添加 `streamingMessageIdsRef` 来跟踪流式更新中的消息
  - 改进 `useEffect` 的消息同步逻辑，使用智能合并策略
  - 在流式更新开始和结束时更新 `streamingMessageIdsRef`

## 预期效果

1. **消息不丢失**：流式更新中的消息不会被hook的消息覆盖
2. **状态同步**：非流式更新的消息仍然会从hook同步（如状态更新）
3. **顺序保持**：消息按timestamp排序，保持正确的显示顺序
4. **性能优化**：只在有流式更新时才进行合并，否则直接使用hook的消息

## 测试场景

### 场景1：连续发送两条消息
```
1. 用户：发送邮件
   AI：🔄 开始处理...（流式更新中）

2. 用户：查询销售订单
   AI：🔄 开始处理...（流式更新中）

预期：
- 第一条AI回复继续显示，不会被覆盖
- 第二条AI回复正常显示
- 两条回复都完整显示
```

### 场景2：快速连续发送
```
1. 用户：问题1
   AI：回复1（流式更新中）

2. 用户：问题2（在回复1完成前）
   AI：回复2（流式更新中）

预期：
- 回复1继续流式更新，不会被中断
- 回复2正常开始流式更新
- 两条回复都完整显示
```

### 场景3：刷新页面
```
1. 发送多条消息
2. 刷新页面

预期：
- 所有消息都从localStorage加载
- 消息顺序正确
- 所有内容完整显示
```

## 技术细节

### 合并策略

1. **流式更新中的消息**：使用本地state的最新内容（包含实时流式更新）
2. **其他消息**：使用hook的消息（可能包含状态更新等）
3. **消息顺序**：按timestamp排序，确保显示顺序正确

### 性能考虑

- 只在有流式更新时才进行合并（`streamingIds.size > 0`）
- 没有流式更新时，直接使用hook的消息（`return messagesFromHook`）
- 使用Map进行快速查找，避免O(n²)复杂度

### 内存管理

- 使用 `useRef` 存储流式更新中的消息ID集合
- 在流式更新完成时及时清理（`delete(aiMessageId)`）
- 避免内存泄漏


