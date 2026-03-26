/**
 * 聊天工具函数
 */
import { Message, ChatSession } from '@/types/chat'

const SESSIONS_KEY = 'chat_sessions'
const MESSAGES_KEY_PREFIX = 'chat_messages_'

/**
 * 安全的JSON序列化函数，移除循环引用和不可序列化的值
 */
function safeStringify(obj: any, space?: number): string {
  const seen = new WeakSet()
  
  return JSON.stringify(obj, (key, value) => {
    // 移除循环引用
    if (typeof value === 'object' && value !== null) {
      if (seen.has(value)) {
        return '[Circular]'
      }
      seen.add(value)
    }
    
    // 移除函数
    if (typeof value === 'function') {
      return undefined
    }
    
    // 移除DOM元素
    if (value instanceof HTMLElement || value instanceof Node) {
      return undefined
    }
    
    // 移除React Fiber节点
    if (value && typeof value === 'object' && value.constructor) {
      const constructorName = value.constructor.name
      if (constructorName === 'FiberNode' || 
          constructorName === 'Fiber' ||
          constructorName.includes('Fiber')) {
        return undefined
      }
    }
    
    // 移除其他不可序列化的对象
    if (value && typeof value === 'object') {
      // 检查是否有常见的React内部属性
      if (value.hasOwnProperty('__reactFiber') || 
          value.hasOwnProperty('__reactInternalInstance') ||
          value.hasOwnProperty('_owner') ||
          value.hasOwnProperty('_store')) {
        return undefined
      }
    }
    
    return value
  }, space)
}

/**
 * 清理会话对象，只保留可序列化的字段
 */
function cleanSession(session: ChatSession): ChatSession {
  // 确保title是字符串，如果它是对象则提取字符串表示或使用默认值
  let titleStr = ''
  if (session.title) {
    if (typeof session.title === 'string') {
      titleStr = session.title
    } else if (typeof session.title === 'object') {
      // 如果是对象，尝试提取有意义的字符串
      if ('title' in session.title && typeof session.title.title === 'string') {
        titleStr = session.title.title
      } else if ('name' in session.title && typeof session.title.name === 'string') {
        titleStr = session.title.name
      } else if ('content' in session.title && typeof session.title.content === 'string') {
        titleStr = session.title.content.substring(0, 50)
      } else {
        // 最后手段：使用JSON字符串的前50个字符
        try {
          titleStr = JSON.stringify(session.title).substring(0, 50)
        } catch {
          titleStr = '未命名会话'
        }
      }
    } else {
      titleStr = String(session.title)
    }
  }
  
  // 如果title为空，使用默认值
  if (!titleStr || titleStr.trim() === '') {
    titleStr = '未命名会话'
  }
  
  return {
    id: String(session.id || ''),
    title: titleStr,
    lastMessage: session.lastMessage ? String(session.lastMessage) : undefined,
    lastMessageTime: session.lastMessageTime ? Number(session.lastMessageTime) : undefined,
    unreadCount: Number(session.unreadCount || 0),
    createdAt: Number(session.createdAt || Date.now()),
  }
}

/**
 * 获取所有会话
 */
export function getSessions(): ChatSession[] {
  if (typeof window === 'undefined') return []
  
  const sessionsStr = localStorage.getItem(SESSIONS_KEY)
  if (!sessionsStr) return []
  
  try {
    return JSON.parse(sessionsStr) as ChatSession[]
  } catch {
    return []
  }
}

/**
 * 保存会话
 */
export function saveSession(session: ChatSession): void {
  if (typeof window === 'undefined') return
  
  // 清理会话对象，移除可能的循环引用
  const cleanSessionData = cleanSession(session)
  
  const sessions = getSessions()
  const index = sessions.findIndex(s => s.id === cleanSessionData.id)
  
  if (index >= 0) {
    sessions[index] = cleanSessionData
  } else {
    sessions.push(cleanSessionData)
  }
  
  // 按最后消息时间排序
  sessions.sort((a, b) => (b.lastMessageTime || 0) - (a.lastMessageTime || 0))
  
  // 清理所有会话对象
  const cleanedSessions = sessions.map(s => cleanSession(s))
  
  try {
    localStorage.setItem(SESSIONS_KEY, safeStringify(cleanedSessions))
  } catch (error) {
    console.error('Failed to save session:', error)
    // 如果仍然失败，使用更激进的清理方式
    const safeSessions = cleanedSessions.map(s => ({
      id: String(s.id),
      title: String(s.title),
      lastMessage: s.lastMessage ? String(s.lastMessage).substring(0, 100) : undefined,
      lastMessageTime: s.lastMessageTime ? Number(s.lastMessageTime) : undefined,
      unreadCount: Number(s.unreadCount || 0),
      createdAt: Number(s.createdAt || Date.now()),
    }))
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(safeSessions))
  }
}

