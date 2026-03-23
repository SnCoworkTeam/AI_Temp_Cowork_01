'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  PlusIcon,
  ChatBubbleLeftRightIcon,
  TrashIcon,
  ClockIcon,
  UserCircleIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';

interface Conversation {
  id: string;
  title: string;
  summary?: string;
  message_count: number;
  model: string;
  created_at: string;
  updated_at: string;
  last_message?: string;
  status: 'active' | 'archived';
}

export default function ConversationsPage() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'recent' | 'oldest'>('recent');

  useEffect(() => {
    fetchConversations();
  }, [filterStatus, sortBy]);

  const fetchConversations = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterStatus !== 'all') {
        params.append('status', filterStatus);
      }
      params.append('sort', sortBy);

      const response = await fetch(`/api/conversations?${params.toString()}`);
      const data = await response.json();

      if (data.conversations) {
        setConversations(data.conversations);
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNewConversation = () => {
    router.push('/chat');
  };

  const handleOpenConversation = (id: string) => {
    router.push(`/chat?conversation_id=${id}`);
  };

  const handleDeleteConversation = async (id: string, title: string) => {
    if (!confirm(`确定要删除对话 "${title}" 吗？此操作不可撤销。`)) {
      return;
    }

    try {
      const response = await fetch(`/api/conversations/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        alert('对话删除成功');
        fetchConversations();
      } else {
        alert('对话删除失败');
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('对话删除失败');
    }
  };

  const handleArchiveConversation = async (id: string) => {
    try {
      const response = await fetch(`/api/conversations/${id}/archive`, {
        method: 'POST',
      });

      if (response.ok) {
        alert('对话已归档');
        fetchConversations();
      } else {
        alert('归档失败');
      }
    } catch (error) {
      console.error('Failed to archive conversation:', error);
      alert('归档失败');
    }
  };

  const filteredConversations = conversations.filter(
    (conv) =>
      conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.summary?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.last_message?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 24 * 7) {
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    } else {
      return date.toLocaleDateString('zh-CN');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">对话历史</h1>
                <p className="mt-1 text-sm text-gray-500">查看和管理您的所有对话记录</p>
              </div>
              <button
                onClick={handleNewConversation}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                新建对话
              </button>
            </div>

            {/* Search and Filters */}
            <div className="mt-6 flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    placeholder="搜索对话..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  <option value="all">全部对话</option>
                  <option value="active">进行中</option>
                  <option value="archived">已归档</option>
                </select>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'recent' | 'oldest')}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  <option value="recent">最近更新</option>
                  <option value="oldest">最早创建</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Conversation List */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
            <ChatBubbleLeftRightIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">暂无对话</h3>
            <p className="mt-1 text-sm text-gray-500">开始您的第一个对话</p>
            <div className="mt-6">
              <button
                onClick={handleNewConversation}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                新建对话
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredConversations.map((conversation) => (
              <div
                key={conversation.id}
                className="bg-white rounded-lg border border-gray-200 hover:border-blue-500 hover:shadow-md transition-all duration-200 cursor-pointer"
                onClick={() => handleOpenConversation(conversation.id)}
              >
                <div className="p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                          <ChatBubbleLeftRightIcon className="h-5 w-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-base font-semibold text-gray-900 truncate">
                            {conversation.title}
                          </h3>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-gray-500">
                              {conversation.message_count} 条消息
                            </span>
                            <span className="text-xs text-gray-400">•</span>
                            <span className="text-xs text-gray-500">{conversation.model}</span>
                            {conversation.status === 'archived' && (
                              <>
                                <span className="text-xs text-gray-400">•</span>
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                  已归档
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Last Message Preview */}
                      {conversation.last_message && (
                        <p className="text-sm text-gray-600 line-clamp-2 ml-13">
                          {conversation.last_message}
                        </p>
                      )}
                    </div>

                    <div className="flex items-start gap-2 ml-4">
                      <div className="text-right">
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <ClockIcon className="h-3.5 w-3.5" />
                          <span>{formatDate(conversation.updated_at)}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenConversation(conversation.id);
                      }}
                      className="flex-1 text-center px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      继续对话
                    </button>
                    {conversation.status === 'active' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleArchiveConversation(conversation.id);
                        }}
                        className="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                      >
                        归档
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteConversation(conversation.id, conversation.title);
                      }}
                      className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
