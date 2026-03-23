'use client';

import React, { useState, useRef, useEffect } from 'react';
import { AgentState } from '../AgentWorkflowInterface';

/**
 * AgentChat组件属性
 */
export interface AgentChatProps {
  /** 智能体状态 */
  agent: AgentState | null;
  /** 发送消息回调 */
  onSendMessage: (message: string) => Promise<void>;
  /** 是否加载中 */
  isLoading?: boolean;
  /** 建议的问题 */
  suggestions?: string[];
}

/**
 * 智能体聊天组件
 *
 * 提供与智能体交互的聊天界面
 */
export const AgentChat: React.FC<AgentChatProps> = ({
  agent,
  onSendMessage,
  isLoading = false,
  suggestions = [],
}) => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<
    Array<{
      id: string;
      role: 'user' | 'assistant';
      content: string;
      timestamp: number;
    }>
  >([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, agent?.currentMessage]);

  // 更新智能体消息
  useEffect(() => {
    if (agent?.currentMessage) {
      setMessages((prev) => {
        const lastMessage = prev[prev.length - 1];
        // 如果最后一条消息是助手消息，更新它；否则添加新消息
        if (lastMessage && lastMessage.role === 'assistant') {
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              content: agent.currentMessage || '',
              timestamp: Date.now(),
            },
          ];
        } else {
          return [
            ...prev,
            {
              id: `msg-${Date.now()}`,
              role: 'assistant',
              content: agent.currentMessage || '',
              timestamp: Date.now(),
            },
          ];
        }
      });
    }
  }, [agent?.currentMessage]);

  // 处理发送消息
  const handleSend = async () => {
    const message = input.trim();
    if (!message || isLoading) {
      return;
    }

    // 添加用户消息到列表
    const userMessage = {
      id: `msg-${Date.now()}`,
      role: 'user' as const,
      content: message,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    // 发送消息
    try {
      await onSendMessage(message);
    } catch (error) {
      console.error('发送消息失败:', error);
    }
  };

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 处理建议问题点击
  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  // 状态指示器
  const getStatusIndicator = () => {
    if (isLoading) {
      return (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span>正在处理...</span>
        </div>
      );
    }

    if (agent?.status === 'thinking') {
      return (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <div className="w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
          <span>思考中...</span>
        </div>
      );
    }

    if (agent?.status === 'awaiting_input') {
      return (
        <div className="flex items-center gap-2 text-sm text-blue-600">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>等待输入</span>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* 聊天消息区域 */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* 欢迎消息 */}
        {messages.length === 0 && !agent?.currentMessage && (
          <div className="text-center text-gray-500 py-8">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <p className="text-sm">
              {agent?.agentName ? `与 ${agent.agentName} 开始对话` : '开始与智能体对话'}
            </p>
            {agent?.status === 'idle' && (
              <p className="text-xs mt-2 text-gray-400">输入消息开始工作流</p>
            )}
          </div>
        )}

        {/* 消息列表 */}
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
              <p
                className={`text-xs mt-1 ${
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                }`}
              >
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {/* 当前智能体消息（流式显示） */}
        {agent?.currentMessage && messages.length > 0 && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900">
              <p className="text-sm whitespace-pre-wrap break-words">{agent.currentMessage}</p>
              {isLoading && (
                <div className="mt-2 flex items-center gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.1s' }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  ></div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 错误消息 */}
        {agent?.error && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-lg px-4 py-2 bg-red-50 border border-red-200">
              <div className="flex items-start gap-2">
                <svg
                  className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <div>
                  <p className="text-sm font-medium text-red-800">错误</p>
                  <p className="text-sm text-red-700 mt-1">{agent.error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 状态指示器 */}
      {getStatusIndicator() && (
        <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">{getStatusIndicator()}</div>
      )}

      {/* 建议问题 */}
      {suggestions.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-500 mb-2">建议问题：</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-3 py-1.5 text-xs bg-white border border-gray-300 rounded-full hover:bg-gray-50 hover:border-gray-400 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 输入区域 */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={agent?.status === 'awaiting_input' ? '请输入回复...' : '输入消息...'}
              disabled={isLoading}
              rows={1}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
              style={{ minHeight: '44px', maxHeight: '120px' }}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              '发送'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