/**
 * 删除会话
 */
export function deleteSession(sessionId: string): void {
  if (typeof window === 'undefined') return
  
  const sessions = getSessions().filter(s => s.id !== sessionId)
  // 清理所有会话对象
  const cleanedSessions = sessions.map(s => cleanSession(s))
  
  try {
    localStorage.setItem(SESSIONS_KEY, safeStringify(cleanedSessions))
  } catch (error) {
    console.error('Failed to delete session:', error)
    // 降级方案
    const safeSessions = cleanedSessions.map(s => ({
      id: String(s.id),
      title: String(s.title),
      lastMessage: s.lastMessage ? String(s.lastMessage).substring(0, 100) : undefined,
      lastMessageTime: s.lastMessageTime ? Number(s.lastMessageTime) : undefined,
      unreadCount: Number(s.unreadCount || 0),
      createdAt: Number(s.createdAt || Date.now()),
    }))
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(safeSessions))
  }
  
  // 删除会话消息
  localStorage.removeItem(`${MESSAGES_KEY_PREFIX}${sessionId}`)
}

/**
 * 获取会话消息
 */
export function getSessionMessages(sessionId: string): Message[] {
  if (typeof window === 'undefined') return []
  
  const messagesStr = localStorage.getItem(`${MESSAGES_KEY_PREFIX}${sessionId}`)
  if (!messagesStr) return []
  
  try {
    return JSON.parse(messagesStr) as Message[]
  } catch {
    return []
  }
}

/**
 * 保存消息
 */
export function saveMessage(sessionId: string, message: Message): void {
  if (typeof window === 'undefined') return
  
  // 清理消息对象，移除可能的循环引用
  let cleanMetadata: Message['metadata'] = undefined
  if (message.metadata) {
    try {
      // 使用safeStringify清理metadata，然后解析回来
      const cleaned = safeStringify(message.metadata)
      cleanMetadata = JSON.parse(cleaned)
    } catch (error) {
      console.warn('Failed to clean message metadata:', error)
      // 如果清理失败，尝试手动清理
      cleanMetadata = Object.fromEntries(
        Object.entries(message.metadata).filter(([k, v]) => 
          typeof v !== 'function' && 
          !(v instanceof HTMLElement) &&
          !(v instanceof Node) &&
          (v === null || typeof v !== 'object' || !v.constructor || !v.constructor.name.includes('Fiber'))
        )
      ) as Message['metadata']
    }
  }
  
  const cleanMessage: Message = {
    id: String(message.id || ''),
    type: message.type,
    content: String(message.content || ''),
    sender: String(message.sender || ''),
    senderId: String(message.senderId || ''),
    timestamp: Number(message.timestamp || Date.now()),
    status: message.status,
    metadata: cleanMetadata,
  }
  
  const messages = getSessionMessages(sessionId)
  messages.push(cleanMessage)
  
  // 清理所有消息对象
  const cleanMessages = messages.map(msg => ({
    id: String(msg.id),
    type: msg.type,
    content: String(msg.content || ''),
    sender: String(msg.sender || ''),
    senderId: String(msg.senderId || ''),
    timestamp: Number(msg.timestamp || 0),
    status: msg.status,
    metadata: msg.metadata ? (() => {
      try {
        return JSON.parse(safeStringify(msg.metadata))
      } catch {
        return undefined
      }
    })() : undefined,
  }))
  
  try {
    localStorage.setItem(`${MESSAGES_KEY_PREFIX}${sessionId}`, safeStringify(cleanMessages))
  } catch (error) {
    console.error('Failed to save message:', error)
    // 如果仍然失败，尝试更激进的清理
    // 注意：不截断内容，确保完整的执行过程被保存
    // localStorage通常有5-10MB的限制，单个消息不应该超过这个限制
    const safeMessages = cleanMessages.map(msg => ({
      id: msg.id,
      type: msg.type,
      content: msg.content, // 不截断内容，保留完整的执行过程
      sender: msg.sender,
      senderId: msg.senderId,
      timestamp: msg.timestamp,
      status: msg.status,
      metadata: msg.metadata ? Object.fromEntries(
        Object.entries(msg.metadata).filter(([k, v]) => 
          typeof v !== 'function' && 
          !(v instanceof HTMLElement) &&
          !(v instanceof Node)
        )
      ) : undefined,
    }))
    try {
      localStorage.setItem(`${MESSAGES_KEY_PREFIX}${sessionId}`, JSON.stringify(safeMessages))
    } catch (storageError) {
      // 如果仍然失败，可能是内容太大，尝试压缩或分片
      console.error('Failed to save message even after cleanup:', storageError)
      // 作为最后手段，只保存最近的消息（保留最后200条，确保长期上下文记忆）
      const recentMessages = safeMessages.slice(-200)
      localStorage.setItem(`${MESSAGES_KEY_PREFIX}${sessionId}`, JSON.stringify(recentMessages))
    }
  }
  
  // 更新会话的最后消息
  const session = getSessions().find(s => s.id === sessionId)
  if (session) {
    session.lastMessage = message.content.substring(0, 50)
    session.lastMessageTime = message.timestamp
    saveSession(session)
  }
}

