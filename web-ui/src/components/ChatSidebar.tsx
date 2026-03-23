'use client';

import { ChatSession } from '@/types/chat';
import { formatTime } from '@/lib/chat';
import { useState } from 'react';

interface ChatSidebarProps {
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  onClose?: () => void;
}

export function ChatSidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onClose,
}: ChatSidebarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [hoveredSession, setHoveredSession] = useState<string | null>(null);

  // 确保所有会话的title都是字符串（在组件内部再次清理，三重保险）
  const cleanedSessions = sessions.map((s) => {
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

  const filteredSessions = cleanedSessions.filter((session) => {
    // 安全地获取title字符串
    let titleStr = '';
    if (session.title) {
      if (typeof session.title === 'string') {
        titleStr = session.title;
      } else if (typeof session.title === 'object') {
        if ('title' in session.title && typeof session.title.title === 'string') {
          titleStr = session.title.title;
        } else if ('name' in session.title && typeof session.title.name === 'string') {
          titleStr = session.title.name;
        } else if ('content' in session.title && typeof session.title.content === 'string') {
          titleStr = session.title.content;
        } else {
          titleStr = '未命名会话';
        }
      } else {
        titleStr = String(session.title);
      }
    }
    const title = titleStr.toLowerCase();
    const lastMessage = session.lastMessage ? String(session.lastMessage).toLowerCase() : '';
    const search = searchTerm.toLowerCase();
    return title.includes(search) || lastMessage.includes(search);
  });

  return (
    <div className="w-full sm:w-64 bg-white border-r border-gray-200 flex flex-col h-full sm:h-screen">
      {/* 头部 */}
      <div className="p-4 border-b border-gray-200 pt-16 sm:pt-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">会话列表</h2>
          {onClose && (
            <button onClick={onClose} className="sm:hidden text-gray-500 hover:text-gray-700">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>
        <button
          onClick={onNewSession}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>新建会话</span>
        </button>
        <input
          type="text"
          placeholder="搜索会话..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full mt-3 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto">
        {filteredSessions.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            {searchTerm ? '未找到匹配的会话' : '暂无会话，点击上方按钮创建'}
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredSessions.map((session) => {
              const isActive = session.id === currentSessionId;
              return (
                <div
                  key={session.id}
                  onMouseEnter={() => setHoveredSession(session.id)}
                  onMouseLeave={() => setHoveredSession(null)}
                  onClick={() => onSelectSession(session.id)}
                  className={`p-4 cursor-pointer transition-colors ${
                    isActive ? 'bg-blue-50 border-l-4 border-blue-600' : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-gray-900 truncate">
                          {session.title || '未命名会话'}
                        </h3>
                        {session.unreadCount > 0 && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-blue-600 text-white rounded-full">
                            {session.unreadCount}
                          </span>
                        )}
                      </div>
                      {session.lastMessage && (
                        <p className="text-sm text-gray-500 truncate mb-1">
                          {String(session.lastMessage)}
                        </p>
                      )}
                      {session.lastMessageTime && (
                        <p className="text-xs text-gray-400">
                          {formatTime(session.lastMessageTime)}
                        </p>
                      )}
                    </div>
                    {hoveredSession === session.id && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(session.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 rounded transition-colors"
                        title="删除会话"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
