'use client';

import { useState, useEffect, useCallback } from 'react';
import { knowledgeApi, Document } from '@/lib/api/knowledge';
import ErrorMessage from '@/components/ErrorMessage';
import { ErrorBoundary } from '@/components/ErrorBoundary';

interface DocumentStats {
  total: number;
  processed: number;
  processing: number;
  failed: number;
  totalSize: number;
}

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<'semantic' | 'keyword' | 'hybrid'>('semantic');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadTags, setUploadTags] = useState('');
  const [uploadCategory, setUploadCategory] = useState('');
  const [activeTab, setActiveTab] = useState<'documents' | 'search' | 'stats'>('documents');
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [stats, setStats] = useState<DocumentStats>({
    total: 0,
    processed: 0,
    processing: 0,
    failed: 0,
    totalSize: 0,
  });
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
    const interval = setInterval(() => {
      loadDocuments();
    }, 5000); // 每5秒刷新一次，更新处理状态
    return () => clearInterval(interval);
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await knowledgeApi.listDocuments({ page: 1, page_size: 100 });
      const docs = response.documents || [];
      setDocuments(docs);

      // 计算统计信息
      const stats: DocumentStats = {
        total: docs.length,
        processed: docs.filter((d) => d.status === 'processed').length,
        processing: docs.filter((d) => d.status === 'processing').length,
        failed: docs.filter((d) => d.status === 'failed').length,
        totalSize: docs.reduce((sum, d) => sum + d.file_size, 0),
      };
      setStats(stats);
    } catch (error: any) {
      console.error('Failed to load documents:', error);
      setError(error?.message || '加载文档列表失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files);
      setSelectedFiles(files);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setSelectedFiles(Array.from(files));
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('请选择要上传的文件');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      const uploadPromises = selectedFiles.map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        if (uploadTags) {
          formData.append('tags', uploadTags);
        }
        if (uploadCategory) {
          formData.append('category', uploadCategory);
        }
        formData.append('process_async', 'true');

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_KNOWLEDGE_BASE_URL || 'http://43.143.139.197:8004'}/api/documents/upload`,
          {
            method: 'POST',
            body: formData,
          }
        );

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || '上传失败');
        }

        return response.json();
      });

      const results = await Promise.all(uploadPromises);
      setSuccessMessage(`成功上传 ${results.length} 个文档！`);
      setTimeout(() => setSuccessMessage(null), 5000);
      setSelectedFiles([]);
      setUploadTags('');
      setUploadCategory('');
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }
      loadDocuments();
    } catch (error: any) {
      console.error('Upload error:', error);
      setError(error?.message || '上传失败，请稍后重试');
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('请输入搜索关键词');
      return;
    }

    try {
      setSearching(true);
      setError(null);
      let results;
      if (searchType === 'semantic') {
        results = await knowledgeApi.semanticSearch(searchQuery, 10);
      } else if (searchType === 'keyword') {
        results = await knowledgeApi.keywordSearch([searchQuery], false, 1, 10);
      } else {
        results = await knowledgeApi.hybridSearch(searchQuery, [searchQuery], 10);
      }
      setSearchResults(results.results || []);
    } catch (error: any) {
      console.error('Search error:', error);
      setError(error?.message || '搜索失败，请稍后重试');
    } finally {
      setSearching(false);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('确定要删除这个文档吗？删除后无法恢复。')) {
      return;
    }

    try {
      setError(null);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_KNOWLEDGE_BASE_URL || 'http://43.143.139.197:8004'}/api/documents/${documentId}`,
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '删除失败' }));
        throw new Error(errorData.detail || '删除失败');
      }

      setSuccessMessage('文档删除成功');
      setTimeout(() => setSuccessMessage(null), 3000);
      loadDocuments();
    } catch (error: any) {
      console.error('Delete error:', error);
      setError(error?.message || '删除失败，请稍后重试');
    }
  };

  const handleViewDocument = async (doc: Document) => {
    try {
      setError(null);
      const fullDoc = await knowledgeApi.getDocument(doc.id);
      setSelectedDoc(fullDoc);
    } catch (error: any) {
      console.error('Failed to load document:', error);
      setError(error?.message || '加载文档详情失败，请稍后重试');
    }
  };

  const filteredDocuments = documents.filter((doc) => {
    if (filterStatus !== 'all' && doc.status !== filterStatus) return false;
    if (filterType !== 'all' && doc.file_type !== filterType) return false;
    return true;
  });

  const uniqueTypes = Array.from(new Set(documents.map((d) => d.file_type)));

  return (
    <ErrorBoundary>
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* 错误和成功提示 */}
        <ErrorMessage message={error} type="error" onClose={() => setError(null)} />
        <ErrorMessage message={successMessage} type="success" onClose={() => setSuccessMessage(null)} autoClose />

        <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">知识库管理</h1>
        <p className="text-gray-600">上传、管理和搜索文档，支持自动向量化和智能检索</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
          <div className="text-sm text-gray-600 mb-1">总文档数</div>
          <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
          <div className="text-sm text-gray-600 mb-1">已处理</div>
          <div className="text-2xl font-bold text-green-600">{stats.processed}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
          <div className="text-sm text-gray-600 mb-1">处理中</div>
          <div className="text-2xl font-bold text-yellow-600">{stats.processing}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
          <div className="text-sm text-gray-600 mb-1">总大小</div>
          <div className="text-2xl font-bold text-gray-900">
            {(stats.totalSize / 1024 / 1024).toFixed(2)} MB
          </div>
        </div>
      </div>

      {/* 标签页切换 */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('documents')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'documents'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          文档管理
        </button>
        <button
          onClick={() => setActiveTab('search')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'search'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          智能搜索
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'stats'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          统计分析
        </button>
      </div>

      {activeTab === 'documents' ? (
        <div className="space-y-6">
          {/* 上传区域 - 支持拖拽 */}
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h2 className="text-lg font-semibold mb-4">上传文档</h2>
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                onChange={handleFileSelect}
                accept=".pdf,.doc,.docx,.txt,.md,.xls,.xlsx"
                multiple
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                <svg
                  className="w-12 h-12 text-gray-400 mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <p className="text-sm text-gray-600 mb-2">
                  拖拽文件到此处或 <span className="text-blue-600">点击选择文件</span>
                </p>
                <p className="text-xs text-gray-500">
                  支持 PDF、Word、Excel、TXT、Markdown，最大 100MB，可批量上传
                </p>
              </label>
            </div>

            {selectedFiles.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-sm font-medium text-gray-700">
                  已选择文件 ({selectedFiles.length}):
                </p>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {selectedFiles.map((file, idx) => (
                    <div key={idx} className="p-2 bg-gray-50 rounded text-sm text-gray-700">
                      {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  标签（可选，用逗号分隔）
                </label>
                <input
                  type="text"
                  value={uploadTags}
                  onChange={(e) => setUploadTags(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="技术,文档,教程"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">分类（可选）</label>
                <input
                  type="text"
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="技术文档"
                />
              </div>
            </div>

            <button
              onClick={handleUpload}
              disabled={selectedFiles.length === 0 || uploading}
              className="mt-4 w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {uploading
                ? '上传中...'
                : `上传并处理 ${selectedFiles.length > 0 ? `(${selectedFiles.length}个文件)` : ''}`}
            </button>
          </div>

          {/* 筛选和搜索 */}
          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">状态筛选</label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="all">全部</option>
                  <option value="processed">已处理</option>
                  <option value="processing">处理中</option>
                  <option value="uploading">上传中</option>
                  <option value="failed">失败</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">类型筛选</label>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="all">全部</option>
                  {uniqueTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={loadDocuments}
                  className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  刷新
                </button>
              </div>
            </div>
          </div>

          {/* 文档列表 */}
          <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold">文档列表 ({filteredDocuments.length})</h2>
            </div>
            {loading ? (
              <div className="p-8 text-center text-gray-500">加载中...</div>
            ) : filteredDocuments.length === 0 ? (
              <div className="p-8 text-center text-gray-500">暂无文档</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        文件名
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        类型
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        大小
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        状态
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        标签
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        上传时间
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredDocuments.map((doc) => (
                      <tr key={doc.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div
                            className="text-sm font-medium text-gray-900 cursor-pointer hover:text-blue-600"
                            onClick={() => handleViewDocument(doc)}
                          >
                            {doc.filename}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">{doc.file_type}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">
                            {(doc.file_size / 1024).toFixed(2)} KB
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded ${
                              doc.status === 'processed'
                                ? 'bg-green-100 text-green-800'
                                : doc.status === 'processing'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : doc.status === 'failed'
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {doc.status === 'processed'
                              ? '✓ 已向量化'
                              : doc.status === 'processing'
                                ? '⏳ 处理中'
                                : doc.status === 'failed'
                                  ? '✗ 失败'
                                  : '⏸ 待处理'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-wrap gap-1">
                            {doc.tags?.map((tag, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">
                            {new Date(doc.uploaded_at).toLocaleString('zh-CN')}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                          <button
                            onClick={() => handleViewDocument(doc)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            查看
                          </button>
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            删除
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : activeTab === 'search' ? (
        <div className="space-y-6">
          {/* 搜索区域 */}
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h2 className="text-lg font-semibold mb-4">智能搜索</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">搜索类型</label>
                <select
                  value={searchType}
                  onChange={(e) =>
                    setSearchType(e.target.value as 'semantic' | 'keyword' | 'hybrid')
                  }
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="semantic">语义搜索（推荐）</option>
                  <option value="keyword">关键词搜索</option>
                  <option value="hybrid">混合搜索</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">搜索查询</label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="输入您要搜索的内容..."
                />
              </div>

              <button
                onClick={handleSearch}
                disabled={!searchQuery.trim() || searching}
                className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {searching ? '搜索中...' : '搜索'}
              </button>
            </div>
          </div>

          {/* 搜索结果 */}
          {searchResults.length > 0 && (
            <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold">搜索结果 ({searchResults.length})</h2>
              </div>
              <div className="divide-y divide-gray-200">
                {searchResults.map((result, idx) => (
                  <div key={idx} className="p-6 hover:bg-gray-50">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-sm font-semibold text-gray-900">
                          {result.document_name}
                        </h3>
                        <p className="text-xs text-gray-500 mt-1">
                          相似度: {(result.score * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 mt-2 line-clamp-3">{result.content}</p>
                    {result.metadata && Object.keys(result.metadata).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {Object.entries(result.metadata)
                          .slice(0, 3)
                          .map(([key, value]) => (
                            <span key={key} className="text-xs text-gray-500">
                              {key}: {String(value)}
                            </span>
                          ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h2 className="text-lg font-semibold mb-4">文档统计</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-3xl font-bold text-blue-600">{stats.total}</div>
                <div className="text-sm text-gray-600 mt-1">总文档数</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-3xl font-bold text-green-600">{stats.processed}</div>
                <div className="text-sm text-gray-600 mt-1">已向量化</div>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <div className="text-3xl font-bold text-yellow-600">{stats.processing}</div>
                <div className="text-sm text-gray-600 mt-1">处理中</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-gray-600">
                  {(stats.totalSize / 1024 / 1024).toFixed(2)}
                </div>
                <div className="text-sm text-gray-600 mt-1">总大小 (MB)</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h2 className="text-lg font-semibold mb-4">文档类型分布</h2>
            <div className="space-y-2">
              {uniqueTypes.map((type) => {
                const count = documents.filter((d) => d.file_type === type).length;
                const percentage = stats.total > 0 ? (count / stats.total) * 100 : 0;
                return (
                  <div key={type} className="flex items-center gap-4">
                    <div className="w-24 text-sm text-gray-600">{type}</div>
                    <div className="flex-1 bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-blue-600 h-4 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <div className="w-16 text-sm text-gray-600 text-right">{count}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* 文档详情模态框 */}
      {selectedDoc && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setSelectedDoc(null)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full m-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-semibold">{selectedDoc.filename}</h2>
              <button
                onClick={() => setSelectedDoc(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">文件类型</label>
                  <p className="text-sm text-gray-900">{selectedDoc.file_type}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">文件大小</label>
                  <p className="text-sm text-gray-900">
                    {(selectedDoc.file_size / 1024).toFixed(2)} KB
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">状态</label>
                  <p className="text-sm text-gray-900">
                    {selectedDoc.status === 'processed'
                      ? '✓ 已向量化'
                      : selectedDoc.status === 'processing'
                        ? '⏳ 处理中'
                        : '待处理'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">上传时间</label>
                  <p className="text-sm text-gray-900">
                    {new Date(selectedDoc.uploaded_at).toLocaleString('zh-CN')}
                  </p>
                </div>
              </div>
              {selectedDoc.tags && selectedDoc.tags.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-700">标签</label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {selectedDoc.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {selectedDoc.metadata && (
                <div>
                  <label className="text-sm font-medium text-gray-700">元数据</label>
                  <pre className="mt-1 p-3 bg-gray-50 rounded text-xs overflow-x-auto">
                    {JSON.stringify(selectedDoc.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      </div>
    </ErrorBoundary>
  );
}