/**
 * 更新消息
 */
export function updateMessage(sessionId: string, messageId: string, updates: Partial<Message>): void {
  if (typeof window === 'undefined') return
  
  const messages = getSessionMessages(sessionId)
  const index = messages.findIndex(m => m.id === messageId)
  
  if (index >= 0) {
    messages[index] = { ...messages[index], ...updates }
    // 清理消息对象
    const cleanMessages = messages.map(msg => ({
      id: msg.id,
      type: msg.type,
      content: String(msg.content || ''),
      sender: String(msg.sender || ''),
      senderId: String(msg.senderId || ''),
      timestamp: Number(msg.timestamp || 0),
      status: msg.status,
      metadata: msg.metadata ? (() => {
        try {
          const cleaned = safeStringify(msg.metadata)
          return cleaned ? JSON.parse(cleaned) : undefined
        } catch {
          return undefined
        }
      })() : undefined,
    }))
    
    try {
      localStorage.setItem(`${MESSAGES_KEY_PREFIX}${sessionId}`, safeStringify(cleanMessages))
    } catch (error) {
      console.error('Failed to update message:', error)
      localStorage.setItem(`${MESSAGES_KEY_PREFIX}${sessionId}`, JSON.stringify(cleanMessages))
    }
  }
}

/**
 * 删除消息
 */
export function deleteMessage(sessionId: string, messageId: string): void {
  if (typeof window === 'undefined') return
  
  const messages = getSessionMessages(sessionId).filter(m => m.id !== messageId)
  // 清理消息对象
  const cleanMessages = messages.map(msg => ({
    id: msg.id,
    type: msg.type,
    content: String(msg.content || ''),
    sender: String(msg.sender || ''),
    senderId: String(msg.senderId || ''),
    timestamp: Number(msg.timestamp || 0),
    status: msg.status,
    metadata: msg.metadata ? (() => {
      try {
        const cleaned = safeStringify(msg.metadata)
        return cleaned ? JSON.parse(cleaned) : undefined
      } catch {
        return undefined
      }
    })() : undefined,
  }))
  
  try {
    localStorage.setItem(`${MESSAGES_KEY_PREFIX}${sessionId}`, safeStringify(cleanMessages))
  } catch (error) {
    console.error('Failed to delete message:', error)
    localStorage.setItem(`${MESSAGES_KEY_PREFIX}${sessionId}`, JSON.stringify(cleanMessages))
  }
}

/**
 * 创建新会话
 */
export function createSession(title: string): ChatSession {
  const session: ChatSession = {
    id: `session_${Date.now()}`,
    title,
    unreadCount: 0,
    createdAt: Date.now(),
  }
  
  saveSession(session)
  return session
}

/**
 * 格式化时间
 */
export function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  
  const diffTime = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    // 今天
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    // 昨天
    return `昨天 ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  } else if (diffDays < 7) {
    // 一周内
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return `${weekdays[date.getDay()]} ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  } else {
    // 更早
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + 
           ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
}

/**
 * 复制到剪贴板
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('Failed to copy:', error)
    // 降级方案
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      document.body.removeChild(textArea)
      return true
    } catch {
      document.body.removeChild(textArea)
      return false
    }
  }
}









