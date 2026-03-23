'use client';

import React from 'react';
import { Handle, Position } from 'reactflow';

interface KnowledgeSearchNodeProps {
  data: {
    label?: string;
    config?: {
      search_type?: string;
      query_field?: string;
      limit?: number;
    };
  };
  selected?: boolean;
}

export function KnowledgeSearchNode({ data, selected }: KnowledgeSearchNodeProps) {
  // 优先使用业务名称，如果没有则使用 label，最后才使用默认值
  const displayName = (data as any).name || data.label || '知识搜索';
  const config = data.config || {};
  const searchType = config.search_type || 'semantic';
  const queryField = config.query_field || 'query';
  const limit = config.limit || 5;

  return (
    <div
      className={`group relative px-5 py-4 bg-gradient-to-br from-cyan-50 to-sky-50 border-2 rounded-xl shadow-md hover:shadow-xl transition-all duration-200 min-w-[220px] backdrop-blur-sm ${
        selected ? 'border-blue-500 ring-2 ring-blue-300' : 'border-cyan-300'
      }`}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-400/10 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-cyan-400 !border-2 !border-white"
        style={{ top: -6 }}
      />

      <div className="relative flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-cyan-500 to-sky-600 rounded-lg flex items-center justify-center text-white text-lg shadow-md">
          🔍
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-cyan-900 text-sm leading-tight mb-1.5 line-clamp-2">
            {displayName}
          </div>
          <div className="mt-2 space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-cyan-700/70">类型</span>
              <span className="px-2 py-0.5 bg-cyan-200/60 text-cyan-800 text-xs font-medium rounded">
                {searchType === 'semantic' ? '语义' : '关键词'}
              </span>
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-cyan-700/70">字段</span>
              <span className="text-xs font-medium text-cyan-800 font-mono">{queryField}</span>
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-cyan-700/70">数量</span>
              <span className="px-2 py-0.5 bg-cyan-200/60 text-cyan-800 text-xs font-bold rounded">
                {limit}
              </span>
            </div>
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-cyan-400 !border-2 !border-white"
        style={{ bottom: -6 }}
      />
    </div>
  );
}
