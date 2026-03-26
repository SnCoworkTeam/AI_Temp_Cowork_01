'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import { ArrowLeftIcon, PencilIcon, PaperAirplaneIcon, TrashIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface Agent {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  status: 'active' | 'inactive' | 'training' | 'error';
  system_prompt?: string;
  config?: Record<string, any>;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ConversationSession {
  id: string;
  name: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export default function AgentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [sessions, setSessions] = useState<ConversationSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [taskInput, setTaskInput] = useState('');
  const [showNewSessionDialog, setShowNewSessionDialog] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // 生成唯一ID的辅助函数
  const generateUniqueId = () => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const createNewSession = (name: string) => {
    const newSession: ConversationSession = {
      id: generateUniqueId(),
      name: name || `对话 ${new Date().toLocaleString('zh-CN')}`,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    setSessions((prev) => [...prev, newSession]);
    setCurrentSessionId(newSession.id);
    setMessages([]);
    setShowNewSessionDialog(false);
    setNewSessionName('');
  };

  useEffect(() => {
    fetchAgent();
    // 从localStorage加载会话列表
    const savedSessions = localStorage.getItem(`agent_sessions_${agentId}`);
    if (savedSessions) {
      try {
        const parsed = JSON.parse(savedSessions);
        const loadedSessions = parsed.map((s: any) => ({
          ...s,
          messages: s.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          })),
          createdAt: new Date(s.createdAt),
          updatedAt: new Date(s.updatedAt),
        }));
        setSessions(loadedSessions);

        // 如果有会话，默认选择第一个或最近更新的
        if (loadedSessions.length > 0) {
          const latestSession = loadedSessions.sort((a: ConversationSession, b: ConversationSession) =>
            b.updatedAt.getTime() - a.updatedAt.getTime()
          )[0];
          setCurrentSessionId(latestSession.id);
          setMessages(latestSession.messages);
        } else {
          // 如果没有会话，创建默认会话
          createNewSession('默认对话');
        }
      } catch (e) {
        console.error('Failed to load sessions:', e);
        createNewSession('默认对话');
      }
    } else {
      // 如果没有保存的会话，创建默认会话
      createNewSession('默认对话');
    }
  }, [agentId]);

  // 当切换会话时，更新消息列表
  useEffect(() => {
    if (currentSessionId && sessions.length > 0) {
      const session = sessions.find(s => s.id === currentSessionId);
      if (session) {
        setMessages(session.messages);
      }
    }
  }, [currentSessionId, sessions]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 保存会话列表到localStorage
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem(`agent_sessions_${agentId}`, JSON.stringify(sessions));
    }
  }, [sessions, agentId]);

  // 更新当前会话的消息
  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      setSessions((prev) =>
        prev.map((session) => {
          if (session.id === currentSessionId) {
            return {
              ...session,
              messages: messages,
              updatedAt: new Date(),
            };
          }
          return session;
        })
      );
    }
  }, [messages, currentSessionId]);


  const switchSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setMessages(session.messages);
    }
  };

  const deleteSession = (sessionId: string) => {
    if (confirm('确定要删除这个对话会话吗？')) {
      const newSessions = sessions.filter(s => s.id !== sessionId);
      setSessions(newSessions);

      if (sessionId === currentSessionId) {
        if (newSessions.length > 0) {
          setCurrentSessionId(newSessions[0].id);
          setMessages(newSessions[0].messages);
        } else {
          createNewSession('默认对话');
        }
      }
    }
  };

  const renameSession = (sessionId: string, newName: string) => {
    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId ? { ...session, name: newName } : session
      )
    );
  };

  const fetchAgent = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/agents/${agentId}`);
      if (!response.ok) {
        if (response.status === 404) {
          // 智能体不存在，返回列表页
          alert('智能体不存在，可能已被删除或服务已重启');
          router.push('/agents');
          return;
        }
        throw new Error('获取智能体详情失败');
      }
      const data = await response.json();
      setAgent(data);
    } catch (error) {
      console.error('Failed to fetch agent:', error);
      // 不显示alert，直接返回列表页
      router.push('/agents');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!taskInput.trim() || executing) {
      return;
    }

    const userMessage: Message = {
      id: generateUniqueId(),
      role: 'user',
      content: taskInput.trim(),
      timestamp: new Date(),
    };

    // 添加用户消息
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = taskInput.trim();
    setTaskInput('');

    // 添加一个占位的助手消息
    const assistantMessageId = generateUniqueId();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      setExecuting(true);

      // 构建对话历史（最近10轮对话）
      const conversationHistory = messages
        .slice(-20) // 最近20条消息（10轮对话）
        .map((msg) => ({
          role: msg.role,
          content: msg.content,
        }))
        .filter((msg) => msg.content.trim().length > 0); // 过滤空消息

      // 非流式执行
      const response = await fetch(`/api/v1/agents/${agentId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task: currentInput,
          context: {
            conversation_history: conversationHistory,
          },
          parameters: {},
          stream: false, // 关闭流式输出
        }),
      });

      if (!response.ok) {
        // 非流式响应，尝试解析JSON
        try {
          const error = await response.json();
          throw new Error(error.error || error.detail || '执行智能体失败');
        } catch (jsonError) {
          // 如果JSON解析失败，使用状态文本
          throw new Error(`执行智能体失败: ${response.status} ${response.statusText}`);
        }
      }

      // 非流式处理
      const result = await response.json();
      const errorMessage = result?.error || result?.detail;
      const output =
        result?.output ||
        result?.response ||
        errorMessage ||
        (result?.success === false ? '执行失败' : '执行完成');

      // 更新助手消息
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: output }
            : msg
        )
      );
    } catch (error) {
      console.error('Failed to execute agent:', error);
      const errorMessage = error instanceof Error ? error.message : '执行失败';

      // 更新助手消息为错误信息
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: `❌ 错误: ${errorMessage}` }
            : msg
        )
      );
    } finally {
      setExecuting(false);
    }
  };

  const handleClearChat = () => {
    if (confirm('确定要清空对话历史吗？')) {
      setMessages([]);
      localStorage.removeItem(`agent_chat_${agentId}`);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDelete = async () => {
    if (!confirm('确定要删除这个智能体吗？此操作不可撤销。')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/agents/${agentId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '删除智能体失败');
      }

      router.push('/agents');
    } catch (error) {
      console.error('Failed to delete agent:', error);
      alert(error instanceof Error ? error.message : '删除智能体失败');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'inactive':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'training':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '运行中';
      case 'inactive':
        return '已停用';
      case 'error':
        return '错误';
      case 'training':
        return '训练中';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <AuthGuard requireAuth>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="ml-3 text-gray-600">加载中...</span>
        </div>
      </AuthGuard>
    );
  }

  if (!agent) {
    return (
      <AuthGuard requireAuth>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <p className="text-gray-600 mb-4">智能体不存在</p>
            <button
              onClick={() => router.push('/agents')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              返回智能体列表
            </button>
          </div>
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard requireAuth>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* 页面标题 */}
          <div className="mb-8">
            <button
              onClick={() => router.push('/agents')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
            >
              <ArrowLeftIcon className="w-5 h-5" />
              <span>返回智能体列表</span>
            </button>

            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{agent.name}</h1>
                <p className="mt-2 text-sm text-gray-600">{agent.description}</p>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`px-3 py-1 text-sm font-medium rounded border ${getStatusColor(agent.status)}`}
                >
                  {getStatusText(agent.status)}
                </span>
                <button
                  onClick={() => router.push(`/agents/${agentId}/edit`)}
                  className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
                >
                  <PencilIcon className="w-5 h-5" />
                  <span>编辑</span>
                </button>
                <button
                  onClick={handleDelete}
                  className="px-4 py-2 text-red-600 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors flex items-center gap-2"
                >
                  <TrashIcon className="w-5 h-5" />
                  <span>删除</span>
                </button>
              </div>
            </div>
          </div>

          {/* 智能体信息 */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">智能体信息</h2>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">能力</label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {agent.capabilities && agent.capabilities.length > 0 ? (
                    agent.capabilities.map((cap, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-sm"
                      >
                        {cap}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-500 text-sm">无</span>
                  )}
                </div>
              </div>

              {agent.config?.use_tool_integration && (
                <div>
                  <label className="text-sm font-medium text-gray-700">MCP工具集成</label>
                  <div className="mt-2 space-y-2">
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">状态：</span>
                      <span className="text-green-600">已启用</span>
                    </p>
                    {agent.config.preferred_tools && agent.config.preferred_tools.length > 0 && (
                      <div>
                        <span className="font-medium text-sm text-gray-700">优先工具：</span>
                        <div className="mt-1 flex flex-wrap gap-2">
                          {agent.config.preferred_tools.map((tool: string, index: number) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                            >
                              {tool}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {agent.metadata?.mcp_server && (
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">MCP服务器：</span>
                        {agent.metadata.mcp_server}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {agent.system_prompt && (
                <div>
                  <label className="text-sm font-medium text-gray-700">系统提示词</label>
                  <div className="mt-2 p-4 bg-gray-50 rounded-lg">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                      {agent.system_prompt}
                    </pre>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <div>
                  <label className="text-sm font-medium text-gray-700">创建时间</label>
                  <p className="text-sm text-gray-600 mt-1">
                    {new Date(agent.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">更新时间</label>
                  <p className="text-sm text-gray-600 mt-1">
                    {new Date(agent.updated_at).toLocaleString('zh-CN')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 聊天界面 */}
          <div className="bg-white rounded-lg border border-gray-200 flex flex-col" style={{ height: 'calc(100vh - 400px)', minHeight: '600px' }}>
            {/* 会话标签页 */}
            {sessions.length > 0 && (
              <div className="flex items-center gap-2 p-2 border-b border-gray-200 bg-gray-50 overflow-x-auto">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors min-w-0 flex-shrink-0 ${
                      currentSessionId === session.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-100'
                    }`}
                    onClick={() => switchSession(session.id)}
                  >
                    <span className="text-sm font-medium truncate max-w-[120px]" title={session.name}>
                      {session.name}
                    </span>
                    {sessions.length > 1 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.id);
                        }}
                        className={`p-0.5 rounded hover:bg-opacity-20 flex-shrink-0 ${
                          currentSessionId === session.id ? 'hover:bg-white' : 'hover:bg-gray-200'
                        }`}
                        title="删除对话"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
                <button
                  onClick={() => {
                    const name = prompt('请输入新对话名称：', `对话 ${new Date().toLocaleString('zh-CN')}`);
                    if (name && name.trim()) {
                      createNewSession(name.trim());
                    }
                  }}
                  className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-1 flex-shrink-0"
                  title="新建对话"
                >
                  <PlusIcon className="w-4 h-4" />
                  <span>新建</span>
                </button>
              </div>
            )}

            {/* 聊天头部 */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  与 {agent.name} 对话
                  {sessions.find(s => s.id === currentSessionId) && (
                    <span className="ml-2 text-sm font-normal text-gray-500">
                      - {sessions.find(s => s.id === currentSessionId)?.name}
                    </span>
                  )}
                </h2>
                <p className="text-sm text-gray-500 mt-1">{agent.description}</p>
              </div>
              <div className="flex items-center gap-2">
                {sessions.find(s => s.id === currentSessionId) && (
                  <button
                    onClick={() => {
                      const session = sessions.find(s => s.id === currentSessionId);
                      if (session) {
                        const newName = prompt('重命名对话：', session.name);
                        if (newName && newName.trim()) {
                          renameSession(session.id, newName.trim());
                        }
                      }
                    }}
                    className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    title="重命名对话"
                  >
                    重命名
                  </button>
                )}
                <button
                  onClick={handleClearChat}
                  className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  清空对话
                </button>
              </div>
            </div>

            {/* 消息列表 */}
            <div
              ref={chatContainerRef}
              className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
            >
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-gray-500">
                    <p className="text-lg mb-2">开始与 {agent.name} 对话</p>
                    <p className="text-sm">输入您的问题或任务，智能体将为您处理</p>
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-900 border border-gray-200'
                      }`}
                    >
                      <div className="whitespace-pre-wrap text-sm leading-relaxed">
                        {message.content}
                      </div>
                      <div
                        className={`text-xs mt-2 ${
                          message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                        }`}
                      >
                        {message.timestamp.toLocaleTimeString('zh-CN', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </div>
                  </div>
                ))
              )}
              {executing && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                    <div className="flex items-center gap-2 text-gray-600">
                      <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-sm">正在思考...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* 输入区域 */}
            <div className="p-4 border-t border-gray-200 bg-white">
              <div className="flex items-end gap-3">
                <textarea
                  value={taskInput}
                  onChange={(e) => setTaskInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  rows={1}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder="输入消息... (Shift+Enter 换行，Enter 发送)"
                  style={{ minHeight: '44px', maxHeight: '120px' }}
                />
                <button
                  onClick={handleSend}
                  disabled={executing || !taskInput.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <PaperAirplaneIcon className="w-5 h-5" />
                  <span>发送</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
