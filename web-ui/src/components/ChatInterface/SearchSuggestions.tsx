'use client';

import { useState, useEffect, useRef } from 'react';
import { knowledgeApi, SearchResult } from '@/lib/api/knowledge';

interface SearchSuggestionsProps {
  query: string;
  onSelect: (query: string) => void;
  onSearch?: (query: string) => void;
  maxSuggestions?: number;
}

export function SearchSuggestions({
  query,
  onSelect,
  onSearch,
  maxSuggestions = 5,
}: SearchSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!query || query.trim().length < 2) {
      setSuggestions([]);
      return;
    }

    const searchTimeout = setTimeout(async () => {
      setLoading(true);
      try {
        const response = await knowledgeApi.semanticSearch(query, maxSuggestions);
        setSuggestions(response.results || []);
      } catch (error) {
        console.error('Failed to fetch search suggestions:', error);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300); // 防抖延迟

    return () => clearTimeout(searchTimeout);
  }, [query, maxSuggestions]);

  useEffect(() => {
    setSelectedIndex(-1);
  }, [suggestions]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          e.preventDefault();
          const selected = suggestions[selectedIndex];
          onSelect(selected.content);
        } else if (onSearch) {
          e.preventDefault();
          onSearch(query);
        }
        break;
      case 'Escape':
        setSuggestions([]);
        break;
    }
  };

  // 将键盘事件传递给父组件
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (suggestions.length > 0 && ['ArrowDown', 'ArrowUp', 'Enter', 'Escape'].includes(e.key)) {
        handleKeyDown(e as any);
      }
    };

    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, [suggestions, selectedIndex]);

  if (suggestions.length === 0 && !loading) {
    return null;
  }

  return (
    <div
      ref={suggestionsRef}
      className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto z-50"
    >
      {loading && (
        <div className="p-3 text-center text-gray-500 text-sm">
          <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="ml-2">搜索中...</span>
        </div>
      )}

      {!loading && suggestions.length > 0 && (
        <div className="py-2">
          <div className="px-3 py-2 text-xs font-medium text-gray-500 border-b border-gray-100">
            知识库建议
          </div>
          {suggestions.map((suggestion, index) => (
            <button
              key={suggestion.chunk_id || index}
              onClick={() => {
                onSelect(suggestion.content);
                setSuggestions([]);
              }}
              className={`w-full text-left px-3 py-2 hover:bg-gray-50 transition-colors ${
                index === selectedIndex ? 'bg-blue-50' : ''
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-gray-900 line-clamp-2">{suggestion.content}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {suggestion.document_name}
                    {suggestion.score && (
                      <span className="ml-2">({(suggestion.score * 100).toFixed(0)}% 匹配)</span>
                    )}
                  </div>
                </div>
                <svg
                  className="w-4 h-4 text-gray-400 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

interface QuickSearchProps {
  onSearch: (query: string) => void;
}

export function QuickSearch({ onSearch }: QuickSearchProps) {
  const quickQueries = ['最新文档', '技术文档', '产品文档', '用户手册', 'API文档', '常见问题'];

  return (
    <div className="p-2 border-b border-gray-200">
      <div className="text-xs font-medium text-gray-500 mb-2">快速搜索:</div>
      <div className="flex flex-wrap gap-2">
        {quickQueries.map((query) => (
          <button
            key={query}
            onClick={() => onSearch(query)}
            className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
          >
            {query}
          </button>
        ))}
      </div>
    </div>
  );
}
