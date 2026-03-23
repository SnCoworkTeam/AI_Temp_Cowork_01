'use client';

import { useState, KeyboardEvent, useRef, useEffect, useCallback } from 'react';
import { SearchSuggestions, QuickSearch } from './ChatInterface/index';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  enableKnowledgeSearch?: boolean;
  onKnowledgeSearch?: (query: string) => void;
  showThinkingContent?: boolean;
  onToggleThinkingContent?: () => void;
}

export function MessageInput({
  onSend,
  disabled = false,
  placeholder = '输入消息...',
  enableKnowledgeSearch = true,
  onKnowledgeSearch,
  showThinkingContent = true,
  onToggleThinkingContent,
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showQuickSearch, setShowQuickSearch] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 自动调整高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  // 发送处理（修复：不使用防抖，直接发送，避免input被清空后无法获取内容）
  const handleSend = useCallback(() => {
    const message = input.trim();
    if (message && !disabled && !isSending) {
      setIsSending(true);
      // 立即清空输入框，提供即时反馈
      setInput('');
      setShowSuggestions(false);
      setShowQuickSearch(false);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }

      // 立即发送，不延迟
      try {
        onSend(message);
      } catch (error) {
        console.error('Failed to send message:', error);
        // 如果发送失败，恢复输入内容
        setInput(message);
      } finally {
        // 延迟重置发送状态，防止快速重复点击
        setTimeout(() => setIsSending(false), 300);
      }
    }
  }, [input, disabled, isSending, onSend]);

  const handleKnowledgeSearch = (query: string) => {
    if (onKnowledgeSearch) {
      onKnowledgeSearch(query);
    } else {
      // 如果没有提供搜索处理函数，将查询作为消息发送
      onSend(query);
    }
    setShowSuggestions(false);
    setShowQuickSearch(false);
  };

  const handleSelectSuggestion = (suggestion: string) => {
    setInput(suggestion);
    setShowSuggestions(false);
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    } else if (e.key === '/' && enableKnowledgeSearch && input.trim() === '') {
      // 输入 / 显示快速搜索
      setShowQuickSearch(true);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setShowQuickSearch(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setInput(value);

    // 显示搜索建议
    if (enableKnowledgeSearch && value.trim().length >= 2 && !value.startsWith('/')) {
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }

    // 如果输入 / 开头，显示快速搜索
    if (value === '/') {
      setShowQuickSearch(true);
    } else if (value.startsWith('/')) {
      setShowQuickSearch(false);
    }
  };

  // 点击外部关闭建议
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
        setShowQuickSearch(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="border-t border-gray-200 bg-white" ref={containerRef}>
      {/* 思考内容开关 - DeepSeek风格 */}
      {onToggleThinkingContent && (
        <div className="px-4 pt-3 pb-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">思考模式</span>
            <button
              onClick={onToggleThinkingContent}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                showThinkingContent ? 'bg-blue-600' : 'bg-gray-300'
              }`}
              role="switch"
              aria-checked={showThinkingContent}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  showThinkingContent ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-xs ${showThinkingContent ? 'text-blue-600' : 'text-gray-400'}`}>
              {showThinkingContent ? '已开启' : '已关闭'}
            </span>
          </div>
        </div>
      )}

      <div className="px-4 pb-4">
        <div className="flex items-end gap-2 relative">
          {/* 快捷命令提示 */}
          <div className="flex-1 relative">
            {/* 知识库搜索建议 */}
            {enableKnowledgeSearch && showSuggestions && input.trim().length >= 2 && (
              <SearchSuggestions
                query={input}
                onSelect={handleSelectSuggestion}
                onSearch={handleKnowledgeSearch}
              />
            )}

            {/* 快速搜索 */}
            {enableKnowledgeSearch && showQuickSearch && (
              <div className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                <QuickSearch onSearch={handleKnowledgeSearch} />
              </div>
            )}

            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled}
              rows={1}
              className="w-full px-4 py-3 border border-gray-200 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none disabled:bg-gray-50 disabled:cursor-not-allowed bg-white shadow-sm transition-all"
              style={{
                maxHeight: '200px',
                overflowY: 'auto',
                fontSize: '15px',
                lineHeight: '1.5',
              }}
            />
            <div className="text-xs text-gray-400 mt-2 px-1">
              提示: 使用{' '}
              <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">/dag 任务描述</kbd>{' '}
              智能分解执行任务 或{' '}
              <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">/workflow 工作流名称</kbd>{' '}
              执行工作流
              {enableKnowledgeSearch && (
                <>
                  {' '}
                  或 <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">/kb 查询</kbd>{' '}
                  搜索知识库 或 <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">/</kbd>{' '}
                  快速搜索
                </>
              )}
            </div>
          </div>

          {/* 发送按钮 - DeepSeek风格 */}
          <button
            onClick={handleSend}
            disabled={!input.trim() || disabled}
            className="px-4 py-3 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center shadow-md hover:shadow-lg disabled:shadow-none min-w-[44px] h-[44px]"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
