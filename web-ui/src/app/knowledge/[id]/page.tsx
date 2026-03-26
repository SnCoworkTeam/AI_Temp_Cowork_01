'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  ArrowLeftIcon,
  ArrowUpTrayIcon,
  DocumentTextIcon,
  FolderIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import DocumentProgress from '@/components/DocumentProgress';

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

interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  tags?: string[];
  category?: string;
  created_at: string;
  updated_at: string;
  processed_at?: string;
}

interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
  start_char?: number;
  end_char?: number;
  page_number?: number;
  embedding_model?: string;
  metadata?: Record<string, any>;
  created_at?: string;
}

interface DocumentProgressData {
  document_id: string;
  stage: string;
  progress_percentage: number;
  current_step: string;
  total_steps: number;
  completed_steps: number;
  estimated_time_remaining?: number;
}

export default function KnowledgeBaseDetailPage() {
  const router = useRouter();
  const params = useParams();
  const kbId = params?.id as string;

  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [expandedDocuments, setExpandedDocuments] = useState<Set<string>>(new Set());
  const [documentChunks, setDocumentChunks] = useState<Map<string, DocumentChunk[]>>(new Map());
  const [chunksLoading, setChunksLoading] = useState<Set<string>>(new Set());
  const [chunksErrors, setChunksErrors] = useState<Map<string, string>>(new Map());
  const [documentProgresses, setDocumentProgresses] = useState<Map<string, DocumentProgressData>>(
    new Map()
  );

  useEffect(() => {
    if (kbId) {
      fetchKnowledgeBase();
      fetchDocuments();
    }
  }, [kbId, page]);

  // 轮询处理中的文档进度
  useEffect(() => {
    const processingDocs = documents.filter(
      (doc) => doc.status === 'processing' || doc.status === 'uploading'
    );

    if (processingDocs.length === 0) {
      return;
    }

    // 立即获取一次
    fetchProgresses(processingDocs);

    // 每3秒轮询一次
    const interval = setInterval(() => {
      fetchProgresses(processingDocs);
    }, 3000);

    return () => clearInterval(interval);
  }, [documents]);

  const fetchKnowledgeBase = async () => {
    try {
      const response = await fetch(`/api/knowledge-bases/${kbId}`);
      if (response.ok) {
        const data = await response.json();
        setKnowledgeBase(data);
      } else {
        alert('知识库不存在');
        router.push('/knowledge-bases');
      }
    } catch (error) {
      console.error('Failed to fetch knowledge base:', error);
      alert('加载知识库信息失败');
      router.push('/knowledge-bases');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async () => {
    try {
      setDocumentsLoading(true);
      const response = await fetch(
        `/api/knowledge-bases/${kbId}/documents?page=${page}&page_size=20`
      );
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
        setTotalPages(data.total_pages || 1);
      } else {
        console.error('Failed to fetch documents');
      }
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    } finally {
      setDocumentsLoading(false);
    }
  };

  const fetchProgresses = async (docs: Document[]) => {
    const progressPromises = docs.map(async (doc) => {
      try {
        const response = await fetch(`/api/knowledge/documents/${doc.id}/progress`);
        if (response.ok) {
          const progress = await response.json();
          return { docId: doc.id, progress };
        } else if (response.status === 404) {
          // 进度不存在，可能已完成
          return null;
        }
      } catch (error) {
        console.error(`Failed to fetch progress for ${doc.id}:`, error);
      }
      return null;
    });

    const results = await Promise.all(progressPromises);
    const newProgresses = new Map<string, DocumentProgressData>();

    results.forEach((result) => {
      if (result && result.progress) {
        newProgresses.set(result.docId, result.progress);
      }
    });

    setDocumentProgresses((prev) => {
      const merged = new Map(prev);
      newProgresses.forEach((value, key) => {
        merged.set(key, value);
      });
      // 移除已完成或失败的文档进度
      docs.forEach((doc) => {
        if (doc.status === 'processed' || doc.status === 'failed') {
          merged.delete(doc.id);
        }
      });
      return merged;
    });
  };

  const handleDeleteDocument = async (docId: string, filename: string) => {
    if (!confirm(`确定要删除文档 "${filename}" 吗？此操作不可撤销。`)) {
      return;
    }

    try {
      console.log(`[Delete Document] Attempting to delete document: ${docId} (${filename})`);

      const response = await fetch(`/api/knowledge/documents/${docId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        const data = await response.json();
        console.log('[Delete Document] Success:', data);
        alert('文档删除成功');
        fetchDocuments();
        if (knowledgeBase) {
          fetchKnowledgeBase(); // 刷新统计信息
        }
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('[Delete Document] Failed:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData,
        });

        const errorMessage =
          errorData.error ||
          errorData.detail ||
          `删除失败: ${response.status} ${response.statusText}`;
        alert(`文档删除失败: ${errorMessage}`);
      }
    } catch (error: any) {
      console.error('[Delete Document] Error:', error);
      const errorMessage = error?.message || '网络错误或服务器无响应';
      alert(`文档删除失败: ${errorMessage}`);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'processing':
        return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'processed':
        return '已处理';
      case 'processing':
        return '处理中';
      case 'failed':
        return '失败';
      case 'uploading':
        return '上传中';
      default:
        return '待处理';
    }
  };

  const toggleDocumentExpansion = (doc: Document) => {
    setExpandedDocuments((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(doc.id)) {
        newSet.delete(doc.id);
      } else {
        newSet.add(doc.id);
      }
      return newSet;
    });

    if (doc.status === 'processed') {
      const hasChunks = documentChunks.has(doc.id);
      if (!hasChunks) {
        fetchAllChunks(doc.id);
      }
    }
  };

  const fetchAllChunks = async (docId: string) => {
    setChunksLoading((prev) => new Set(prev).add(docId));
    setChunksErrors((prev) => {
      const next = new Map(prev);
      next.delete(docId);
      return next;
    });

    try {
      const pageSize = 500;
      const firstResponse = await fetch(
        `/api/knowledge/documents/${docId}/chunks?page=1&page_size=${pageSize}`
      );

      if (!firstResponse.ok) {
        const errorData = await firstResponse.json().catch(() => ({}));
        throw new Error(errorData?.error || errorData?.detail || '获取分块失败');
      }

      const firstData = await firstResponse.json();
      const chunks = (firstData.chunks || []) as DocumentChunk[];
      const totalPages = firstData.total_pages || 1;

      for (let currentPage = 2; currentPage <= totalPages; currentPage += 1) {
        const response = await fetch(
          `/api/knowledge/documents/${docId}/chunks?page=${currentPage}&page_size=${pageSize}`
        );
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData?.error || errorData?.detail || '获取分块失败');
        }
        const data = await response.json();
        if (Array.isArray(data.chunks)) {
          chunks.push(...(data.chunks as DocumentChunk[]));
        }
      }

      setDocumentChunks((prev) => {
        const next = new Map(prev);
        next.set(docId, chunks);
        return next;
      });
    } catch (error: any) {
      const message = error?.message || '获取分块失败';
      setChunksErrors((prev) => {
        const next = new Map(prev);
        next.set(docId, message);
        return next;
      });
    } finally {
      setChunksLoading((prev) => {
        const next = new Set(prev);
        next.delete(docId);
        return next;
      });
    }
  };

  const handleProgressUpdate = () => {
    // 当进度更新时，刷新文档列表
    fetchDocuments();
    if (knowledgeBase) {
      fetchKnowledgeBase();
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!knowledgeBase) {
    return null;
  }

  const filteredDocuments = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/knowledge-bases')}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <ArrowLeftIcon className="h-5 w-5 mr-2" />
                返回
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{knowledgeBase.name}</h1>
                {knowledgeBase.description && (
                  <p className="mt-1 text-sm text-gray-500">{knowledgeBase.description}</p>
                )}
              </div>
            </div>
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('[Upload Button] Clicked, navigating to:', `/knowledge/${kbId}/upload`);
                router.push(`/knowledge/${kbId}/upload`);
              }}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <ArrowUpTrayIcon className="h-5 w-5 mr-2" />
              上传文档
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">文档数量</p>
                <p className="text-2xl font-bold text-gray-900">
                  {knowledgeBase.document_count || 0}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <FolderIcon className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">向量块数量</p>
                <p className="text-2xl font-bold text-gray-900">
                  {knowledgeBase.total_chunks || 0}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">嵌入模型</p>
                <p className="text-lg font-semibold text-gray-900">
                  {knowledgeBase.embedding_model || 'N/A'}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <div
                className={`h-3 w-3 rounded-full mr-3 ${
                  knowledgeBase.status === 'active'
                    ? 'bg-green-500'
                    : knowledgeBase.status === 'indexing'
                      ? 'bg-blue-500'
                      : knowledgeBase.status === 'failed'
                        ? 'bg-red-500'
                        : 'bg-gray-400'
                }`}
              ></div>
              <div>
                <p className="text-sm font-medium text-gray-500">状态</p>
                <p className="text-lg font-semibold text-gray-900">
                  {knowledgeBase.status === 'active'
                    ? '活跃'
                    : knowledgeBase.status === 'indexing'
                      ? '索引中'
                      : knowledgeBase.status === 'failed'
                        ? '失败'
                        : knowledgeBase.status === 'paused'
                          ? '已暂停'
                          : '已归档'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Documents Section */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">文档列表</h2>
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="搜索文档..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <button
                  onClick={fetchDocuments}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <ArrowPathIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>

          {documentsLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="text-center py-12">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">暂无文档</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchQuery ? '没有找到匹配的文档' : '开始上传文档以构建知识库'}
              </p>
              {!searchQuery && (
                <div className="mt-6">
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      console.log(
                        '[Upload Button] Clicked, navigating to:',
                        `/knowledge/${kbId}/upload`
                      );
                      router.push(`/knowledge/${kbId}/upload`);
                    }}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                  >
                    <ArrowUpTrayIcon className="h-5 w-5 mr-2" />
                    上传文档
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        文件名
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        类型
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        大小
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        状态
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        标签
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        创建时间
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredDocuments.map((doc) => {
                      const isExpanded = expandedDocuments.has(doc.id);
                      const isProcessing =
                        doc.status === 'processing' || doc.status === 'uploading';
                      const isProcessed = doc.status === 'processed';

                      return (
                        <React.Fragment key={doc.id}>
                          <tr className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <DocumentTextIcon className="h-5 w-5 text-gray-400 mr-2" />
                                <span className="text-sm font-medium text-gray-900">
                                  {doc.filename}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-sm text-gray-500">{doc.file_type}</span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-sm text-gray-500">
                                {formatFileSize(doc.file_size)}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center gap-2">
                                {getStatusIcon(doc.status)}
                                <div className="flex flex-col">
                                  <span className="text-sm text-gray-500">
                                    {getStatusText(doc.status)}
                                  </span>
                                  {isProcessing && documentProgresses.has(doc.id) && (
                                    <span className="text-xs text-blue-600 font-medium">
                                      {documentProgresses
                                        .get(doc.id)
                                        ?.progress_percentage.toFixed(1)}
                                      %
                                    </span>
                                  )}
                                </div>
                                {(isProcessing || isProcessed) && (
                                  <button
                                    onClick={() => toggleDocumentExpansion(doc)}
                                    className="ml-2 text-blue-600 hover:text-blue-800"
                                    title={isProcessing ? '查看详细进度' : '查看分块内容'}
                                  >
                                    {isExpanded ? (
                                      <ChevronUpIcon className="h-4 w-4" />
                                    ) : (
                                      <ChevronDownIcon className="h-4 w-4" />
                                    )}
                                  </button>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex flex-wrap gap-1">
                                {doc.tags && doc.tags.length > 0 ? (
                                  doc.tags.map((tag, idx) => (
                                    <span
                                      key={idx}
                                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                                    >
                                      {tag}
                                    </span>
                                  ))
                                ) : (
                                  <span className="text-sm text-gray-400">-</span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-sm text-gray-500">
                                {formatDate(doc.created_at)}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <button
                                onClick={() => handleDeleteDocument(doc.id, doc.filename)}
                                className="text-red-600 hover:text-red-900"
                              >
                                <TrashIcon className="h-5 w-5" />
                              </button>
                            </td>
                          </tr>
                          {isExpanded && isProcessing && (
                            <tr>
                              <td colSpan={7} className="px-6 py-4 bg-gray-50">
                                <div className="max-w-4xl">
                                  <DocumentProgress
                                    documentId={doc.id}
                                    status={doc.status}
                                    onUpdate={handleProgressUpdate}
                                  />
                                </div>
                              </td>
                            </tr>
                          )}
                          {isExpanded && isProcessed && (
                            <tr>
                              <td colSpan={7} className="px-6 py-4 bg-gray-50">
                                <div className="space-y-3">
                                  <div className="flex items-center justify-between">
                                    <div className="text-sm font-medium text-gray-700">
                                      分块内容（{documentChunks.get(doc.id)?.length || 0}）
                                    </div>
                                    <button
                                      onClick={() => fetchAllChunks(doc.id)}
                                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-white hover:bg-gray-50"
                                    >
                                      <ArrowPathIcon className="h-4 w-4 mr-1" />
                                      刷新分块
                                    </button>
                                  </div>

                                  {chunksLoading.has(doc.id) && (
                                    <div className="flex items-center gap-2 text-sm text-gray-500">
                                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                      正在加载分块...
                                    </div>
                                  )}

                                  {chunksErrors.has(doc.id) && (
                                    <div className="text-sm text-red-600">
                                      {chunksErrors.get(doc.id)}
                                    </div>
                                  )}

                                  {!chunksLoading.has(doc.id) &&
                                    !chunksErrors.has(doc.id) &&
                                    (documentChunks.get(doc.id) || []).length === 0 && (
                                      <div className="text-sm text-gray-500">暂无分块内容</div>
                                    )}

                                  {(documentChunks.get(doc.id) || []).length > 0 && (
                                    <div className="max-h-[480px] overflow-y-auto rounded border border-gray-200 bg-white">
                                      {(documentChunks.get(doc.id) || []).map((chunk, index) => (
                                        <div
                                          key={chunk.id}
                                          className="border-b border-gray-100 p-3 last:border-b-0"
                                        >
                                          <div className="text-xs text-gray-500 mb-1">
                                            #{chunk.chunk_index ?? index + 1}
                                            {chunk.page_number !== null &&
                                              chunk.page_number !== undefined && (
                                                <span className="ml-2">
                                                  页码: {chunk.page_number}
                                                </span>
                                              )}
                                            {chunk.start_char !== null &&
                                              chunk.start_char !== undefined &&
                                              chunk.end_char !== null &&
                                              chunk.end_char !== undefined && (
                                                <span className="ml-2">
                                                  字符: {chunk.start_char}-{chunk.end_char}
                                                </span>
                                              )}
                                          </div>
                                          <pre className="whitespace-pre-wrap text-sm text-gray-800">
                                            {chunk.content}
                                          </pre>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    第 {page} 页，共 {totalPages} 页
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      上一页
                    </button>
                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      下一页
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
