'use client';

import { useState, useEffect } from 'react';
import { Document, knowledgeApi } from '@/lib/api/knowledge';

interface SourceDocumentsProps {
  documentIds: string[];
  onDocumentClick?: (document: Document) => void;
}

export function SourceDocuments({ documentIds, onDocumentClick }: SourceDocumentsProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (documentIds.length === 0) {
      setDocuments([]);
      return;
    }

    const fetchDocuments = async () => {
      setLoading(true);
      setError(null);
      try {
        const docPromises = documentIds.map((id) => knowledgeApi.getDocument(id));
        const docs = await Promise.all(docPromises);
        setDocuments(docs);
      } catch (err: any) {
        setError(err.message || '加载文档失败');
        console.error('Failed to fetch documents:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, [documentIds]);

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-500">
        <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-sm">加载文档中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-500 text-sm">
        <span>❌ {error}</span>
      </div>
    );
  }

  if (documents.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="text-xs font-medium text-gray-600 mb-2">参考文档:</div>
      {documents.map((doc) => (
        <button
          key={doc.id}
          onClick={() => onDocumentClick?.(doc)}
          className="w-full text-left p-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-blue-300 transition-colors"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm text-gray-900 truncate">{doc.filename}</div>
              {doc.metadata?.title && doc.metadata.title !== doc.filename && (
                <div className="text-xs text-gray-500 mt-1">{doc.metadata.title}</div>
              )}
              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                {doc.file_type && (
                  <span className="px-2 py-0.5 bg-gray-100 rounded">
                    {doc.file_type.toUpperCase()}
                  </span>
                )}
                {doc.metadata?.page_count && <span>📄 {doc.metadata.page_count} 页</span>}
                {doc.tags && doc.tags.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {doc.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <svg
              className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>
      ))}
    </div>
  );
}
