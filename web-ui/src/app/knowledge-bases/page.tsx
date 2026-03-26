'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  PlusIcon,
  DocumentTextIcon,
  FolderIcon,
  TrashIcon,
  ArrowUpTrayIcon,
  MagnifyingGlassIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  document_count: number;
  total_chunks: number;
  embedding_model: string;
  chunk_strategy?: string;
  chunk_size?: number;
  chunk_overlap?: number;
  settings?: Record<string, any>;
  created_at: string;
  updated_at: string;
  status: 'active' | 'indexing' | 'paused' | 'archived' | 'failed';
}

export default function KnowledgeBasePage() {
  const router = useRouter();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKBName, setNewKBName] = useState('');
  const [newKBDescription, setNewKBDescription] = useState('');

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  const fetchKnowledgeBases = async () => {
    try {
      setLoading(true);
      const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      const response = await fetch(`${API_BASE}/api/knowledge/knowledge-bases`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // 处理不同的响应格式
      if (Array.isArray(data)) {
        setKnowledgeBases(data);
      } else if (data.knowledge_bases) {
        setKnowledgeBases(data.knowledge_bases);
      } else if (data.data) {
        setKnowledgeBases(Array.isArray(data.data) ? data.data : []);
      } else {
        setKnowledgeBases([]);
      }
    } catch (error) {
      console.error('Failed to fetch knowledge bases:', error);
      setKnowledgeBases([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKB = async () => {
    if (!newKBName.trim()) {
      alert('请输入知识库名称');
      return;
    }

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      const response = await fetch(`${API_BASE}/api/knowledge/knowledge-bases`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newKBName,
          description: newKBDescription,
        }),
      });

      if (response.ok) {
        alert('知识库创建成功');
        setShowCreateModal(false);
        setNewKBName('');
        setNewKBDescription('');
        fetchKnowledgeBases();
      } else {
        alert('知识库创建失败');
      }
    } catch (error) {
      console.error('Failed to create knowledge base:', error);
      alert('知识库创建失败');
    }
  };

  const handleDeleteKB = async (id: string, name: string) => {
    if (!confirm(`确定要删除知识库 "${name}" 吗？此操作不可撤销。`)) {
      return;
    }

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      const response = await fetch(`${API_BASE}/api/knowledge/knowledge-bases/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        alert('知识库删除成功');
        fetchKnowledgeBases();
      } else {
        alert('知识库删除失败');
      }
    } catch (error) {
      console.error('Failed to delete knowledge base:', error);
      alert('知识库删除失败');
    }
  };

  const handleViewKB = (id: string) => {
    console.log('Navigating to knowledge base:', id);
    router.push(`/knowledge/${id}`);
  };

  const handleUploadDocument = (kbId: string) => {
    router.push(`/knowledge/${kbId}/upload`);
  };

  const filteredKBs = knowledgeBases.filter(
    (kb) =>
      kb.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      kb.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const badges = {
      active: { bg: 'bg-green-100', text: 'text-green-800', label: '就绪', icon: '●' },
      indexing: { bg: 'bg-blue-100', text: 'text-blue-800', label: '索引中', icon: '◐' },
      paused: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: '已暂停', icon: '⏸' },
      archived: { bg: 'bg-gray-100', text: 'text-gray-800', label: '已归档', icon: '📦' },
      failed: { bg: 'bg-red-100', text: 'text-red-800', label: '失败', icon: '✕' },
    };

    const badge = badges[status as keyof typeof badges] || badges.active;

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}
      >
        <span className="mr-1">{badge.icon}</span>
        {badge.label}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">知识库</h1>
                <p className="mt-1 text-sm text-gray-500">管理您的文档和知识库，为AI提供专业知识</p>
              </div>
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                创建知识库
              </button>
            </div>

            {/* Search */}
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="搜索知识库..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Knowledge Base List */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredKBs.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
            <FolderIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">暂无知识库</h3>
            <p className="mt-1 text-sm text-gray-500">创建您的第一个知识库以开始组织文档</p>
            <div className="mt-6">
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                创建知识库
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredKBs.map((kb) => (
              <div
                key={kb.id}
                className="bg-white rounded-lg border border-gray-200 hover:border-blue-500 hover:shadow-lg transition-all duration-200"
              >
                <div className="p-6">
                  <Link href={`/knowledge/${kb.id}`} className="block cursor-pointer">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3 flex-1">
                        <div className="flex-shrink-0 w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                          <DocumentTextIcon className="h-6 w-6 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold text-gray-900 truncate">
                            {kb.name}
                          </h3>
                          {getStatusBadge(kb.status)}
                        </div>
                      </div>
                    </div>

                    <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                      {kb.description || '暂无描述'}
                    </p>

                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-4 mb-4 pt-4 border-t border-gray-100">
                      <div>
                        <div className="text-xs text-gray-500">文档数量</div>
                        <div className="text-lg font-semibold text-gray-900">
                          {kb.document_count || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">知识块</div>
                        <div className="text-lg font-semibold text-gray-900">
                          {kb.total_chunks || 0}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 text-xs text-gray-400 mb-4">
                      <ClockIcon className="h-4 w-4" />
                      <span>更新于 {new Date(kb.updated_at).toLocaleDateString('zh-CN')}</span>
                    </div>
                  </Link>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleUploadDocument(kb.id);
                      }}
                      className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-blue-300 rounded-lg text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <ArrowUpTrayIcon className="h-4 w-4 mr-1" />
                      上传文档
                    </button>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleDeleteKB(kb.id, kb.name);
                      }}
                      className="inline-flex items-center justify-center p-2 border border-red-300 rounded-lg text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
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

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={() => setShowCreateModal(false)}
            ></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-4">创建知识库</h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      知识库名称 *
                    </label>
                    <input
                      type="text"
                      value={newKBName}
                      onChange={(e) => setNewKBName(e.target.value)}
                      placeholder="输入知识库名称"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                    <textarea
                      value={newKBDescription}
                      onChange={(e) => setNewKBDescription(e.target.value)}
                      placeholder="输入知识库描述"
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse gap-3">
                <button
                  onClick={handleCreateKB}
                  className="w-full sm:w-auto inline-flex justify-center rounded-lg border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  创建
                </button>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="mt-3 sm:mt-0 w-full sm:w-auto inline-flex justify-center rounded-lg border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
