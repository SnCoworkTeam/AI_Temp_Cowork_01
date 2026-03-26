'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useChat } from '@/hooks/useChat';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { ChatSidebar } from './ChatSidebar';
import { AuthGuard } from './AuthGuard';
import { KnowledgeSidebar } from './ChatInterface/index';
import { DynamicWorkflowDisplay } from './DynamicWorkflowDisplay';
import { knowledgeApi } from '@/lib/api/knowledge';
import { Message } from '@/types/chat';
import { listWorkflows, executeWorkflowById, WorkflowListItem } from '@/lib/api/workflow';
import { getSessionMessages, saveMessage, updateMessage } from '@/lib/chat';
import { executeDAGTask, getDAGExecutionStatus, DAGExecutionRequest } from '@/lib/api/dag';
import { agentChat, IntelligentChatRequest } from '@/lib/api/chat';
import { executeDynamicWorkflow, WorkflowChunk } from '@/lib/api/dynamic-workflow';
import '@/app/message-styles.css';

interface ChatInterfaceProps {
  sessionId?: string;
}

export function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const { user } = useAuth();
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
  } = useChat({ sessionId, autoScroll: true });

  // 维护本地消息state，用于实时流式更新
  const [messages, setMessages] = useState<Message[]>(messagesFromHook);
  // 跟踪正在流式更新的消息ID，避免被hook的消息覆盖
  const streamingMessageIdsRef = useRef<Set<string>>(new Set());

  // 当hook中的消息变化时，智能合并到本地state（保留流式更新中的消息）
  useEffect(() => {
    setMessages((prev) => {
      // 如果有正在流式更新的消息，保留它们的最新内容
      const streamingIds = streamingMessageIdsRef.current;

      if (streamingIds.size === 0) {
        // 没有流式更新，直接使用hook的消息
        return messagesFromHook;
      }

      // 有流式更新，需要合并
      const merged: Message[] = [];
      const hookMessageMap = new Map(messagesFromHook.map((m) => [m.id, m]));
      const prevMessageMap = new Map(prev.map((m) => [m.id, m]));

      // 合并策略：
      // 1. 对于流式更新中的消息，使用本地state的最新内容
      // 2. 对于其他消息，使用hook的消息（可能更新了状态等）
      // 3. 保持消息顺序（按timestamp排序）
      // 4. 确保所有消息都被保留，不会丢失

      const allMessageIds = new Set([
        ...messagesFromHook.map((m) => m.id),
        ...prev.map((m) => m.id),
      ]);

      const sortedIds = Array.from(allMessageIds).sort((a, b) => {
        const msgA = prevMessageMap.get(a) || hookMessageMap.get(a);
        const msgB = prevMessageMap.get(b) || hookMessageMap.get(b);
        return (msgA?.timestamp || 0) - (msgB?.timestamp || 0);
      });

      for (const id of sortedIds) {
        if (streamingIds.has(id)) {
          // 流式更新中的消息，使用本地state的最新内容
          const localMsg = prevMessageMap.get(id);
          if (localMsg) {
            merged.push(localMsg);
          }
        } else {
          // 其他消息，使用hook的消息（优先）或本地消息（如果hook中没有）
          const hookMsg = hookMessageMap.get(id);
          const localMsg = prevMessageMap.get(id);
          if (hookMsg) {
            merged.push(hookMsg);
          } else if (localMsg) {
            // 如果hook中没有但本地有，保留本地消息（可能是刚保存但还没从hook加载）
            merged.push(localMsg);
          }
        }
      }

      return merged;
    });
  }, [messagesFromHook]);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [knowledgeSidebarOpen, setKnowledgeSidebarOpen] = useState(false);
  const [knowledgeQuery, setKnowledgeQuery] = useState<string>('');
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
  const [workflowExecutions, setWorkflowExecutions] = useState<Map<string, any>>(new Map());
  const [showWorkflowInput, setShowWorkflowInput] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [useDynamicWorkflow, setUseDynamicWorkflow] = useState(true); // 默认使用动态工作流
  const [workflowChunks, setWorkflowChunks] = useState<Map<string, WorkflowChunk[]>>(new Map());
  const chatUpdateTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 加载工作流列表
  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const response = await listWorkflows();
      setWorkflows(response.workflows || []);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    }
  };

  const handleSend = async (content: string) => {
    if (!user) return;

    // 保留命令前缀支持（向后兼容），但优先使用智能路由
    // 如果用户明确使用命令前缀，则执行命令逻辑
    if (content.startsWith('/workflow ') || content.startsWith('/wf ')) {
      const workflowNameOrId = content.replace(/^\/workflow\s+|\/wf\s+/, '').trim();

      // 先发送用户消息
      sendMessage(content, user.user_id, user.username);

      // 查找工作流
      const workflow = workflows.find(
        (w) =>
          w.workflow_id === workflowNameOrId ||
          w.name === workflowNameOrId ||
          w.name.toLowerCase().includes(workflowNameOrId.toLowerCase())
      );

      if (workflow) {
        setCurrentWorkflowId(workflow.workflow_id);
        setShowWorkflowInput(true);
      } else {
        const availableWorkflows = workflows
          .slice(0, 5)
          .map((w) => `- ${w.name} (ID: ${w.workflow_id.substring(0, 8)}...)`)
          .join('\n');
        sendMessage(
          `❌ 未找到工作流: ${workflowNameOrId}\n\n可用工作流:\n${availableWorkflows || '暂无可用工作流'}`,
          'system',
          '系统'
        );
      }
      return;
    }

    // 检查是否是知识库搜索命令（保留向后兼容）
    if (content.startsWith('/kb ') || content.startsWith('/knowledge ')) {
      const query = content.replace(/^\/kb\s+|\/knowledge\s+/, '');
      setKnowledgeQuery(query);
      setKnowledgeSidebarOpen(true);

      // 同时执行搜索并在聊天中显示
      try {
        const searchResponse = await knowledgeApi.semanticSearch(query, 5);
        const aiResponse = `基于知识库搜索"${query}"的结果:\n\n${searchResponse.results
          .slice(0, 3)
          .map((r, i) => `${i + 1}. ${r.content.substring(0, 200)}...`)
          .join('\n\n')}`;

        sendMessage(content, user.user_id, user.username);
        sendMessage(aiResponse, 'ai', 'AI助手');
      } catch (error) {
        console.error('Knowledge search failed:', error);
        sendMessage(content, user.user_id, user.username);
      }
      return;
    }

    // 使用智能路由处理所有消息（包括原来的/dag命令）
    // 先发送用户消息
    sendMessage(content, user.user_id, user.username);

    // 如果启用动态工作流，使用动态工作流执行
    if (useDynamicWorkflow) {
      await handleDynamicWorkflow(content, user);
      return;
    }

    // 创建AI回复消息（用于流式更新）- 移到try块外，确保catch块可以访问
    const aiMessageId = `ai-${Date.now()}`;
    let aiMessageContent = '🤔 正在分析您的请求...';
    let currentProgress = 0;

    try {
      const aiMessage: Message = {
        id: aiMessageId,
        type: 'text',
        content: aiMessageContent,
        sender: 'AI助手',
        senderId: 'ai',
        timestamp: Date.now(),
        status: 'sending',
      };

      // 标记为流式更新中
      streamingMessageIdsRef.current.add(aiMessageId);

      // 使用sendMessage添加初始消息
      // 然后通过updateMessage实时更新
      if (currentSessionId) {
        saveMessage(currentSessionId, aiMessage);
        // 立即添加到React state，确保消息显示
        setMessages((prev) => {
          // 检查是否已存在，避免重复
          if (prev.find((m) => m.id === aiMessageId)) {
            return prev;
          }
          return [...prev, aiMessage];
        });
        // 触发消息列表更新
        switchSession(currentSessionId);
      }

      // 构建对话历史（最近5条消息）
      const recentMessages = messages
        .filter((m) => m.type === 'text' && m.senderId !== 'system')
        .slice(-5)
        .map((m) => ({
          role: m.senderId === user.user_id ? 'user' : 'assistant',
          content: m.content,
        }));

      // 构建智能聊天请求
      const chatRequest = {
        message: content,
        conversation_history: recentMessages,
        user_context: {
          user_id: user.user_id,
          username: user.username,
        },
      };

      // 使用流式请求
      const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      const requestUrl = `${API_GATEWAY_URL}/api/chat/intelligent/stream`;

      console.log('[Chat] Sending request to:', requestUrl);
      console.log('[Chat] Request body:', chatRequest);

      let response: Response;
      try {
        response = await fetch(requestUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
          },
          body: JSON.stringify(chatRequest),
        });
      } catch (fetchError: any) {
        console.error('[Chat] Fetch error:', fetchError);
        throw new Error(`网络请求失败: ${fetchError?.message || '无法连接到服务器'}`);
      }

      console.log('[Chat] Response status:', response.status, response.statusText);
      console.log('[Chat] Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text().catch(() => '');
        console.error('[Chat] Response error:', response.status, errorText);
        throw new Error(
          `HTTP错误! 状态: ${response.status}, 详情: ${errorText || response.statusText}`
        );
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      // 读取流式数据
      let buffer = '';
      console.log('[Chat] Starting to read stream...');

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log('[Chat] Stream reading done');
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        console.log(
          '[Chat] Received chunk:',
          chunk.substring(0, 100) + (chunk.length > 100 ? '...' : '')
        );

        // 处理完整的行（SSE格式：data: {...}\n\n）
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保留最后一个不完整的行

        for (const line of lines) {
          if (line.trim() === '') continue; // 跳过空行

          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.substring(6);
              console.log('[Chat] Parsing SSE data:', jsonStr.substring(0, 200));
              const data = JSON.parse(jsonStr);
              console.log('[Chat] Parsed data type:', data.type);

              // 处理不同类型的流式消息
              switch (data.type) {
                case 'start':
                  // 只在第一次收到start时初始化，后续不覆盖
                  if (!aiMessageContent || aiMessageContent === '🤔 正在分析您的请求...') {
                    aiMessageContent = '🔄 开始处理...\n\n';
                  }
                  break;

                case 'step':
                  if (data.step) {
                    // 保留之前的步骤信息，追加新步骤（不覆盖）
                    const stepInfo = `📋 ${data.step}: ${data.data?.status || '处理中'}\n`;
                    // 检查是否已经显示过这个步骤，避免重复
                    if (!aiMessageContent.includes(stepInfo.trim())) {
                      aiMessageContent += stepInfo;
                    }
                    if (data.data?.task_type) {
                      const intentLine = `   意图: ${data.data.task_type}\n`;
                      if (!aiMessageContent.includes(intentLine.trim())) {
                        aiMessageContent += intentLine;
                      }
                    }
                    if (data.data?.strategy) {
                      const strategyLine = `   策略: ${data.data.strategy}\n`;
                      if (!aiMessageContent.includes(strategyLine.trim())) {
                        aiMessageContent += strategyLine;
                      }
                    }
                  }
                  currentProgress = data.progress || currentProgress;
                  break;

                case 'chunk':
                  if (data.data?.chunk) {
                    // 直接追加chunk内容，确保不丢失任何内容
                    // 不进行任何检查，直接追加，因为chunk是流式的，不应该重复检查
                    aiMessageContent += data.data.chunk;
                    console.log(
                      '[Chat] Appended chunk, current content length:',
                      aiMessageContent.length
                    );
                  }
                  currentProgress = data.progress || currentProgress;
                  break;

                case 'progress':
                  currentProgress = data.progress || currentProgress;
                  break;

                case 'complete':
                  // 保留所有之前的流式内容（包括所有步骤信息），只在最后添加最终响应（如果还没有）
                  console.log(
                    '[Chat] Complete event received, current content length:',
                    aiMessageContent.length
                  );
                  console.log('[Chat] Complete data:', JSON.stringify(data.data).substring(0, 200));

                  // 保存当前内容（包含所有步骤信息）的备份，防止被覆盖
                  const contentBeforeComplete = aiMessageContent;

                  let hasNewContent = false;

                  if (data.data?.result?.response) {
                    const finalResponse = data.data.result.response;
                    console.log('[Chat] Final response length:', finalResponse.length);
                    // 检查最终响应是否已经在内容中（避免重复）
                    // 使用更宽松的检查：如果响应很长，只检查开头和结尾
                    const responseStart = finalResponse.substring(
                      0,
                      Math.min(100, finalResponse.length)
                    );
                    const responseEnd =
                      finalResponse.length > 100
                        ? finalResponse.substring(finalResponse.length - 100)
                        : '';

                    // 检查是否已经包含（检查开头和结尾，更准确）
                    const alreadyIncluded =
                      responseStart &&
                      aiMessageContent.includes(responseStart) &&
                      (responseEnd ? aiMessageContent.includes(responseEnd) : true);

                    if (finalResponse && !alreadyIncluded) {
                      // 如果当前内容以步骤信息结尾，添加换行
                      if (!aiMessageContent.endsWith('\n\n') && !aiMessageContent.endsWith('\n')) {
                        aiMessageContent += '\n\n';
                      }
                      // 追加最终响应，但保留所有之前的步骤信息
                      aiMessageContent += finalResponse;
                      hasNewContent = true;
                      console.log(
                        '[Chat] Appended final response, new content length:',
                        aiMessageContent.length
                      );
                    } else {
                      console.log('[Chat] Final response already included, skipping');
                    }
                  } else if (data.data?.result) {
                    // 如果没有response，检查raw_result中是否有output
                    const result = data.data.result;
                    const rawResult = result.raw_result || {};
                    const output = rawResult.output || rawResult.response || rawResult.result;
                    if (output && typeof output === 'string') {
                      console.log('[Chat] Output found, length:', output.length);
                      // 检查输出是否已经在内容中（使用更宽松的检查）
                      const outputStart = output.substring(0, Math.min(100, output.length));
                      const outputEnd =
                        output.length > 100 ? output.substring(output.length - 100) : '';
                      const alreadyIncluded =
                        outputStart &&
                        aiMessageContent.includes(outputStart) &&
                        (outputEnd ? aiMessageContent.includes(outputEnd) : true);

                      if (!alreadyIncluded) {
                        if (
                          !aiMessageContent.endsWith('\n\n') &&
                          !aiMessageContent.endsWith('\n')
                        ) {
                          aiMessageContent += '\n\n';
                        }
                        // 追加输出，但保留所有之前的步骤信息
                        aiMessageContent += output;
                        hasNewContent = true;
                        console.log(
                          '[Chat] Appended output, new content length:',
                          aiMessageContent.length
                        );
                      } else {
                        console.log('[Chat] Output already included, skipping');
                      }
                    }
                  }

                  // 如果complete事件没有提供新内容，但当前内容仍然是初始状态，至少保留步骤信息
                  if (!hasNewContent && aiMessageContent === '🤔 正在分析您的请求...') {
                    aiMessageContent = '🔄 处理完成';
                    console.log('[Chat] No new content, set to default completion message');
                  }

                  // 确保内容包含所有步骤信息（如果被意外覆盖，恢复备份）
                  if (
                    contentBeforeComplete &&
                    contentBeforeComplete.length > aiMessageContent.length
                  ) {
                    console.warn('[Chat] Content was truncated, restoring from backup');
                    aiMessageContent = contentBeforeComplete;
                    if (hasNewContent) {
                      // 如果确实有新内容，追加到备份内容后面
                      if (!aiMessageContent.endsWith('\n\n') && !aiMessageContent.endsWith('\n')) {
                        aiMessageContent += '\n\n';
                      }
                      // 这里需要重新获取最终响应并追加
                      if (data.data?.result?.response) {
                        aiMessageContent += data.data.result.response;
                      }
                    }
                  }

                  console.log(
                    '[Chat] Final content after complete:',
                    aiMessageContent.substring(0, 200)
                  );
                  console.log('[Chat] Full content length:', aiMessageContent.length);

                  // 确保最终消息已保存（包含所有步骤信息和最终结果）
                  if (currentSessionId && aiMessageId) {
                    // 强制保存完整内容到localStorage
                    updateMessage(currentSessionId, aiMessageId, {
                      content: aiMessageContent, // 确保保存完整内容
                      status: 'sent',
                    });
                    // 确保消息在state中
                    setMessages((prev) => {
                      const existingIndex = prev.findIndex((m) => m.id === aiMessageId);
                      if (existingIndex >= 0) {
                        const updated = [...prev];
                        updated[existingIndex] = {
                          ...updated[existingIndex],
                          content: aiMessageContent,
                          status: 'sent',
                        };
                        return updated;
                      }
                      return prev;
                    });

                    // 额外保存一次，确保localStorage中有完整内容
                    const finalMessage = {
                      id: aiMessageId,
                      type: 'text' as const,
                      content: aiMessageContent,
                      sender: 'AI助手',
                      senderId: 'ai',
                      timestamp: Date.now(),
                      status: 'sent' as const,
                    };
                    saveMessage(currentSessionId, finalMessage);
                  }

                  // 标记流式更新完成
                  streamingMessageIdsRef.current.delete(aiMessageId);
                  // 确保消息状态更新为sent
                  break;

                case 'error':
                  // 错误信息追加，不覆盖之前的内容
                  const errorMsg = data.data?.error || data.data?.message || '未知错误';
                  // 检查是否已经包含这个错误信息（避免重复）
                  if (!aiMessageContent.includes(errorMsg)) {
                    // 如果当前内容不为空且不是初始状态，添加换行
                    if (
                      aiMessageContent &&
                      aiMessageContent !== '🤔 正在分析您的请求...' &&
                      !aiMessageContent.endsWith('\n\n')
                    ) {
                      aiMessageContent += '\n\n';
                    }
                    aiMessageContent += `❌ 错误: ${errorMsg}`;
                  }
                  // 确保错误消息已保存
                  if (currentSessionId && aiMessageId) {
                    updateMessage(currentSessionId, aiMessageId, {
                      content: aiMessageContent,
                      status: 'sent',
                    });
                    // 确保消息在state中
                    setMessages((prev) => {
                      const existingIndex = prev.findIndex((m) => m.id === aiMessageId);
                      if (existingIndex >= 0) {
                        const updated = [...prev];
                        updated[existingIndex] = {
                          ...updated[existingIndex],
                          content: aiMessageContent,
                          status: 'sent',
                        };
                        return updated;
                      }
                      return prev;
                    });
                  }

                  // 标记流式更新完成（即使有错误）
                  streamingMessageIdsRef.current.delete(aiMessageId);
                  // 确保消息状态更新为sent，即使有错误也要显示
                  break;
              }

              // 更新消息内容 - 直接更新React state以实现实时流式显示
              // 每次收到数据都更新，确保不丢失任何内容（包括所有中间步骤）
              if (currentSessionId && aiMessageId) {
                // 更新 localStorage（每次更新都保存，确保中间步骤不丢失）
                try {
                  updateMessage(currentSessionId, aiMessageId, {
                    content: aiMessageContent, // 保存完整的当前内容（包含所有步骤）
                    status: data.type === 'complete' || data.type === 'error' ? 'sent' : 'sending',
                  });
                  // 额外验证：确保保存成功
                  const savedMessages = getSessionMessages(currentSessionId);
                  const savedMsg = savedMessages.find((m) => m.id === aiMessageId);
                  if (savedMsg && savedMsg.content.length < aiMessageContent.length) {
                    console.warn('[Chat] Saved content is shorter than current, re-saving...');
                    // 如果保存的内容被截断，重新保存
                    updateMessage(currentSessionId, aiMessageId, {
                      content: aiMessageContent,
                      status:
                        data.type === 'complete' || data.type === 'error' ? 'sent' : 'sending',
                    });
                  }
                } catch (e) {
                  console.warn('[Chat] Failed to update localStorage:', e);
                  // 如果更新失败，尝试直接保存整个消息
                  try {
                    const fullMessage: Message = {
                      id: aiMessageId,
                      type: 'text',
                      content: aiMessageContent,
                      sender: 'AI助手',
                      senderId: 'ai',
                      timestamp: Date.now(),
                      status:
                        data.type === 'complete' || data.type === 'error' ? 'sent' : 'sending',
                    };
                    saveMessage(currentSessionId, fullMessage);
                  } catch (saveError) {
                    console.error('[Chat] Failed to save message as fallback:', saveError);
                  }
                }

                // 直接更新React state中的消息，实现实时流式显示
                // 使用函数式更新，确保基于最新状态
                setMessages((prev) => {
                  const existingIndex = prev.findIndex((m) => m.id === aiMessageId);

                  if (existingIndex >= 0) {
                    // 消息已存在，更新它
                    const updated = [...prev];
                    updated[existingIndex] = {
                      ...updated[existingIndex],
                      content: aiMessageContent, // 直接使用最新的完整内容
                      status:
                        data.type === 'complete' || data.type === 'error' ? 'sent' : 'sending',
                    };
                    console.log(
                      '[Chat] Updated existing message, content length:',
                      aiMessageContent.length
                    );
                    return updated;
                  } else {
                    // 消息不存在，添加它
                    const newMessage = {
                      id: aiMessageId,
                      type: 'text' as const,
                      content: aiMessageContent,
                      sender: 'AI助手',
                      senderId: 'ai',
                      timestamp: Date.now(),
                      status: (data.type === 'complete' || data.type === 'error'
                        ? 'sent'
                        : 'sending') as 'sending' | 'sent' | 'failed',
                    };
                    console.log(
                      '[Chat] Added new message, content length:',
                      aiMessageContent.length
                    );
                    return [...prev, newMessage];
                  }
                });
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e, line);
            }
          }
        }
      }
    } catch (error: any) {
      console.error('[Chat] Streaming chat error:', error);
      console.error('[Chat] Error details:', {
        message: error?.message,
        stack: error?.stack,
        name: error?.name,
        cause: error?.cause,
      });

      // 更新AI消息显示错误，但保留之前的所有内容（追加错误信息，不替换）
      if (currentSessionId && aiMessageId) {
        // 标记流式更新完成
        streamingMessageIdsRef.current.delete(aiMessageId);

        // 获取当前消息内容（如果存在）
        const currentMessages = messages.filter((m) => m.id === aiMessageId);
        const currentContent =
          currentMessages.length > 0
            ? currentMessages[0].content
            : aiMessageContent || '🤔 正在分析您的请求...';

        // 如果当前内容不是初始状态，追加错误信息
        let finalContent = currentContent;
        const errorMessage = `❌ 处理失败: ${error?.message || '网络错误，请稍后重试'}`;

        // 检查是否已经包含错误信息（避免重复）
        if (!finalContent.includes(errorMessage)) {
          // 如果当前内容不为空且不是初始状态，添加换行
          if (
            finalContent &&
            finalContent !== '🤔 正在分析您的请求...' &&
            !finalContent.endsWith('\n\n')
          ) {
            finalContent += '\n\n';
          }
          finalContent += errorMessage;
        }

        updateMessage(currentSessionId, aiMessageId, {
          content: finalContent,
          status: 'sent', // 即使有错误也标记为sent，确保显示
        });
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiMessageId ? { ...msg, content: finalContent, status: 'sent' } : msg
          )
        );
        saveMessage(currentSessionId, {
          id: aiMessageId,
          type: 'text', // 保持为text类型，即使有错误
          content: finalContent,
          sender: 'AI助手',
          senderId: 'ai',
          timestamp: Date.now(),
          status: 'sent', // 标记为sent，确保显示
        });
      } else {
        sendMessage(`❌ 处理失败: ${error?.message || '网络错误，请稍后重试'}`, 'system', '系统');
      }
    }
  };

  // 执行工作流
  const handleExecuteWorkflow = async (workflowId: string, inputData: Record<string, any>) => {
    if (!user || !currentSessionId) return;

    setExecuting(true);
    setCurrentWorkflowId(workflowId);
    setShowWorkflowInput(false);

    try {
      const workflowName = workflows.find((w) => w.workflow_id === workflowId)?.name || '工作流';

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
      };

      // 直接添加到消息列表
      if (currentSessionId) {
        saveMessage(currentSessionId, workflowStartMessage);
        // 触发消息列表更新
        switchSession(currentSessionId);
      }

      const result = await executeWorkflowById(workflowId, inputData);

      // 存储执行结果
      setWorkflowExecutions((prev) => {
        const newMap = new Map(prev);
        newMap.set(workflowId, result);
        return newMap;
      });

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
      };

      // 直接添加到消息列表
      if (currentSessionId) {
        saveMessage(currentSessionId, workflowResultMessage);
        // 触发消息列表更新
        switchSession(currentSessionId);
      }
    } catch (error: any) {
      console.error('Workflow execution failed:', error);
      sendMessage(`❌ 工作流执行失败: ${error?.message || '未知错误'}`, 'system', '系统');
    } finally {
      setExecuting(false);
    }
  };

  // 安全的JSON序列化函数，避免循环引用
  const safeStringify = (obj: any): string => {
    const seen = new WeakSet();
    try {
      return JSON.stringify(
        obj,
        (key, value) => {
          // 移除循环引用
          if (typeof value === 'object' && value !== null) {
            if (seen.has(value)) {
              return '[Circular]';
            }
            seen.add(value);
          }
          // 移除函数和DOM元素
          if (typeof value === 'function' || value instanceof HTMLElement) {
            return undefined;
          }
          return value;
        },
        2
      );
    } catch (error) {
      console.error('JSON stringify error:', error);
      return String(obj);
    }
  };

  // 格式化工作流结果（安全序列化，避免循环引用）
  const formatWorkflowResult = (result: any): string => {
    if (!result) return '无结果';

    const llmResult =
      result['LLM节点_result'] ||
      result['LLM节点_output']?.content ||
      result.LLM节点_result ||
      result.LLM节点_output?.content;

    if (llmResult) {
      return String(llmResult);
    }

    if (result.final_result) {
      return typeof result.final_result === 'string'
        ? result.final_result
        : safeStringify(result.final_result);
    }

    return safeStringify(result);
  };

  const handleKnowledgeSearch = (query: string) => {
    setKnowledgeQuery(query);
    setKnowledgeSidebarOpen(true);
    handleSend(`/kb ${query}`);
  };

  const handleDynamicWorkflow = async (content: string, user: any) => {
    if (!currentSessionId) {
      console.error('[DynamicWorkflow] No current session ID');
      return;
    }

    console.log('[DynamicWorkflow] Starting workflow execution for:', content.substring(0, 50));

    try {
      setExecuting(true);

      // 创建AI回复消息（用于显示动态工作流）
      const aiMessageId = `ai-${Date.now()}`;
      const workflowMessageId = `workflow-${aiMessageId}`;

      // 初始化工作流chunks
      const chunks: WorkflowChunk[] = [];
      setWorkflowChunks((prev) => new Map(prev).set(workflowMessageId, chunks));

      let messageContent = '💭 正在分析您的请求...';

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
          workflowType: 'dynamic',
        },
      };

      // 标记为流式更新中，防止被hook的消息覆盖
      streamingMessageIdsRef.current.add(aiMessageId);

      // 保存消息并立即更新本地state
      if (currentSessionId) {
        saveMessage(currentSessionId, aiMessage);
        // 立即添加到本地state，确保消息显示
        setMessages((prev) => {
          // 检查是否已存在，避免重复
          if (prev.find((m) => m.id === aiMessageId)) {
            return prev;
          }
          return [...prev, aiMessage];
        });
        // 不要调用switchSession，避免重新加载消息导致丢失
        // switchSession(currentSessionId)
      }

      // 执行动态工作流（流式）
      console.log('[DynamicWorkflow] Starting stream execution...');

      // 更新初始消息内容
      updateMessage(currentSessionId, aiMessageId, {
        content: messageContent,
        status: 'sending',
      });
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMessageId ? { ...m, content: messageContent, status: 'sending' } : m
        )
      );

      try {
        let chunkCount = 0;
        for await (const chunk of executeDynamicWorkflow({
          user_input: content,
          context: {
            user_id: user.user_id,
            username: user.username,
            session_id: currentSessionId,
          },
          stream: true,
        })) {
          chunkCount++;
          console.log(`[DynamicWorkflow] Received chunk ${chunkCount}:`, chunk.type, chunk.stage);

          // 更新chunks
          chunks.push(chunk);
          setWorkflowChunks((prev) => {
            const newMap = new Map(prev);
            newMap.set(workflowMessageId, [...chunks]);
            return newMap;
          });

          // 实时更新消息内容，显示进度
          let shouldUpdate = false;

          if (chunk.type === 'thinking') {
            if (chunk.message) {
              messageContent = `💡 ${chunk.message}`;
              if (chunk.progress) {
                messageContent += ` (${chunk.progress}%)`;
              }
              shouldUpdate = true;
            }
          } else if (chunk.type === 'design') {
            if (chunk.stage === 'network_designed' && chunk.network_summary) {
              messageContent = `✨ 智能体网络设计完成：${chunk.network_summary.total_agents}个智能体，${chunk.network_summary.execution_layers}个执行层`;
              shouldUpdate = true;
            } else if (chunk.message) {
              messageContent = `✨ ${chunk.message}`;
              shouldUpdate = true;
            }
          } else if (chunk.type === 'execution') {
            if (chunk.stage === 'layer_start') {
              messageContent = `⚡ 执行第${chunk.layer_number}/${chunk.total_layers}层：${chunk.message || ''}`;
              shouldUpdate = true;
            } else if (chunk.stage === 'agent_start') {
              messageContent = `   • ${chunk.agent_type || chunk.agent_id}：${chunk.agent_task || ''}`;
              shouldUpdate = true;
            } else if (chunk.stage === 'agent_complete') {
              const time = chunk.agent_result?.execution_time || 0;
              const status = chunk.agent_result?.success ? '✓' : '✗';
              messageContent = `   ${status} ${chunk.agent_id} 完成 (${time.toFixed(2)}s)`;
              shouldUpdate = true;
            } else if (chunk.stage === 'execution_complete') {
              console.log(
                '[DynamicWorkflow] Execution complete, final_result:',
                chunk.final_result
              );
              // 执行完成时，只显示完成提示，最终结果会在DynamicWorkflowDisplay组件中显示
              messageContent = `✅ 分析完成`;
              shouldUpdate = true;
            } else if (chunk.message) {
              messageContent = `⚡ ${chunk.message}`;
              shouldUpdate = true;
            }
          } else if (chunk.type === 'error') {
            // 优先使用message，其次使用error，最后使用默认消息
            // 处理空字符串的情况
            const errorMsg =
              (chunk.message && chunk.message.trim()) ||
              (chunk.error && chunk.error.trim()) ||
              chunk.error_type ||
              '未知错误';
            messageContent = `⚠️ 错误: ${errorMsg}`;
            // 如果有stage信息，添加到错误消息中
            if (chunk.stage) {
              messageContent += ` (阶段: ${chunk.stage})`;
            }
            // 如果有error_type，也添加到消息中
            if (chunk.error_type && chunk.error_type !== errorMsg) {
              messageContent += ` [${chunk.error_type}]`;
            }
            shouldUpdate = true;
            console.error('[DynamicWorkflow] Error chunk received:', chunk);
          }

          // 实时更新消息内容
          if (shouldUpdate) {
            // 安全地记录日志
            const logContent =
              typeof messageContent === 'string'
                ? messageContent.substring(0, 100)
                : String(messageContent).substring(0, 100);
            console.log(`[DynamicWorkflow] Updating message content:`, logContent);
            console.log(`[DynamicWorkflow] Message ID:`, aiMessageId);

            // 更新localStorage
            updateMessage(currentSessionId, aiMessageId, {
              content: messageContent,
              status:
                chunk.type === 'execution_complete' || chunk.type === 'error' ? 'sent' : 'sending',
            });

            // 强制更新React state，确保UI刷新
            setMessages((prev) => {
              const messageExists = prev.find((m) => m.id === aiMessageId);
              if (!messageExists) {
                console.warn(
                  `[DynamicWorkflow] Message ${aiMessageId} not found in state, adding it`
                );
                const messageStatus: 'sending' | 'sent' | 'failed' =
                  chunk.type === 'execution_complete' || chunk.type === 'error'
                    ? 'sent'
                    : 'sending';
                return [
                  ...prev,
                  {
                    id: aiMessageId,
                    type: 'text' as const,
                    content:
                      typeof messageContent === 'string' ? messageContent : String(messageContent),
                    sender: 'AI助手',
                    senderId: 'ai',
                    timestamp: Date.now(),
                    status: messageStatus,
                    metadata: {
                      workflowMessageId,
                      workflowType: 'dynamic',
                    },
                  },
                ];
              }

              const updated = prev.map((m) => {
                if (m.id === aiMessageId) {
                  const messageStatus: 'sending' | 'sent' | 'failed' =
                    chunk.type === 'execution_complete' || chunk.type === 'error'
                      ? 'sent'
                      : 'sending';
                  return {
                    ...m,
                    content:
                      typeof messageContent === 'string' ? messageContent : String(messageContent),
                    status: messageStatus,
                  };
                }
                return m;
              });
              const foundMessage = updated.find((m) => m.id === aiMessageId);
              // 安全地记录日志
              if (foundMessage?.content) {
                const logContent =
                  typeof foundMessage.content === 'string'
                    ? foundMessage.content.substring(0, 50)
                    : String(foundMessage.content).substring(0, 50);
                console.log(`[DynamicWorkflow] Updated messages, message content:`, logContent);
              }
              return updated;
            });

            // 强制触发重新渲染
            setWorkflowChunks((prev) => {
              const newMap = new Map(prev);
              newMap.set(workflowMessageId, [...chunks]);
              return newMap;
            });
          }
        }

        console.log(`[DynamicWorkflow] Stream completed, received ${chunkCount} chunks`);

        // 确保最终消息已保存
        if (currentSessionId) {
          const finalMessage = messages.find((m) => m.id === aiMessageId);
          if (finalMessage) {
            saveMessage(currentSessionId, finalMessage);
          }
        }

        // 流式更新完成，移除标记
        streamingMessageIdsRef.current.delete(aiMessageId);

        // 流式更新完成后，重新加载消息确保同步
        if (currentSessionId) {
          const loadedMessages = getSessionMessages(currentSessionId);
          setMessages(loadedMessages);
        }
      } catch (error: any) {
        console.error('Dynamic workflow execution failed:', error);
        const errorMsg = error?.message || '执行失败';

        // 流式更新完成（即使有错误），移除标记
        streamingMessageIdsRef.current.delete(aiMessageId);

        updateMessage(currentSessionId, aiMessageId, {
          content: `❌ 错误: ${errorMsg}`,
          status: 'sent',
        });

        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMessageId ? { ...m, content: `❌ 错误: ${errorMsg}`, status: 'sent' } : m
          )
        );
      } finally {
        setExecuting(false);
      }
    } catch (error: any) {
      console.error('Dynamic workflow handler failed:', error);
      sendMessage(`❌ 动态工作流执行失败: ${error?.message || '未知错误'}`, 'system', '系统');
      setExecuting(false);
    }
  };

  const handleDeleteMessage = (messageId: string) => {
    removeMessage(messageId);
  };

  // 轮询DAG执行状态
  const pollDAGExecutionStatus = async (executionId: string, maxAttempts = 30) => {
    let attempts = 0;

    const poll = async () => {
      if (attempts >= maxAttempts) {
        sendMessage('⏱️ 任务执行超时，请稍后查询执行状态', 'system', '系统');
        return;
      }

      try {
        const status = await getDAGExecutionStatus(executionId);

        if (status.status === 'completed') {
          sendMessage(`✅ 任务执行完成！\n\n${status.final_output || '无输出'}`, 'system', '系统');
        } else if (status.status === 'failed') {
          sendMessage(`❌ 任务执行失败: ${status.error_message || '未知错误'}`, 'system', '系统');
        } else {
          // 继续轮询
          attempts++;
          setTimeout(poll, 2000); // 每2秒轮询一次
        }
      } catch (error) {
        console.error('Failed to poll DAG execution status:', error);
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        }
      }
    };

    setTimeout(poll, 2000); // 首次延迟2秒
  };

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
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              </button>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  {String(sessions.find((s) => s.id === currentSessionId)?.title || '企业AI助手')}
                </h1>
                <p className="text-sm text-gray-500">{user?.username || '用户'}</p>
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
              />
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* 消息输入 */}
          <MessageInput
            onSend={handleSend}
            disabled={sending || executing || !currentSessionId}
            placeholder={
              executing
                ? '工作流执行中...'
                : currentSessionId
                  ? '输入消息，系统会自动识别意图并路由到合适的服务...'
                  : '请先创建或选择会话'
            }
            enableKnowledgeSearch={true}
            onKnowledgeSearch={handleKnowledgeSearch}
          />
        </div>

        {/* 知识库侧边栏 */}
        {knowledgeSidebarOpen ? (
          <KnowledgeSidebar
            query={knowledgeQuery}
            onClose={() => setKnowledgeSidebarOpen(false)}
            onSelectDocument={(doc) => {
              console.log('Selected document:', doc);
              // TODO: 打开文档详情
            }}
            onSelectConcept={(concept) => {
              handleKnowledgeSearch(concept);
            }}
          />
        ) : null}

        {/* 工作流输入对话框 */}
        {showWorkflowInput && currentWorkflowId ? (
          <WorkflowInputDialog
            workflowId={currentWorkflowId}
            workflow={workflows.find((w) => w.workflow_id === currentWorkflowId)}
            onExecute={handleExecuteWorkflow}
            onCancel={() => {
              setShowWorkflowInput(false);
              setCurrentWorkflowId(null);
            }}
          />
        ) : null}
      </div>
    </AuthGuard>
  );
}

// 工作流输入对话框组件
interface WorkflowInputDialogProps {
  workflowId: string;
  workflow?: WorkflowListItem;
  onExecute: (workflowId: string, inputData: Record<string, any>) => void;
  onCancel: () => void;
}

const WorkflowInputDialog: React.FC<WorkflowInputDialogProps> = ({
  workflowId,
  workflow,
  onExecute,
  onCancel,
}) => {
  const [inputData, setInputData] = useState('{\n  "input": ""\n}');
  const [error, setError] = useState<string | null>(null);

  const handleExecute = () => {
    try {
      const parsed = JSON.parse(inputData);
      onExecute(workflowId, parsed);
    } catch (e) {
      setError('无效的 JSON 格式');
    }
  };

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
            <label className="block text-sm font-medium text-gray-700 mb-2">输入参数 (JSON)</label>
            <textarea
              value={inputData}
              onChange={(e) => {
                setInputData(e.target.value);
                setError(null);
              }}
              rows={12}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              placeholder='{\n  "input": "您的输入内容"\n}'
            />
            {error ? <p className="text-red-600 text-sm mt-2">{error}</p> : null}
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
  );
};
