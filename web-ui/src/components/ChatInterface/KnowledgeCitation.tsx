'use client';

import { useState } from 'react';
import { SearchResult } from '@/lib/api/knowledge';

interface KnowledgeCitationProps {
  citation: SearchResult;
  index?: number;
  onViewSource?: (documentId: string, chunkId: string) => void;
}

export function KnowledgeCitation({ citation, index, onViewSource }: KnowledgeCitationProps) {
  const [expanded, setExpanded] = useState(false);

  const handleClick = () => {
    if (onViewSource) {
      onViewSource(citation.document_id, citation.chunk_id);
    }
    setExpanded(!expanded);
  };

  return (
    <div className="mt-2">
      <button
        onClick={handleClick}
        className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 underline"
      >
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span>
          来源 {index !== undefined ? index + 1 : ''}: {citation.document_name}
        </span>
        {citation.score && (
          <span className="text-gray-500">({(citation.score * 100).toFixed(0)}%)</span>
        )}
      </button>

      {expanded && (
        <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm">
          <div className="font-medium text-gray-700 mb-2">文档片段:</div>
          <div className="text-gray-600 whitespace-pre-wrap">{citation.content}</div>
          {citation.metadata && Object.keys(citation.metadata).length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <div className="text-xs text-gray-500">
                文档ID: {citation.document_id} | 块ID: {citation.chunk_id}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface KnowledgeCitationsProps {
  citations: SearchResult[];
  onViewSource?: (documentId: string, chunkId: string) => void;
}

export function KnowledgeCitations({ citations, onViewSource }: KnowledgeCitationsProps) {
  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-200">
      <div className="text-xs font-medium text-gray-600 mb-2">知识来源:</div>
      <div className="space-y-1">
        {citations.map((citation, index) => (
          <KnowledgeCitation
            key={citation.chunk_id || index}
            citation={citation}
            index={index}
            onViewSource={onViewSource}
          />
        ))}
      </div>
    </div>
  );
}
