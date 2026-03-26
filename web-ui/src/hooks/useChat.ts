'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Message, ChatSession, WorkflowExecutionStatus, ToolExecutionStatus } from '@/types/chat';
import {
  getSessions,
  saveSession,
  deleteSession,
  getSessionMessages,
  saveMessage,
  updateMessage,
  deleteMessage,
  createSession,
} from '@/lib/chat';
import { workflowEngineClient } from '@/lib/api/client';
import { mcpGatewayClient } from '@/lib/api/client';

interface UseChatOptions {
  sessionId?: string;
  autoScroll?: boolean;
}

export function useChat(options: UseChatOptions = {}) {
  const { sessionId, autoScroll = true } = options;

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  // 从localStorage恢复currentSessionId，确保刷新后不丢失
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(() => {
    if (sessionId) return sessionId;
    // 尝试从localStorage恢复上次的会话ID
    if (typeof window !== 'undefined') {
      try {
        const savedSessionId = localStorage.getItem('chat_current_session_id');
        if (savedSessionId) {
          // 验证会话是否存在
          const sessions = getSessions();
          if (sessions.find((s) => s.id === savedSessionId)) {
            return savedSessionId;
          }
        }
      } catch (e) {
        console.warn('[useChat] Failed to restore sessionId from localStorage:', e);
      }
    }
    return null;
  });
  // 初始化消息：如果有sessionId，立即从localStorage加载
  const [messages, setMessages] = useState<Message[]>(() => {
    if (sessionId) {
      try {
        const loadedMessages = getSessionMessages(sessionId);
        if (loadedMessages.length > 0) {
          return loadedMessages;
        }
      } catch (e) {
        console.warn('[useChat] Failed to load initial messages:', e);
      }
    }
    return [];
  });
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [workflowStatuses, setWorkflowStatuses] = useState<Map<string, WorkflowExecutionStatus>>(
    new Map()
  );
  const [toolStatuses, setToolStatuses] = useState<Map<string, ToolExecutionStatus>>(new Map());

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollingIntervalsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  // 加载会话列表（同步执行，确保数据及时加载）
  const loadSessions = useCallback(() => {
    try {
      const loadedSessions = getSessions();
      // 确保所有会话的title都是字符串，再次清理（双重保险）
      const cleanedSessions = loadedSessions.map((s) => {
        let title = s.title;
        if (typeof title !== 'string') {
          if (typeof title === 'object' && title !== null) {
            if ('title' in title && typeof title.title === 'string') {
              title = title.title;
            } else if ('name' in title && typeof title.name === 'string') {
              title = title.name;
            } else if ('content' in title && typeof title.content === 'string') {
              title = title.content.substring(0, 50);
            } else {
              title = '未命名会话';
            }
          } else {
            const str = String(title);
            title = str === '[object Object]' ? '未命名会话' : str;
          }
        }
        if (!title || title === '[object Object]') {
          title = '未命名会话';
        }
        return { ...s, title };
      });
      setSessions(cleanedSessions);

      // 如果没有当前会话且有会话，选择第一个
      if (!currentSessionId && cleanedSessions.length > 0) {
        setCurrentSessionId(cleanedSessions[0].id);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  }, [currentSessionId]);

  // 加载消息（同步执行，确保数据及时加载）
  const loadMessages = useCallback((sid: string) => {
    try {
      const loadedMessages = getSessionMessages(sid);
      setMessages(loadedMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
      setMessages([]);
    }
  }, []);

  // 初始化（立即同步加载，确保刷新后数据不丢失）
  useEffect(() => {
    // 立即同步加载会话列表，确保刷新后数据不丢失
    loadSessions();

    // 如果有当前会话ID，立即加载消息
    if (currentSessionId) {
      try {
        const loadedMessages = getSessionMessages(currentSessionId);
        if (loadedMessages.length > 0) {
          console.log(
            '[useChat] Loaded initial messages:',
            loadedMessages.length,
            'session:',
            currentSessionId
          );
          setMessages(loadedMessages);
        } else {
          console.log('[useChat] No messages found in localStorage for session:', currentSessionId);
        }
      } catch (error) {
        console.error('[useChat] Failed to load initial messages:', error);
      }
    } else {
      console.log('[useChat] No currentSessionId on mount');
    }
  }, []); // 只在组件挂载时执行一次

  // 当会话ID变化时加载消息（同步加载，确保数据及时显示）
  useEffect(() => {
    if (currentSessionId) {
      // 同步加载消息，确保刷新后数据不丢失
      try {
        const loadedMessages = getSessionMessages(currentSessionId);
        // 只在有消息时记录日志，避免新会话的噪音
        if (loadedMessages.length > 0 && process.env.NODE_ENV === 'development') {
          console.log(
            '[useChat] Loaded messages on session change:',
            loadedMessages.length,
            'session:',
            currentSessionId
          );
        }
        setMessages(loadedMessages);
      } catch (error) {
        console.error('[useChat] Failed to load messages:', error);
        setMessages([]);
      }
    } else {
      setMessages([]);
    }
  }, [currentSessionId]); // 移除 loadMessages 依赖，直接调用 getSessionMessages

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  // 发送消息
  const sendMessage = useCallback(
    async (content: string, userId: string, username: string) => {
      if (!currentSessionId || !content.trim() || sending) return;

      setSending(true);

      // 创建用户消息
      const userMessage: Message = {
        id: `msg_${Date.now()}`,
        type: 'text',
        content: content.trim(),
        sender: username,
        senderId: userId,
        timestamp: Date.now(),
        status: 'sending',
      };

      // 添加到消息列表
      setMessages((prev) => [...prev, userMessage]);
      saveMessage(currentSessionId, userMessage);

      try {
        // 更新消息状态为已发送
        updateMessage(currentSessionId, userMessage.id, { status: 'sent' });
        setMessages((prev) =>
          prev.map((msg) => (msg.id === userMessage.id ? { ...msg, status: 'sent' } : msg))
        );

        // 检查是否是工作流执行命令
        if (content.trim().startsWith('/workflow ')) {
          const workflowName = content.trim().substring(10).trim();
          await executeWorkflow(workflowName, userId, username);
        } else if (content.trim().startsWith('/tool ')) {
          const toolName = content.trim().substring(6).trim();
          await executeTool(toolName, userId, username);
        } else {
          // 普通文本消息，可以添加AI回复逻辑
          await handleTextMessage(content, userId, username);
        }
      } catch (error) {
        console.error('Failed to send message:', error);
        updateMessage(currentSessionId, userMessage.id, { status: 'failed' });
        setMessages((prev) =>
          prev.map((msg) => (msg.id === userMessage.id ? { ...msg, status: 'failed' } : msg))
        );
      } finally {
        setSending(false);
      }
    },
    [currentSessionId, sending]
  );

  // 执行工作流
  const executeWorkflow = useCallback(
    async (workflowName: string, userId: string, username: string) => {
      if (!currentSessionId) return;

      const executionId = `exec_${Date.now()}`;

      // 创建工作流执行消息
      const workflowMessage: Message = {
        id: `msg_workflow_${Date.now()}`,
        type: 'workflow',
        content: `正在执行工作流: ${workflowName}`,
        sender: '系统',
        senderId: 'system',
        timestamp: Date.now(),
        status: 'sent',
        metadata: {
          workflowName,
          executionId,
        },
      };

      setMessages((prev) => [...prev, workflowMessage]);
      saveMessage(currentSessionId, workflowMessage);

      // 初始化工作流状态
      const workflowStatus: WorkflowExecutionStatus = {
        executionId,
        workflowId: '',
        workflowName,
        status: 'running',
        progress: 0,
        startTime: Date.now(),
      };

      setWorkflowStatuses((prev) => new Map(prev).set(executionId, workflowStatus));

      try {
        // 执行工作流
        const result = await workflowEngineClient.post('/api/workflows/execute', {
          workflow_name: workflowName,
          input_data: {},
          context: {},
        });

        // 更新状态
        const typedResult = result as { success?: boolean; error?: string };
        workflowStatus.status = typedResult.success ? 'completed' : 'failed';
        workflowStatus.progress = 100;
        workflowStatus.endTime = Date.now();
        workflowStatus.error = typedResult.error;

        setWorkflowStatuses((prev) => new Map(prev).set(executionId, workflowStatus));

        // 添加完成消息
        const completeMessage: Message = {
          id: `msg_complete_${Date.now()}`,
          type: typedResult.success ? 'text' : 'error',
          content: typedResult.success
            ? `工作流执行完成: ${workflowName}`
            : `工作流执行失败: ${typedResult.error || '未知错误'}`,
          sender: '系统',
          senderId: 'system',
          timestamp: Date.now(),
          status: 'sent',
          metadata: {
            workflowName,
            executionId,
          },
        };

        setMessages((prev) => [...prev, completeMessage]);
        saveMessage(currentSessionId, completeMessage);
      } catch (error: any) {
        workflowStatus.status = 'failed';
        workflowStatus.error = error.message || '执行失败';
        workflowStatus.endTime = Date.now();

        setWorkflowStatuses((prev) => new Map(prev).set(executionId, workflowStatus));

        const errorMessage: Message = {
          id: `msg_error_${Date.now()}`,
          type: 'error',
          content: `工作流执行失败: ${workflowStatus.error}`,
          sender: '系统',
          senderId: 'system',
          timestamp: Date.now(),
          status: 'sent',
          metadata: {
            workflowName,
            executionId,
          },
        };

        setMessages((prev) => [...prev, errorMessage]);
        saveMessage(currentSessionId, errorMessage);
      }
    },
    [currentSessionId]
  );

  // 执行工具
  const executeTool = useCallback(
    async (toolName: string, userId: string, username: string) => {
      if (!currentSessionId) return;

      const executionId = `tool_exec_${Date.now()}`;

      // 创建工具执行消息
      const toolMessage: Message = {
        id: `msg_tool_${Date.now()}`,
        type: 'tool',
        content: `正在执行工具: ${toolName}`,
        sender: '系统',
        senderId: 'system',
        timestamp: Date.now(),
        status: 'sent',
        metadata: {
          toolName,
          executionId,
        },
      };

      setMessages((prev) => [...prev, toolMessage]);
      saveMessage(currentSessionId, toolMessage);

      // 初始化工具状态
      const toolStatus: ToolExecutionStatus = {
        toolName,
        executionId,
        status: 'running',
        startTime: Date.now(),
      };

      setToolStatuses((prev) => new Map(prev).set(executionId, toolStatus));

      try {
        // 执行工具
        const result = await mcpGatewayClient.post(`/api/tools/${toolName}/execute`, {
          parameters: {},
          timeout: 30,
        });

        const typedToolResult = result as { success?: boolean; result?: any; error?: string };
        toolStatus.status = typedToolResult.success ? 'completed' : 'failed';
        toolStatus.result = typedToolResult.result;
        toolStatus.error = typedToolResult.error;
        toolStatus.endTime = Date.now();

        setToolStatuses((prev) => new Map(prev).set(executionId, toolStatus));

        // 添加完成消息
        const completeMessage: Message = {
          id: `msg_tool_complete_${Date.now()}`,
          type: typedToolResult.success ? 'text' : 'error',
          content: typedToolResult.success
            ? `工具执行完成: ${toolName}\n结果: ${JSON.stringify(typedToolResult.result, null, 2)}`
            : `工具执行失败: ${typedToolResult.error || '未知错误'}`,
          sender: '系统',
          senderId: 'system',
          timestamp: Date.now(),
          status: 'sent',
          metadata: {
            toolName,
            executionId,
          },
        };

        setMessages((prev) => [...prev, completeMessage]);
        saveMessage(currentSessionId, completeMessage);
      } catch (error: any) {
        toolStatus.status = 'failed';
        toolStatus.error = error.message || '执行失败';
        toolStatus.endTime = Date.now();

        setToolStatuses((prev) => new Map(prev).set(executionId, toolStatus));

        const errorMessage: Message = {
          id: `msg_tool_error_${Date.now()}`,
          type: 'error',
          content: `工具执行失败: ${toolStatus.error}`,
          sender: '系统',
          senderId: 'system',
          timestamp: Date.now(),
          status: 'sent',
          metadata: {
            toolName,
            executionId,
          },
        };

        setMessages((prev) => [...prev, errorMessage]);
        saveMessage(currentSessionId, errorMessage);
      }
    },
    [currentSessionId]
  );

  // 处理文本消息（可以集成AI回复）
  const handleTextMessage = useCallback(
    async (content: string, userId: string, username: string) => {
      // AI回复逻辑已集成到智能路由中，这里不再需要占位消息
      // 消息会通过智能路由系统处理
    },
    [currentSessionId]
  );

  // 创建新会话
  const createNewSession = useCallback((title: string = '新会话') => {
    const session = createSession(title);
    setSessions((prev) => [session, ...prev]);
    setCurrentSessionId(session.id);
    setMessages([]);
    // 持久化当前会话ID到localStorage
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('chat_current_session_id', session.id);
      } catch (e) {
        console.warn('[useChat] Failed to save new sessionId:', e);
      }
    }
  }, []);

  // 切换会话
  const switchSession = useCallback((sid: string) => {
    setCurrentSessionId(sid);
  }, []);

  // 删除会话
  const removeSession = useCallback(
    (sid: string) => {
      deleteSession(sid);
      setSessions((prev) => {
        const updated = prev.filter((s) => s.id !== sid);
        if (currentSessionId === sid) {
          setCurrentSessionId(updated.length > 0 ? updated[0].id : null);
          setMessages([]);
        }
        return updated;
      });
    },
    [currentSessionId]
  );

  // 重发消息
  const resendMessage = useCallback(
    (messageId: string) => {
      if (!currentSessionId) return;

      const message = messages.find((m) => m.id === messageId);
      if (message && message.type === 'text') {
        // 删除旧消息
        deleteMessage(currentSessionId, messageId);
        setMessages((prev) => prev.filter((m) => m.id !== messageId));

        // 重新发送
        sendMessage(message.content, message.senderId, message.sender);
      }
    },
    [messages, currentSessionId, sendMessage]
  );

  // 删除消息
  const removeMessage = useCallback(
    (messageId: string) => {
      if (!currentSessionId) return;

      deleteMessage(currentSessionId, messageId);
      setMessages((prev) => prev.filter((m) => m.id !== messageId));
    },
    [currentSessionId]
  );

  // 获取当前会话
  const currentSession = sessions.find((s) => s.id === currentSessionId);

  return {
    sessions,
    currentSessionId,
    currentSession,
    messages,
    loading,
    sending,
    workflowStatuses,
    toolStatuses,
    messagesEndRef,
    sendMessage,
    createNewSession,
    switchSession,
    removeSession,
    resendMessage,
    removeMessage,
    loadSessions,
  };
}
