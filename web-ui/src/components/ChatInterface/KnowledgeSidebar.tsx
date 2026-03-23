'use client';

import { useState, useEffect } from 'react';
import { knowledgeApi, SearchResult, Document, KnowledgeGraphNode } from '@/lib/api/knowledge';

interface KnowledgeSidebarProps {
  query?: string;
  onClose?: () => void;
  onSelectDocument?: (document: Document) => void;
  onSelectConcept?: (concept: string) => void;
}

export function KnowledgeSidebar({
  query,
  onClose,
  onSelectDocument,
  onSelectConcept,
}: KnowledgeSidebarProps) {
  const [searchQuery, setSearchQuery] = useState(query || '');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [relatedDocuments, setRelatedDocuments] = useState<Document[]>([]);
  const [relatedConcepts, setRelatedConcepts] = useState<KnowledgeGraphNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'search' | 'documents' | 'graph'>('search');

  // 搜索知识库
  const handleSearch = async (q: string) => {
    if (!q.trim()) return;

    setLoading(true);
    try {
      const response = await knowledgeApi.semanticSearch(q, 10);
      setSearchResults(response.results || []);

      // 获取相关文档
      const docIds = Array.from(new Set(response.results.map((r) => r.document_id)));
      if (docIds.length > 0) {
        const docs = await Promise.all(docIds.map((id) => knowledgeApi.getDocument(id)));
        setRelatedDocuments(docs);
      }

      // 尝试从查询中提取概念并获取相关概念
      const concepts = q.split(/\s+/).filter((w) => w.length > 2);
      if (concepts.length > 0) {
        try {
          const conceptResponse = await knowledgeApi.getRelatedConcepts(concepts[0], 5);
          setRelatedConcepts(conceptResponse.related_concepts || []);
        } catch (error) {
          console.error('Failed to get related concepts:', error);
        }
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (query) {
      setSearchQuery(query);
      handleSearch(query);
    }
  }, [query]);

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col h-full">
      {/* 头部 */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">知识库</h2>
        {onClose && (
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600 rounded">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

      {/* 搜索框 */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch(searchQuery);
              }
            }}
            placeholder="搜索知识库..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={() => handleSearch(searchQuery)}
            disabled={loading || !searchQuery.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              '搜索'
            )}
          </button>
        </div>
      </div>

      {/* 标签页 */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('search')}
          className={`flex-1 px-4 py-2 text-sm font-medium ${
            activeTab === 'search'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          搜索结果
        </button>
        <button
          onClick={() => setActiveTab('documents')}
          className={`flex-1 px-4 py-2 text-sm font-medium ${
            activeTab === 'documents'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          相关文档
        </button>
        <button
          onClick={() => setActiveTab('graph')}
          className={`flex-1 px-4 py-2 text-sm font-medium ${
            activeTab === 'graph'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          知识图谱
        </button>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'search' && (
          <div className="space-y-3">
            {searchResults.length === 0 && !loading && (
              <div className="text-center text-gray-500 py-8">
                <div className="text-4xl mb-2">📚</div>
                <p>暂无搜索结果</p>
                <p className="text-sm mt-1">尝试搜索其他关键词</p>
              </div>
            )}
            {searchResults.map((result, index) => (
              <div
                key={result.chunk_id || index}
                className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer"
                onClick={() => {
                  if (onSelectDocument) {
                    const doc = relatedDocuments.find((d) => d.id === result.document_id);
                    if (doc) onSelectDocument(doc);
                  }
                }}
              >
                <div className="text-sm font-medium text-gray-900 mb-1">{result.document_name}</div>
                <div className="text-xs text-gray-600 line-clamp-3 mb-2">{result.content}</div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    {(result.score * 100).toFixed(0)}% 匹配
                  </span>
                  <button
                    className="text-xs text-blue-600 hover:text-blue-800"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectConcept?.(result.content);
                    }}
                  >
                    查看详情
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="space-y-2">
            {relatedDocuments.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <p>暂无相关文档</p>
              </div>
            )}
            {relatedDocuments.map((doc) => (
              <div
                key={doc.id}
                className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer"
                onClick={() => onSelectDocument?.(doc)}
              >
                <div className="font-medium text-sm text-gray-900">{doc.filename}</div>
                {doc.metadata?.title && (
                  <div className="text-xs text-gray-600 mt-1">{doc.metadata.title}</div>
                )}
                <div className="flex items-center gap-2 mt-2">
                  {doc.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'graph' && (
          <div className="space-y-2">
            {relatedConcepts.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <p>暂无相关概念</p>
              </div>
            )}
            {relatedConcepts.map((concept) => (
              <button
                key={concept.id}
                onClick={() => onSelectConcept?.(concept.label)}
                className="w-full text-left p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
              >
                <div className="font-medium text-sm text-gray-900">{concept.label}</div>
                {concept.type && (
                  <div className="text-xs text-gray-500 mt-1">类型: {concept.type}</div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
