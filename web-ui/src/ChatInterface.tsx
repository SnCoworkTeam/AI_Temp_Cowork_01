'use client'

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useChat } from '@/hooks/useChat'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { ChatSidebar } from './ChatSidebar'
import { AuthGuard } from './AuthGuard'
import { KnowledgeSidebar } from './ChatInterface/index'
import { DynamicWorkflowDisplay } from './DynamicWorkflowDisplay'
import { knowledgeApi } from '@/lib/api/knowledge'
import { Message } from '@/types/chat'
import { listWorkflows, executeWorkflowById, WorkflowListItem } from '@/lib/api/workflow'
import { getSessionMessages, saveMessage, updateMessage } from '@/lib/chat'
import { executeDAGTask, getDAGExecutionStatus, DAGExecutionRequest } from '@/lib/api/dag'
import { agentChat, IntelligentChatRequest } from '@/lib/api/chat'
import { executeDynamicWorkflow, WorkflowChunk } from '@/lib/api/dynamic-workflow'
import '@/app/message-styles.css'

interface ChatInterfaceProps {
  sessionId?: string
}

export function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const { user } = useAuth()
  const {
    sessions,
    currentSessionId,
    messages: messagesFromHook,
    sending,
    messagesEndRef,
    sendMessage,
    createNewSession,
    switchSession,
    removeSession,
    resendMessage,
    removeMessage,
    loadSessions,
  } = useChat({ sessionId, autoScroll: true })

  // 维护本地消息state，用于实时流式更新
  // 初始化时，如果hook的消息为空，尝试从localStorage加载
  const [messages, setMessages] = useState<Message[]>(() => {
    if (messagesFromHook.length > 0) {
      return messagesFromHook
    }
    // 如果hook消息为空，尝试从localStorage加载
    if (currentSessionId) {
      try {
        const loadedMessages = getSessionMessages(currentSessionId)
        if (loadedMessages.length > 0) {
          return loadedMessages
        }
      } catch (e) {
        console.warn('[ChatInterface] Failed to load initial messages:', e)
      }
    }
    return messagesFromHook
  })
  // 跟踪正在流式更新的消息ID，避免被hook的消息覆盖
  const streamingMessageIdsRef = useRef<Set<string>>(new Set())

  // 初始化时，确保从localStorage加载消息
  useEffect(() => {
    // 组件挂载时，立即加载当前会话的消息
    if (currentSessionId) {
      try {
        const loadedMessages = getSessionMessages(currentSessionId)
        if (loadedMessages.length > 0) {
          setMessages(loadedMessages)
        }
      } catch (e) {
        console.warn('[ChatInterface] Failed to load messages on mount:', e)
      }
    }
  }, []) // 只在组件挂载时执行一次
  
  // 当currentSessionId变化时，重新加载消息
  useEffect(() => {
    if (currentSessionId) {
      try {
        const loadedMessages = getSessionMessages(currentSessionId)
        setMessages(loadedMessages)
      } catch (e) {
        console.warn('[ChatInterface] Failed to load messages on session change:', e)
      }
    }
  }, [currentSessionId])

  // 当hook中的消息变化时，智能合并到本地state（保留流式更新中的消息）
  // 同时确保从localStorage加载的消息不会被覆盖
  useEffect(() => {
    setMessages(prev => {
      // 如果有正在流式更新的消息，保留它们的最新内容
      const streamingIds = streamingMessageIdsRef.current
      
      // 如果hook的消息为空，但本地有消息，保留本地消息（可能是刚保存但还没从hook加载）
      if (messagesFromHook.length === 0 && prev.length > 0 && streamingIds.size === 0) {
        // 尝试从localStorage重新加载
        if (currentSessionId) {
          try {
            const loadedMessages = getSessionMessages(currentSessionId)
            if (loadedMessages.length > 0) {
              return loadedMessages
            }
          } catch (e) {
            console.warn('[ChatInterface] Failed to reload messages from localStorage:', e)
          }
        }
        // 如果加载失败，保留本地消息
        return prev
      }
      
      if (streamingIds.size === 0) {
        // 没有流式更新，直接使用hook的消息（但确保不为空）
        if (messagesFromHook.length > 0) {
          return messagesFromHook
        }
        // 如果hook消息为空，尝试从localStorage加载
        if (currentSessionId) {
          try {
            const loadedMessages = getSessionMessages(currentSessionId)
            if (loadedMessages.length > 0) {
              return loadedMessages
            }
          } catch (e) {
            console.warn('[ChatInterface] Failed to reload messages from localStorage:', e)
          }
        }
        return prev.length > 0 ? prev : messagesFromHook
      }
      
      // 有流式更新，需要合并
      const merged: Message[] = []
      const hookMessageMap = new Map(messagesFromHook.map(m => [m.id, m]))
      const prevMessageMap = new Map(prev.map(m => [m.id, m]))
      
      // 合并策略：
      // 1. 对于流式更新中的消息，使用本地state的最新内容
      // 2. 对于其他消息，使用hook的消息（可能更新了状态等）
      // 3. 保持消息顺序（按timestamp排序）
      // 4. 确保所有消息都被保留，不会丢失
      
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
          // 其他消息，使用hook的消息（优先）或本地消息（如果hook中没有）
          const hookMsg = hookMessageMap.get(id)
          const localMsg = prevMessageMap.get(id)
          if (hookMsg) {
            merged.push(hookMsg)
          } else if (localMsg) {
            // 如果hook中没有但本地有，保留本地消息（可能是刚保存但还没从hook加载）
            merged.push(localMsg)
          }
        }
      }
      
      return merged
    })
  }, [messagesFromHook, currentSessionId])

  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [knowledgeSidebarOpen, setKnowledgeSidebarOpen] = useState(false)
  const [knowledgeQuery, setKnowledgeQuery] = useState<string>('')
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([])
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null)
  const [workflowExecutions, setWorkflowExecutions] = useState<Map<string, any>>(new Map())
  const [showWorkflowInput, setShowWorkflowInput] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [useDynamicWorkflow, setUseDynamicWorkflow] = useState(true) // 默认使用动态工作流
  const [workflowChunks, setWorkflowChunks] = useState<Map<string, WorkflowChunk[]>>(new Map())
  const chatUpdateTimerRef = useRef<NodeJS.Timeout | null>(null)
  
  // 思考内容显示开关（全局控制）
  const [showThinkingContent, setShowThinkingContent] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('chat_show_thinking_content')
      return saved !== null ? saved === 'true' : true // 默认显示
    }
    return true
  })
  
  // 保存用户偏好
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('chat_show_thinking_content', String(showThinkingContent))
    }
  }, [showThinkingContent])

  // 加载工作流列表
  useEffect(() => {
    loadWorkflows()
  }, [])

  const loadWorkflows = async () => {
    try {
      const response = await listWorkflows()
      setWorkflows(response.workflows || [])
    } catch (error: any) {
      // 404错误时静默处理，不显示错误日志
      if (error?.statusCode !== 404 && error?.status !== 404) {
        console.error('Failed to load workflows:', error)
      }
      // 设置空列表，避免UI错误
      setWorkflows([])
    }
  }

  const handleSend = async (content: string) => {
    if (!user) return
    
    // 保留命令前缀支持（向后兼容），但优先使用智能路由
    // 如果用户明确使用命令前缀，则执行命令逻辑
    if (content.startsWith('/workflow ') || content.startsWith('/wf ')) {
      const workflowNameOrId = content.replace(/^\/workflow\s+|\/wf\s+/, '').trim()
      
      // 先发送用户消息
      sendMessage(content, user.user_id, user.username)
      
      // 查找工作流
      const workflow = workflows.find(
        w => w.workflow_id === workflowNameOrId || 
             w.name === workflowNameOrId ||
             w.name.toLowerCase().includes(workflowNameOrId.toLowerCase())
      )

      if (workflow) {
        setCurrentWorkflowId(workflow.workflow_id)
        setShowWorkflowInput(true)
      } else {
        const availableWorkflows = workflows.slice(0, 5)
          .map(w => `- ${w.name} (ID: ${w.workflow_id.substring(0, 8)}...)`)
          .join('\n')
        sendMessage(
          `❌ 未找到工作流: ${workflowNameOrId}\n\n可用工作流:\n${availableWorkflows || '暂无可用工作流'}`,
          'system',
          '系统'
        )
      }
      return
    }

    // 检查是否是知识库搜索命令（保留向后兼容）
    if (content.startsWith('/kb ') || content.startsWith('/knowledge ')) {
      const query = content.replace(/^\/kb\s+|\/knowledge\s+/, '')
      setKnowledgeQuery(query)
      setKnowledgeSidebarOpen(true)
      
      // 同时执行搜索并在聊天中显示
      try {
        const searchResponse = await knowledgeApi.semanticSearch(query, 5)
        const aiResponse = `基于知识库搜索"${query}"的结果:\n\n${searchResponse.results
          .slice(0, 3)
          .map((r, i) => `${i + 1}. ${r.content.substring(0, 200)}...`)
          .join('\n\n')}`
        
        sendMessage(content, user.user_id, user.username)
        sendMessage(aiResponse, 'ai', 'AI助手')
      } catch (error) {
        console.error('Knowledge search failed:', error)
        sendMessage(content, user.user_id, user.username)
      }
      return
    }

    // 使用智能路由处理所有消息（包括原来的/dag命令）
    // 先发送用户消息
    sendMessage(content, user.user_id, user.username)
    
    // 如果启用动态工作流，使用动态工作流执行
    if (useDynamicWorkflow) {
      await handleDynamicWorkflow(content, user)
      return
    }
    
    // 创建AI回复消息（用于流式更新）- 移到try块外，确保catch块可以访问
    const aiMessageId = `ai-${Date.now()}`
    let aiMessageContent = '🤔 正在分析您的请求...'
    let currentProgress = 0
    
    try {
      
      const aiMessage: Message = {
        id: aiMessageId,
        type: 'text',
        content: aiMessageContent,
        sender: 'AI助手',
        senderId: 'ai',
        timestamp: Date.now(),
        status: 'sending',
      }
      
      // 标记为流式更新中
      streamingMessageIdsRef.current.add(aiMessageId)
      
      // 使用sendMessage添加初始消息
      // 然后通过updateMessage实时更新
      if (currentSessionId) {
        saveMessage(currentSessionId, aiMessage)
        // 立即添加到React state，确保消息显示
        setMessages(prev => {
          // 检查是否已存在，避免重复
          if (prev.find(m => m.id === aiMessageId)) {
            return prev
          }
          return [...prev, aiMessage]
        })
        // 触发消息列表更新
        switchSession(currentSessionId)
      }

      // 构建对话历史（最近20条消息，保持更长的上下文记忆）
      const recentMessages = messages
        .filter(m => m.type === 'text' && m.senderId !== 'system')
        .slice(-20)  // 增加到20条，保持更长的对话上下文
        .map(m => ({
          role: m.senderId === user.user_id ? 'user' : 'assistant',
          content: m.content,
        }))

      // 构建智能聊天请求
      const chatRequest = {
        message: content,
        conversation_history: recentMessages,
        user_context: {
          user_id: user.user_id,
          username: user.username,
        },
      }

      // 使用流式请求
      const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080'
      const requestUrl = `${API_GATEWAY_URL}/api/chat/intelligent/stream`
      
      console.log('[Chat] Sending request to:', requestUrl)
      console.log('[Chat] Request body:', chatRequest)
      
      let response: Response
      try {
        response = await fetch(requestUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
          },
          body: JSON.stringify(chatRequest),
        })
      } catch (fetchError: any) {
        console.error('[Chat] Fetch error:', fetchError)
        throw new Error(`网络请求失败: ${fetchError?.message || '无法连接到服务器'}`)
      }

      console.log('[Chat] Response status:', response.status, response.statusText)
      console.log('[Chat] Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const errorText = await response.text().catch(() => '')
        console.error('[Chat] Response error:', response.status, errorText)
        throw new Error(`HTTP错误! 状态: ${response.status}, 详情: ${errorText || response.statusText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      // 读取流式数据
      let buffer = ''
      console.log('[Chat] Starting to read stream...')
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          console.log('[Chat] Stream reading done')
          break
        }

        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk
        console.log('[Chat] Received chunk:', chunk.substring(0, 100) + (chunk.length > 100 ? '...' : ''))
        
        // 处理完整的行（SSE格式：data: {...}\n\n）
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留最后一个不完整的行
        
        for (const line of lines) {
          if (line.trim() === '') continue // 跳过空行
          
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.substring(6)
              console.log('[Chat] Parsing SSE data:', jsonStr.substring(0, 200))
              const data = JSON.parse(jsonStr)
              console.log('[Chat] Parsed data type:', data.type)
              
              // 处理不同类型的流式消息
              switch (data.type) {
                case 'start':
                  // 只在第一次收到start时初始化，后续不覆盖
                  if (!aiMessageContent || aiMessageContent === '🤔 正在分析您的请求...') {
                    aiMessageContent = '🔄 开始处理...\n\n'
                  }
                  break
                  
                case 'step':
                  // DeepSeek风格：只显示文字描述，不显示步骤、意图分类等
                  if (data.data?.description || data.data?.message) {
                    const description = data.data.description || data.data.message
                    // 检查是否已经包含这个描述，避免重复
                    if (description && !aiMessageContent.includes(description)) {
                      if (aiMessageContent && !aiMessageContent.endsWith('\n\n')) {
                        aiMessageContent += '\n'
                      }
                      aiMessageContent += description
                    }
                  }
                  currentProgress = data.progress || currentProgress
                  break
                  
                case 'chunk':
                  if (data.data?.chunk) {
                    // 直接追加chunk内容，确保不丢失任何内容
                    // 不进行任何检查，直接追加，因为chunk是流式的，不应该重复检查
                    aiMessageContent += data.data.chunk
                    console.log('[Chat] Appended chunk, current content length:', aiMessageContent.length)
                  }
                  currentProgress = data.progress || currentProgress
                  break
                  
                case 'progress':
                  currentProgress = data.progress || currentProgress
                  break
                  
                case 'complete':
                  // 保留所有之前的流式内容（包括所有步骤信息），只在最后添加最终响应（如果还没有）
                  console.log('[Chat] Complete event received, current content length:', aiMessageContent.length)
                  console.log('[Chat] Complete data:', JSON.stringify(data.data).substring(0, 200))
                  
                  // 保存当前内容（包含所有步骤信息）的备份，防止被覆盖
                  const contentBeforeComplete = aiMessageContent
                  
                  let hasNewContent = false
                  
                  if (data.data?.result?.response) {
                    const finalResponse = data.data.result.response
                    console.log('[Chat] Final response length:', finalResponse.length)
                    // 检查最终响应是否已经在内容中（避免重复）
                    // 使用更宽松的检查：如果响应很长，只检查开头和结尾
                    const responseStart = finalResponse.substring(0, Math.min(100, finalResponse.length))
                    const responseEnd = finalResponse.length > 100 ? finalResponse.substring(finalResponse.length - 100) : ''
                    
                    // 检查是否已经包含（检查开头和结尾，更准确）
                    const alreadyIncluded = responseStart && aiMessageContent.includes(responseStart) && 
                                          (responseEnd ? aiMessageContent.includes(responseEnd) : true)
                    
                    if (finalResponse && !alreadyIncluded) {
                      // 如果当前内容以步骤信息结尾，添加换行
                      if (!aiMessageContent.endsWith('\n\n') && !aiMessageContent.endsWith('\n')) {
                        aiMessageContent += '\n\n'
                      }
                      // 追加最终响应，但保留所有之前的步骤信息
                      aiMessageContent += finalResponse
                      hasNewContent = true
                      console.log('[Chat] Appended final response, new content length:', aiMessageContent.length)
                    } else {
                      console.log('[Chat] Final response already included, skipping')
                    }
                  } else if (data.data?.result) {
                    // 如果没有response，检查raw_result中是否有output
                    const result = data.data.result
                    const rawResult = result.raw_result || {}
                    const output = rawResult.output || rawResult.response || rawResult.result
                    if (output && typeof output === 'string') {
                      console.log('[Chat] Output found, length:', output.length)
                      // 检查输出是否已经在内容中（使用更宽松的检查）
                      const outputStart = output.substring(0, Math.min(100, output.length))
                      const outputEnd = output.length > 100 ? output.substring(output.length - 100) : ''
                      const alreadyIncluded = outputStart && aiMessageContent.includes(outputStart) && 
                                            (outputEnd ? aiMessageContent.includes(outputEnd) : true)
                      
                      if (!alreadyIncluded) {
                        if (!aiMessageContent.endsWith('\n\n') && !aiMessageContent.endsWith('\n')) {
                          aiMessageContent += '\n\n'
                        }
                        // 追加输出，但保留所有之前的步骤信息
                        aiMessageContent += output
                        hasNewContent = true
                        console.log('[Chat] Appended output, new content length:', aiMessageContent.length)
                      } else {
                        console.log('[Chat] Output already included, skipping')
                      }
                    }
                  }
                  
                  // 如果complete事件没有提供新内容，但当前内容仍然是初始状态，至少保留步骤信息
                  if (!hasNewContent && aiMessageContent === '🤔 正在分析您的请求...') {
                    aiMessageContent = '🔄 处理完成'
                    console.log('[Chat] No new content, set to default completion message')
                  }
                  
                  // 确保内容包含所有步骤信息（如果被意外覆盖，恢复备份）
                  if (contentBeforeComplete && contentBeforeComplete.length > aiMessageContent.length) {
                    console.warn('[Chat] Content was truncated, restoring from backup')
                    aiMessageContent = contentBeforeComplete
                    if (hasNewContent) {
                      // 如果确实有新内容，追加到备份内容后面
                      if (!aiMessageContent.endsWith('\n\n') && !aiMessageContent.endsWith('\n')) {
                        aiMessageContent += '\n\n'
                      }
                      // 这里需要重新获取最终响应并追加
                      if (data.data?.result?.response) {
                        aiMessageContent += data.data.result.response
                      }
                    }
                  }
                  
                  console.log('[Chat] Final content after complete:', aiMessageContent.substring(0, 200))
                  console.log('[Chat] Full content length:', aiMessageContent.length)
                  
                  // 确保最终消息已保存（包含所有步骤信息和最终结果）
                  if (currentSessionId && aiMessageId) {
                    // 强制保存完整内容到localStorage
                    updateMessage(currentSessionId, aiMessageId, {
                      content: aiMessageContent, // 确保保存完整内容
                      status: 'sent'
                    })
                    // 确保消息在state中
                    setMessages(prev => {
                      const existingIndex = prev.findIndex(m => m.id === aiMessageId)
                      if (existingIndex >= 0) {
                        const updated = [...prev]
                        updated[existingIndex] = { ...updated[existingIndex], content: aiMessageContent, status: 'sent' }
                        return updated
                      }
                      return prev
                    })
                    
                    // 额外保存一次，确保localStorage中有完整内容
                    const finalMessage = {
                      id: aiMessageId,
                      type: 'text' as const,
                      content: aiMessageContent,
                      sender: 'AI助手',
                      senderId: 'ai',
                      timestamp: Date.now(),
                      status: 'sent' as const,
                    }
                    saveMessage(currentSessionId, finalMessage)
                  }
                  
                  // 标记流式更新完成
                  streamingMessageIdsRef.current.delete(aiMessageId)
                  // 确保消息状态更新为sent
                  break
                  
                case 'error':
                  // 错误信息追加，不覆盖之前的内容
                  const errorMsg = data.data?.error || data.data?.message || '未知错误'
                  // 检查是否已经包含这个错误信息（避免重复）
                  if (!aiMessageContent.includes(errorMsg)) {
                    // 如果当前内容不为空且不是初始状态，添加换行
                    if (aiMessageContent && aiMessageContent !== '🤔 正在分析您的请求...' && !aiMessageContent.endsWith('\n\n')) {
                      aiMessageContent += '\n\n'
                    }
                    aiMessageContent += `❌ 错误: ${errorMsg}`
                  }
                  // 确保错误消息已保存
                  if (currentSessionId && aiMessageId) {
                    updateMessage(currentSessionId, aiMessageId, {
                      content: aiMessageContent,
                      status: 'sent'
                    })
                    // 确保消息在state中
                    setMessages(prev => {
                      const existingIndex = prev.findIndex(m => m.id === aiMessageId)
                      if (existingIndex >= 0) {
                        const updated = [...prev]
                        updated[existingIndex] = { ...updated[existingIndex], content: aiMessageContent, status: 'sent' }
                        return updated
                      }
                      return prev
                    })
                  }
                  
                  // 标记流式更新完成（即使有错误）
                  streamingMessageIdsRef.current.delete(aiMessageId)
                  // 确保消息状态更新为sent，即使有错误也要显示
                  break
              }

              // 更新消息内容 - 直接更新React state以实现实时流式显示
              // 每次收到数据都更新，确保不丢失任何内容（包括所有中间步骤）
              if (currentSessionId && aiMessageId) {
                // 更新 localStorage（每次更新都保存，确保中间步骤不丢失）
                try {
                  updateMessage(currentSessionId, aiMessageId, {
                    content: aiMessageContent, // 保存完整的当前内容（包含所有步骤）
                    status: data.type === 'complete' || data.type === 'error' ? 'sent' : 'sending',
                  })
                  // 额外验证：确保保存成功
                  const savedMessages = getSessionMessages(currentSessionId)
                  const savedMsg = savedMessages.find(m => m.id === aiMessageId)
                  if (savedMsg && savedMsg.content.length < aiMessageContent.length) {
                    console.warn('[Chat] Saved content is shorter than current, re-saving...')
                    // 如果保存的内容被截断，重新保存
                    updateMessage(currentSessionId, aiMessageId, {
                      content: aiMessageContent,
                      status: data.type === 'complete' || data.type === 'error' ? 'sent' : 'sending',
                    })
                  }
                } catch (e) {
                  console.warn('[Chat] Failed to update localStorage:', e)
                  // 如果更新失败，尝试直接保存整个消息
                  try {
                    const fullMessage: Message = {
                      id: aiMessageId,
                      type: 'text',
                      content: aiMessageContent,
                      sender: 'AI助手',
                      senderId: 'ai',
                      timestamp: Date.now(),
                      status: data.type === 'complete' || data.type === 'error' ? 'sent' : 'sending',
                    }
                    saveMessage(currentSessionId, fullMessage)
                  } catch (saveError) {
                    console.error('[Chat] Failed to save message as fallback:', saveError)
                  }
                }
                
                // 直接更新React state中的消息，实现实时流式显示
                // 使用函数式更新，确保基于最新状态
                setMessages(prev => {
                  const existingIndex = prev.findIndex(m => m.id === aiMessageId)
                  
                  if (existingIndex >= 0) {
                    // 消息已存在，更新它
                    const updated = [...prev]
                    updated[existingIndex] = {
                      ...updated[existingIndex],
                      content: aiMessageContent, // 直接使用最新的完整内容
                      status: data.type === 'complete' || data.type === 'error' ? 'sent' : 'sending'
                    }
                    console.log('[Chat] Updated existing message, content length:', aiMessageContent.length)
                    return updated
                  } else {
                    // 消息不存在，添加它
                    const newMessage = {
                      id: aiMessageId,
                      type: 'text' as const,
                      content: aiMessageContent,
                      sender: 'AI助手',
                      senderId: 'ai',
                      timestamp: Date.now(),
                      status: (data.type === 'complete' || data.type === 'error' ? 'sent' : 'sending') as 'sending' | 'sent' | 'failed',
                    }
                    console.log('[Chat] Added new message, content length:', aiMessageContent.length)
                    return [...prev, newMessage]
                  }
                })
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e, line)
            }
          }
        }
      }
    } catch (error: any) {
      console.error('[Chat] Streaming chat error:', error)
      console.error('[Chat] Error details:', {
        message: error?.message,
        stack: error?.stack,
        name: error?.name,
        cause: error?.cause,
      })
      
      // 更新AI消息显示错误，但保留之前的所有内容（追加错误信息，不替换）
      if (currentSessionId && aiMessageId) {
        // 标记流式更新完成
        streamingMessageIdsRef.current.delete(aiMessageId)
        
        // 获取当前消息内容（如果存在）
        const currentMessages = messages.filter(m => m.id === aiMessageId)
        const currentContent = currentMessages.length > 0 
          ? currentMessages[0].content 
          : aiMessageContent || '🤔 正在分析您的请求...'
        
        // 如果当前内容不是初始状态，追加错误信息
        let finalContent = currentContent
        const errorMessage = `❌ 处理失败: ${error?.message || '网络错误，请稍后重试'}`
        
        // 检查是否已经包含错误信息（避免重复）
        if (!finalContent.includes(errorMessage)) {
          // 如果当前内容不为空且不是初始状态，添加换行
          if (finalContent && finalContent !== '🤔 正在分析您的请求...' && !finalContent.endsWith('\n\n')) {
            finalContent += '\n\n'
          }
          finalContent += errorMessage
        }
        
        updateMessage(currentSessionId, aiMessageId, {
          content: finalContent,
          status: 'sent', // 即使有错误也标记为sent，确保显示
        })
        setMessages(prev => prev.map(msg => 
          msg.id === aiMessageId 
            ? { ...msg, content: finalContent, status: 'sent' }
            : msg
        ))
        saveMessage(
          currentSessionId,
          {
            id: aiMessageId,
            type: 'text', // 保持为text类型，即使有错误
            content: finalContent,
            sender: 'AI助手',
            senderId: 'ai',
            timestamp: Date.now(),
            status: 'sent', // 标记为sent，确保显示
          }
        )
      } else {
        sendMessage(
          `❌ 处理失败: ${error?.message || '网络错误，请稍后重试'}`,
          'system',
          '系统'
        )
      }
    }
  }

  // 执行工作流
  const handleExecuteWorkflow = async (workflowId: string, inputData: Record<string, any>) => {
    if (!user || !currentSessionId) return

    setExecuting(true)
    setCurrentWorkflowId(workflowId)
    setShowWorkflowInput(false)

    try {
      const workflowName = workflows.find(w => w.workflow_id === workflowId)?.name || '工作流'
      
      // 创建工作流执行开始消息
      const workflowStartMessage: Message = {
        id: `workflow-start-${Date.now()}`,
        type: 'workflow',
        content: `🔄 正在执行工作流: ${workflowName}`,
        sender: '系统',
        senderId: 'system',
        timestamp: Date.now(),
        status: 'sent',
        metadata: {
          workflowId,
          workflowName,
          executionId: `exec-${Date.now()}`,
          progress: 0,
          executing: true,
        },
      }

      // 直接添加到消息列表
      if (currentSessionId) {
        saveMessage(currentSessionId, workflowStartMessage)
        // 不要调用switchSession，避免重新加载消息导致丢失
        // switchSession(currentSessionId)
      }

      const result = await executeWorkflowById(workflowId, inputData)
      
      // 存储执行结果
      setWorkflowExecutions(prev => {
        const newMap = new Map(prev)
        newMap.set(workflowId, result)
        return newMap
      })

      // 创建工作流执行结果消息（带完整执行数据）
      const workflowResultMessage: Message = {
        id: `workflow-result-${Date.now()}`,
        type: 'workflow',
        content: result.success
          ? `✅ 工作流执行完成: ${workflowName}`
          : `❌ 工作流执行失败: ${workflowName}`,
        sender: '系统',
        senderId: 'system',
        timestamp: Date.now(),
        status: 'sent',
        metadata: {
          workflowId,
          workflowName,
          executionId: result.execution_id,
          execution: result,
          executing: false,
          progress: result.success ? 100 : 0,
          error: result.error,
        },
      }

      // 直接添加到消息列表
      if (currentSessionId) {
        saveMessage(currentSessionId, workflowResultMessage)
        // 不要调用switchSession，避免重新加载消息导致丢失
        // switchSession(currentSessionId)
      }
    } catch (error: any) {
      console.error('Workflow execution failed:', error)
      sendMessage(
        `❌ 工作流执行失败: ${error?.message || '未知错误'}`,
        'system',
        '系统'
      )
    } finally {
      setExecuting(false)
    }
  }

  // 安全的JSON序列化函数，避免循环引用
  const safeStringify = (obj: any): string => {
    const seen = new WeakSet()
    try {
      return JSON.stringify(obj, (key, value) => {
        // 移除循环引用
        if (typeof value === 'object' && value !== null) {
          if (seen.has(value)) {
            return '[Circular]'
          }
          seen.add(value)
        }
        // 移除函数和DOM元素
        if (typeof value === 'function' || value instanceof HTMLElement) {
          return undefined
        }
        return value
      }, 2)
    } catch (error) {
      console.error('JSON stringify error:', error)
      return String(obj)
    }
  }

  // 格式化工作流结果（安全序列化，避免循环引用）
  const formatWorkflowResult = (result: any): string => {
    if (!result) return '无结果'
    
    const llmResult = result['LLM节点_result'] || 
                      result['LLM节点_output']?.content ||
                      result.LLM节点_result ||
                      result.LLM节点_output?.content
    
    if (llmResult) {
      return String(llmResult)
    }
    
    if (result.final_result) {
      return typeof result.final_result === 'string' 
        ? result.final_result 
        : safeStringify(result.final_result)
    }
    
    return safeStringify(result)
  }

  const handleKnowledgeSearch = (query: string) => {
    setKnowledgeQuery(query)
    setKnowledgeSidebarOpen(true)
    handleSend(`/kb ${query}`)
  }

  const handleDynamicWorkflow = async (content: string, user: any) => {
    if (!currentSessionId) {
      console.error('[DynamicWorkflow] No current session ID')
      return
    }

    console.log('[DynamicWorkflow] Starting workflow execution for:', content.substring(0, 50))

    try {
      setExecuting(true)
      
      // 创建AI回复消息（用于显示动态工作流）
      const aiMessageId = `ai-${Date.now()}`
      const workflowMessageId = `workflow-${aiMessageId}`
      
      // 初始化工作流chunks
      const chunks: WorkflowChunk[] = []
      setWorkflowChunks(prev => new Map(prev).set(workflowMessageId, chunks))
      
      let messageContent = '💭 正在分析您的请求...'
      let thinkingContent = '' // 单独保存思考内容，确保不被覆盖
      
      const aiMessage: Message = {
        id: aiMessageId,
        type: 'text',
        content: messageContent,
        sender: 'AI助手',
        senderId: 'ai',
        timestamp: Date.now(),
        status: 'sending',
        metadata: {
          workflowMessageId,
          workflowType: 'dynamic'
        }
      }

      // 标记为流式更新中，防止被hook的消息覆盖
      streamingMessageIdsRef.current.add(aiMessageId)

      // 保存消息并立即更新本地state
      if (currentSessionId) {
        saveMessage(currentSessionId, aiMessage)
        // 立即添加到本地state，确保消息显示
        setMessages(prev => {
          // 检查是否已存在，避免重复
          if (prev.find(m => m.id === aiMessageId)) {
            return prev
          }
          return [...prev, aiMessage]
        })
        // 不要调用switchSession，避免重新加载消息导致丢失
        // switchSession(currentSessionId)
      }

      // 执行动态工作流（流式）
      console.log('[DynamicWorkflow] Starting stream execution...')
      
      // 更新初始消息内容
      updateMessage(currentSessionId, aiMessageId, {
        content: messageContent,
        status: 'sending'
      })
      setMessages(prev => prev.map(m => 
        m.id === aiMessageId 
          ? { ...m, content: messageContent, status: 'sending' }
          : m
      ))

      try {
        let chunkCount = 0
        let hasExecutionCompleted = false // 跟踪是否已经收到执行完成的信号
        // 用于去重：记录每个agent_id的最后一次agent_complete chunk的索引
        const lastAgentCompleteIndices = new Map<string, number>()
        
        // 构建对话历史（最近20条消息，保持更长的上下文记忆）
        const recentMessages = messages
          .filter(m => m.type === 'text' && m.senderId !== 'system')
          .slice(-20)  // 增加到20条，保持更长的对话上下文
          .map(m => ({
            role: m.senderId === user.user_id ? 'user' : 'assistant',
            content: m.content,
          }))
        
        for await (const chunk of executeDynamicWorkflow({
          user_input: content,
          context: {
            user_id: user.user_id,
            username: user.username,
            session_id: currentSessionId,
            conversation_history: recentMessages  // 添加对话历史
          },
          stream: true
        })) {
          chunkCount++
          console.log(`[DynamicWorkflow] Received chunk ${chunkCount}:`, chunk.type, chunk.stage)
          
          // 检查是否已经收到执行完成的信号
          if (
            (chunk.type === 'execution' && chunk.stage === 'execution_complete') ||
            chunk.type === 'execution_complete'
          ) {
            hasExecutionCompleted = true
          }
          
          // 去重逻辑：对于agent_complete，只保留每个agent_id的最后一个
          if (chunk.type === 'execution' && chunk.stage === 'agent_complete' && chunk.agent_id) {
            const agentId = chunk.agent_id
            const lastIndex = lastAgentCompleteIndices.get(agentId)
            if (lastIndex !== undefined && lastIndex >= 0 && lastIndex < chunks.length) {
              // 移除之前的agent_complete chunk
              chunks.splice(lastIndex, 1)
              // 更新所有后续chunk的索引（减1）
              for (const [aid, idx] of lastAgentCompleteIndices.entries()) {
                if (idx > lastIndex) {
                  lastAgentCompleteIndices.set(aid, idx - 1)
                }
              }
            }
          }
          
          // 更新chunks - 确保完整保存chunk数据，包括final_result
          // 关键修复：对于thinking类型的chunk，确保保存原始完整的message，而不是清理后的
          const chunkToSave = { ...chunk } // 创建副本，确保所有数据都被保存
          
          // 如果是thinking类型的chunk，且chunk.message存在，确保保存原始完整内容
          // 注意：这里保存的是从流式响应中接收到的原始message，确保不被清理逻辑截断
          if (chunk.type === 'thinking' && chunk.message) {
            // 确保chunkToSave中的message是原始完整内容
            // 如果chunk.message已经被清理过，我们需要从原始chunk中恢复
            // 但实际上，从流式响应中接收到的chunk.message应该是完整的
            // 所以这里主要是确保不会因为后续的清理逻辑而丢失内容
            chunkToSave.message = chunk.message // 确保保存原始完整内容
            
            // 调试：记录保存的thinking chunk的message长度
            if (chunkCount % 20 === 0 || chunkCount < 5) { // 每20个chunk记录一次，或前5个chunk都记录
              console.log(`[DynamicWorkflow] Saving thinking chunk ${chunkCount} to workflowChunks:`, {
                messageLength: chunk.message.length,
                messagePreview: chunk.message.substring(0, 50) + '...',
                messageEnd: '...' + chunk.message.substring(Math.max(0, chunk.message.length - 30))
              })
            }
          }
          
          chunks.push(chunkToSave)
          
          // 如果是agent_complete，记录当前chunk的索引（在push之后）
          if (chunk.type === 'execution' && chunk.stage === 'agent_complete' && chunk.agent_id) {
            lastAgentCompleteIndices.set(chunk.agent_id, chunks.length - 1)
          }
          setWorkflowChunks(prev => {
            const newMap = new Map(prev)
            newMap.set(workflowMessageId, [...chunks])
            // 如果是execution_complete，额外记录日志
            if (chunk.type === 'execution_complete' || chunk.stage === 'execution_complete') {
              console.log('[DynamicWorkflow] Saving execution_complete chunk to workflowChunks:', {
                hasFinalResult: !!chunk.final_result,
                chunkKeys: Object.keys(chunk),
                finalResultKeys: chunk.final_result ? Object.keys(chunk.final_result) : []
              })
            }
            return newMap
          })

          // 实时更新消息内容，显示进度
          let shouldUpdate = false
          
          if (chunk.type === 'thinking') {
            // 思考内容：单独保存，确保不被执行过程覆盖
            if (chunk.message) {
              let cleanMessage = chunk.message
              // 移除复杂度信息（如：medium复杂度、simple、complex等）
              cleanMessage = cleanMessage.replace(/[：:]\s*(simple|medium|complex|简单|中等|复杂|低|中|高)\s*复杂度?/gi, '')
              cleanMessage = cleanMessage.replace(/复杂度[：:]\s*(simple|medium|complex|简单|中等|复杂|低|中|高)/gi, '')
              // 移除类型信息（如：类型: data_analysis等）
              cleanMessage = cleanMessage.replace(/类型[：:]\s*[^，,\n]+/gi, '')
              cleanMessage = cleanMessage.replace(/[，,]\s*类型[：:]\s*[^，,\n]+/gi, '')
              // 移除预计时间信息
              cleanMessage = cleanMessage.replace(/预计时间[：:]\s*[^，,\n]+/gi, '')
              cleanMessage = cleanMessage.replace(/[，,]\s*预计时间[：:]\s*[^，,\n]+/gi, '')
              // 移除智能体数量、执行层等统计信息（如果只是简单描述）
              cleanMessage = cleanMessage.replace(/：\s*\d+个智能体[，,]\s*\d+个执行层/gi, '')
              // 清理多余的空格和标点
              cleanMessage = cleanMessage.replace(/\s+/g, ' ').trim()
              cleanMessage = cleanMessage.replace(/[，,]\s*[，,]/g, '，')
              
              // 保存思考内容（始终更新，确保获取最新完整内容）
              // 这是关键：无论是否更新UI，都要保存最新的思考内容到变量中
              // 注意：保存原始消息（rawMessage），而不是清理后的消息，确保完整内容不被截断
              const rawMessage = chunk.message || ''
              thinkingContent = rawMessage // 保存原始完整内容，不进行清理
              
              // 优化：对于流式输出，减少UI更新频率
              // 如果is_streaming为true，且内容长度变化不大，可以跳过部分更新
              const isStreaming = chunk.is_streaming === true
              const hasExistingThinking = messageContent.includes('💭 思考过程')
              
              // 如果内容长度显著增加（超过50个字符），或者流式输出完成，则更新
              const currentThinkingMatch = messageContent.match(/💭 思考过程\n\n(.+?)(?:\n\n⚙️ 执行过程|$)/s)
              const currentThinkingLength = currentThinkingMatch ? currentThinkingMatch[1].length : 0
              const newThinkingLength = cleanMessage.length
              const lengthIncreased = newThinkingLength - currentThinkingLength >= 50
              
              // 决定是否更新UI：
              // 1. 如果流式输出完成（!isStreaming），必须更新
              // 2. 如果内容显著增加（lengthIncreased），必须更新
              // 3. 如果还没有显示思考内容（!hasExistingThinking），必须更新
              // 4. 否则，如果是流式输出且内容变化不大，可以跳过更新（减少UI刷新）
              const shouldUpdateUI = !isStreaming || lengthIncreased || !hasExistingThinking
              
              // 重要：即使跳过UI更新，也要确保thinkingContent变量已保存最新内容
              // 这样在执行过程开始时，可以从thinkingContent变量中获取完整内容
              
              if (shouldUpdateUI) {
                // 构建完整的消息内容：思考内容 + 执行过程（如果有）
                // 注意：UI显示时使用清理后的内容（cleanMessage），但thinkingContent变量保存原始完整内容
                let fullContent = ''
                if (cleanMessage) {
                  fullContent = `💭 思考过程\n\n${cleanMessage}`
                }
                
                // 如果有执行过程内容，追加它
                const executionMatch = messageContent.match(/⚙️ 执行过程\n\n(.+)/s)
                if (executionMatch) {
                  if (fullContent) {
                    fullContent += '\n\n'
                  }
                  fullContent += `⚙️ 执行过程\n\n${executionMatch[1]}`
                }
                
                messageContent = fullContent || thinkingContent || '💭 正在分析您的请求...'
                shouldUpdate = true
              }
              // 注意：即使不更新UI，thinkingContent变量也已经保存了最新内容
            }
          } else if (chunk.type === 'design') {
            // DeepSeek风格：只显示文字描述
            if (chunk.message) {
              messageContent = chunk.message
              shouldUpdate = true
            }
          } else if (chunk.type === 'execution') {
            // 执行过程：追加到现有内容，不覆盖思考内容
            let executionContent = ''
            if (chunk.stage === 'layer_start') {
              executionContent = `⚡ 执行第${chunk.layer_number}/${chunk.total_layers}层：${chunk.message || ''}`
            } else if (chunk.stage === 'agent_start') {
              executionContent = `   • ${chunk.agent_type || chunk.agent_id}：${chunk.agent_task || ''}`
            } else if (chunk.stage === 'agent_complete') {
              const time = chunk.agent_result?.execution_time || 0
              const status = chunk.agent_result?.success ? '✓' : '✗'
              executionContent = `   ${status} ${chunk.agent_id} 完成 (${time.toFixed(2)}s)`
            } else if (chunk.stage === 'execution_complete') {
              console.log('[DynamicWorkflow] Execution complete, final_result:', chunk.final_result)
              console.log('[DynamicWorkflow] Full chunk data:', JSON.stringify(chunk, null, 2).substring(0, 500))
              // 执行完成时，只显示完成提示，最终结果会在DynamicWorkflowDisplay组件中显示
              executionContent = `✅ 执行完成`
              // 确保final_result被正确保存到chunks中
              if (chunk.final_result) {
                console.log('[DynamicWorkflow] final_result found in chunk:', Object.keys(chunk.final_result))
              } else {
                console.warn('[DynamicWorkflow] No final_result in execution_complete chunk')
              }
            } else if (chunk.message) {
              executionContent = `⚡ ${chunk.message}`
            }
            
            if (executionContent) {
              // 构建完整的消息内容：思考内容 + 执行过程
              let fullContent = ''
              
              // 关键修复：始终优先使用thinkingContent变量（这是最可靠的来源）
              // thinkingContent变量在thinking chunks处理时被持续更新，保存了完整的原始思考内容
              // 绝对不要从messageContent中提取思考内容，因为messageContent可能已经被截断
              // 只有在thinkingContent完全为空时，才尝试从messageContent中提取（作为最后的后备方案）
              let finalThinkingContent = thinkingContent
              
              // 如果thinkingContent为空，才尝试从messageContent中提取（作为最后的后备方案）
              if (!finalThinkingContent || finalThinkingContent.trim().length === 0) {
                const thinkingMatch = messageContent.match(/💭 思考过程\n\n(.+?)(?:\n\n⚙️ 执行过程|$)/s)
                const existingThinkingContent = thinkingMatch ? thinkingMatch[1] : ''
                if (existingThinkingContent && existingThinkingContent.trim().length > 0) {
                  finalThinkingContent = existingThinkingContent
                  // 同时更新thinkingContent变量，以便后续使用
                  thinkingContent = existingThinkingContent
                  console.log('[DynamicWorkflow] Restored thinkingContent from messageContent:', existingThinkingContent.length, 'chars')
                }
              }
              
              // 调试日志：检查思考内容状态（仅在关键阶段记录）
              if (chunk.stage === 'execution_start' || (chunk.stage === 'layer_start' && chunk.layer_number === 1)) {
                console.log('[DynamicWorkflow] Execution started - Thinking content status:', {
                  thinkingContentLength: thinkingContent ? thinkingContent.length : 0,
                  thinkingContentPreview: thinkingContent ? thinkingContent.substring(0, 100) + '...' : 'empty',
                  thinkingContentEnd: thinkingContent ? '...' + thinkingContent.substring(thinkingContent.length - 50) : 'empty',
                  finalThinkingLength: finalThinkingContent ? finalThinkingContent.length : 0,
                  messageContentLength: messageContent.length,
                  messageContentPreview: messageContent.substring(0, 200),
                  messageContentEnd: messageContent.length > 200 ? '...' + messageContent.substring(messageContent.length - 100) : messageContent
                })
              }
              
              // 先添加思考内容（如果存在）
              if (finalThinkingContent && finalThinkingContent.trim().length > 0) {
                // 直接使用finalThinkingContent，确保完整内容被包含
                fullContent = `💭 思考过程\n\n${finalThinkingContent}`
                
                // 调试：验证最终内容长度
                if (chunk.stage === 'execution_start' || (chunk.stage === 'layer_start' && chunk.layer_number === 1)) {
                  console.log('[DynamicWorkflow] Final content being built:', {
                    fullContentLength: fullContent.length,
                    thinkingPartLength: finalThinkingContent.length,
                    fullContentPreview: fullContent.substring(0, 150) + '...',
                    fullContentEnd: '...' + fullContent.substring(fullContent.length - 100)
                  })
                }
              } else {
                // 如果思考内容完全丢失，记录警告
                console.warn('[DynamicWorkflow] ⚠️ Thinking content is missing when execution starts!', {
                  hasThinkingContent: !!thinkingContent,
                  thinkingContentLength: thinkingContent ? thinkingContent.length : 0,
                  messageContentLength: messageContent.length,
                  messageContentPreview: messageContent.substring(0, 300)
                })
              }
              
              // 然后添加执行过程
              const executionMatch = messageContent.match(/⚙️ 执行过程\n\n(.+)/s)
              let currentExecutionContent = executionMatch ? executionMatch[1] : ''
              
              // 追加新的执行内容
              if (currentExecutionContent) {
                currentExecutionContent += `\n${executionContent}`
              } else {
                currentExecutionContent = executionContent
              }
              
              // 组合完整内容
              if (fullContent) {
                fullContent += '\n\n'
              }
              fullContent += `⚙️ 执行过程\n\n${currentExecutionContent}`
              
              messageContent = fullContent
              shouldUpdate = true
            }
          } else if (chunk.type === 'error') {
            // 优先使用message，其次使用error，最后使用默认消息
            // 处理空字符串的情况
            const errorMsg = (chunk.message && chunk.message.trim()) || 
                           (chunk.error && chunk.error.trim()) || 
                           chunk.error_type || 
                           '未知错误'
            
            // 检查是否是网络错误（在流式传输中断时常见）
            const isNetworkError = /network error|ERR_INCOMPLETE_CHUNKED_ENCODING|连接中断|连接失败/i.test(errorMsg)
            
            // 如果已经收到执行完成的信号，且是网络错误，则忽略该错误（不更新UI）
            if (hasExecutionCompleted && isNetworkError) {
              console.warn(
                '[DynamicWorkflow] Network error after execution completed, ignoring for UI:',
                errorMsg
              )
              // 不更新 messageContent，不设置 shouldUpdate，继续处理下一个chunk
              continue
            }
            
            messageContent = `⚠️ 错误: ${errorMsg}`
            // 如果有stage信息，添加到错误消息中
            if (chunk.stage) {
              messageContent += ` (阶段: ${chunk.stage})`
            }
            // 如果有error_type，也添加到消息中
            if (chunk.error_type && chunk.error_type !== errorMsg) {
              messageContent += ` [${chunk.error_type}]`
            }
            shouldUpdate = true
            console.error('[DynamicWorkflow] Error chunk received:', chunk)
          }

          // 实时更新消息内容
          if (shouldUpdate) {
            // 安全地记录日志
            const logContent = typeof messageContent === 'string' 
              ? messageContent.substring(0, 100) 
              : String(messageContent).substring(0, 100)
            console.log(`[DynamicWorkflow] Updating message content:`, logContent)
            console.log(`[DynamicWorkflow] Message ID:`, aiMessageId)
            
            // 更新localStorage
            updateMessage(currentSessionId, aiMessageId, {
              content: messageContent,
              status: chunk.type === 'execution_complete' || chunk.type === 'error' ? 'sent' : 'sending'
            })

            // 强制更新React state，确保UI刷新
            setMessages(prev => {
              const messageExists = prev.find(m => m.id === aiMessageId)
              if (!messageExists) {
                console.warn(`[DynamicWorkflow] Message ${aiMessageId} not found in state, adding it`)
                const messageStatus: 'sending' | 'sent' | 'failed' = 
                  chunk.type === 'execution_complete' || chunk.type === 'error' ? 'sent' : 'sending'
                return [...prev, {
                  id: aiMessageId,
                  type: 'text' as const,
                  content: typeof messageContent === 'string' ? messageContent : String(messageContent),
                  sender: 'AI助手',
                  senderId: 'ai',
                  timestamp: Date.now(),
                  status: messageStatus,
                  metadata: {
                    workflowMessageId,
                    workflowType: 'dynamic'
                  }
                }]
              }
              
              const updated = prev.map(m => {
                if (m.id === aiMessageId) {
                  const messageStatus: 'sending' | 'sent' | 'failed' = 
                    chunk.type === 'execution_complete' || chunk.type === 'error' ? 'sent' : 'sending'
                  return {
                    ...m,
                    content: typeof messageContent === 'string' ? messageContent : String(messageContent),
                    status: messageStatus
                  }
                }
                return m
              })
              const foundMessage = updated.find(m => m.id === aiMessageId)
              // 安全地记录日志
              if (foundMessage?.content) {
                const logContent = typeof foundMessage.content === 'string'
                  ? foundMessage.content.substring(0, 50)
                  : String(foundMessage.content).substring(0, 50)
                console.log(`[DynamicWorkflow] Updated messages, message content:`, logContent)
              }
              return updated
            })
            
            // 强制触发重新渲染
            setWorkflowChunks(prev => {
              const newMap = new Map(prev)
              newMap.set(workflowMessageId, [...chunks])
              return newMap
            })
          }
        }
        
        console.log(`[DynamicWorkflow] Stream completed, received ${chunkCount} chunks`)
        
        // 检查是否已有最终结果（即使流被中断，也可能已经收到结果）
        const hasFinalResult = chunks.some(c => 
          (c.type === 'execution' && c.stage === 'execution_complete' && (c.final_result || c.result)) ||
          (c.type === 'execution_complete' && (c.final_result || c.result))
        )
        
        if (!hasFinalResult && chunks.length > 0) {
          // 尝试从最后一个执行chunk中提取结果
          const lastExecutionChunk = chunks.filter(c => c.type === 'execution').pop()
          if (lastExecutionChunk?.agent_result?.output) {
            console.log('[DynamicWorkflow] Found result in last execution chunk, stream may have been interrupted')
          }
        }
        
        // 确保最终消息已保存
        if (currentSessionId) {
          const finalMessage = messages.find(m => m.id === aiMessageId)
          if (finalMessage) {
            saveMessage(currentSessionId, finalMessage)
          }
        }
        
        // 流式更新完成，移除标记
        streamingMessageIdsRef.current.delete(aiMessageId)
        
        // 流式更新完成后，重新加载消息确保同步
        if (currentSessionId) {
          const loadedMessages = getSessionMessages(currentSessionId)
          setMessages(loadedMessages)
        }
      } catch (error: any) {
        console.error('Dynamic workflow execution failed:', error)
        const errorMsg = error?.message || '执行失败'
        
        // 检查是否在错误发生前已经收到了最终结果
        const hasFinalResult = chunks.some(c => 
          (c.type === 'execution' && c.stage === 'execution_complete' && (c.final_result || c.result)) ||
          (c.type === 'execution_complete' && (c.final_result || c.result))
        )
        
        if (hasFinalResult) {
          console.log('[DynamicWorkflow] Error occurred but final result was already received, will be displayed')
          // 如果有最终结果，不显示错误消息，让DynamicWorkflowDisplay组件显示结果
        } else {
          // 流式更新完成（即使有错误），移除标记
          streamingMessageIdsRef.current.delete(aiMessageId)
          
          updateMessage(currentSessionId, aiMessageId, {
            content: `❌ 错误: ${errorMsg}`,
            status: 'sent'
          })

          setMessages(prev => prev.map(m => 
            m.id === aiMessageId 
              ? { ...m, content: `❌ 错误: ${errorMsg}`, status: 'sent' }
              : m
          ))
        }
      } finally {
        setExecuting(false)
      }
    } catch (error: any) {
      console.error('Dynamic workflow handler failed:', error)
      sendMessage(
        `❌ 动态工作流执行失败: ${error?.message || '未知错误'}`,
        'system',
        '系统'
      )
      setExecuting(false)
    }
  }

  const handleDeleteMessage = (messageId: string) => {
    removeMessage(messageId)
  }

  // 轮询DAG执行状态
  const pollDAGExecutionStatus = async (executionId: string, maxAttempts = 30) => {
    let attempts = 0
    
    const poll = async () => {
      if (attempts >= maxAttempts) {
        sendMessage('⏱️ 任务执行超时，请稍后查询执行状态', 'system', '系统')
        return
      }
      
      try {
        const status = await getDAGExecutionStatus(executionId)
        
        if (status.status === 'completed') {
          sendMessage(
            `✅ 任务执行完成！\n\n${status.final_output || '无输出'}`,
            'system',
            '系统'
          )
        } else if (status.status === 'failed') {
          sendMessage(
            `❌ 任务执行失败: ${status.error_message || '未知错误'}`,
            'system',
            '系统'
          )
        } else {
          // 继续轮询
          attempts++
          setTimeout(poll, 2000) // 每2秒轮询一次
        }
      } catch (error) {
        console.error('Failed to poll DAG execution status:', error)
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000)
        }
      }
    }
    
    setTimeout(poll, 2000) // 首次延迟2秒
  }

  return (
    <AuthGuard requireAuth>
      <div className="flex h-screen bg-gray-50">
        {/* 侧边栏 */}
        <div
          className={`${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } sm:translate-x-0 fixed sm:static inset-y-0 left-0 z-30 transition-transform duration-300`}
        >
          <ChatSidebar
            sessions={sessions}
            currentSessionId={currentSessionId}
            onSelectSession={switchSession}
            onNewSession={createNewSession}
            onDeleteSession={removeSession}
            onClose={() => setSidebarOpen(false)}
          />
        </div>

        {/* 遮罩层（移动端） */}
        {sidebarOpen ? (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 sm:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        ) : null}

        {/* 主聊天区域 */}
        <div className="flex-1 flex flex-col min-w-0 relative">
          {/* 顶部导航栏 */}
          <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="sm:hidden text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  {(() => {
                    const session = sessions.find(s => s.id === currentSessionId)
                    if (!session || !session.title) return '企业AI助手'
                    if (typeof session.title === 'string') return session.title
                    if (typeof session.title === 'object') {
                      if ('title' in session.title && typeof session.title.title === 'string') {
                        return session.title.title
                      }
                      if ('name' in session.title && typeof session.title.name === 'string') {
                        return session.title.name
                      }
                      return '企业AI助手'
                    }
                    return String(session.title)
                  })()}
                </h1>
                <p className="text-sm text-gray-500">
                  {user?.username || '用户'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* 知识库按钮 */}
              <button
                onClick={() => setKnowledgeSidebarOpen(!knowledgeSidebarOpen)}
                className={`p-2 rounded-lg transition-colors ${
                  knowledgeSidebarOpen
                    ? 'bg-blue-100 text-blue-600'
                    : 'text-gray-500 hover:bg-gray-100'
                }`}
                title="知识库"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                  />
                </svg>
              </button>
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-blue-600 text-sm font-semibold">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
            </div>
          </div>

          {/* 消息列表 */}
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="flex-1 overflow-y-auto">
              <MessageList
                messages={messages}
                currentUserId={user?.user_id || ''}
                onResend={resendMessage}
                onDelete={removeMessage}
                workflowExecutions={workflowExecutions}
                workflowChunks={workflowChunks}
                showThinkingContent={showThinkingContent}
              />
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* 消息输入 */}
          <MessageInput
            onSend={handleSend}
            disabled={sending || executing || !currentSessionId}
            placeholder={executing ? '工作流执行中...' : currentSessionId ? '输入消息，系统会自动识别意图并路由到合适的服务...' : '请先创建或选择会话'}
            enableKnowledgeSearch={true}
            onKnowledgeSearch={handleKnowledgeSearch}
            showThinkingContent={showThinkingContent}
            onToggleThinkingContent={() => setShowThinkingContent(!showThinkingContent)}
          />
        </div>


        {/* 知识库侧边栏 */}
        {knowledgeSidebarOpen ? (
          <KnowledgeSidebar
            query={knowledgeQuery}
            onClose={() => setKnowledgeSidebarOpen(false)}
            onSelectDocument={(doc) => {
              console.log('Selected document:', doc)
              // TODO: 打开文档详情
            }}
            onSelectConcept={(concept) => {
              handleKnowledgeSearch(concept)
            }}
          />
        ) : null}

        {/* 工作流输入对话框 */}
        {showWorkflowInput && currentWorkflowId ? (
          <WorkflowInputDialog
            workflowId={currentWorkflowId}
            workflow={workflows.find(w => w.workflow_id === currentWorkflowId)}
            onExecute={handleExecuteWorkflow}
            onCancel={() => {
              setShowWorkflowInput(false)
              setCurrentWorkflowId(null)
            }}
          />
        ) : null}
      </div>
    </AuthGuard>
  )
}

// 工作流输入对话框组件
interface WorkflowInputDialogProps {
  workflowId: string
  workflow?: WorkflowListItem
  onExecute: (workflowId: string, inputData: Record<string, any>) => void
  onCancel: () => void
}

const WorkflowInputDialog: React.FC<WorkflowInputDialogProps> = ({
  workflowId,
  workflow,
  onExecute,
  onCancel,
}) => {
  const [inputData, setInputData] = useState('{\n  "input": ""\n}')
  const [error, setError] = useState<string | null>(null)

  const handleExecute = () => {
    try {
      const parsed = JSON.parse(inputData)
      onExecute(workflowId, parsed)
    } catch (e) {
      setError('无效的 JSON 格式')
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            执行工作流: {workflow?.name || workflowId}
          </h2>
          {workflow?.description ? (
            <p className="text-sm text-gray-600 mt-1">{workflow.description}</p>
          ) : null}
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              输入参数 (JSON)
            </label>
            <textarea
              value={inputData}
              onChange={(e) => {
                setInputData(e.target.value)
                setError(null)
              }}
              rows={12}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              placeholder='{\n  "input": "您的输入内容"\n}'
            />
            {error ? (
              <p className="text-red-600 text-sm mt-2">{error}</p>
            ) : null}
            <div className="mt-2 text-xs text-gray-500">
              <p>示例:</p>
              <pre className="bg-gray-50 p-2 rounded mt-1">
{`{
  "input": "请帮我写一首关于春天的诗"
}`}
              </pre>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleExecute}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            执行
          </button>
        </div>
      </div>
    </div>
  )
}


