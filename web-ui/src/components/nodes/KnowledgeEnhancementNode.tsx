'use client';

import React from 'react';
import { Handle, Position } from 'reactflow';

interface KnowledgeEnhancementNodeProps {
  data: {
    label?: string;
    config?: {
      enhancement_strategy?: string;
      enable_search?: boolean;
      enable_graph?: boolean;
      merge_mode?: string;
    };
  };
  selected?: boolean;
}

export function KnowledgeEnhancementNode({ data, selected }: KnowledgeEnhancementNodeProps) {
  // 优先使用业务名称，如果没有则使用 label，最后才使用默认值
  const displayName = (data as any).name || data.label || '知识增强';
  const config = data.config || {};
  const strategy = config.enhancement_strategy || 'search_and_merge';
  const enableSearch = config.enable_search !== false;
  const enableGraph = config.enable_graph !== false;
  const mergeMode = config.merge_mode || 'append';

  const mergeModeLabels: Record<string, string> = {
    append: '追加',
    prepend: '前置',
    replace: '替换',
    context: '上下文',
  };

  return (
    <div
      className={`group relative px-5 py-4 bg-gradient-to-br from-pink-50 to-rose-50 border-2 rounded-xl shadow-md hover:shadow-xl transition-all duration-200 min-w-[220px] backdrop-blur-sm ${
        selected ? 'border-blue-500 ring-2 ring-blue-300' : 'border-pink-300'
      }`}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-pink-400/10 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-pink-400 !border-2 !border-white"
        style={{ top: -6 }}
      />

      <div className="relative flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-pink-500 to-rose-600 rounded-lg flex items-center justify-center text-white text-lg shadow-md">
          ✨
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-pink-900 text-sm leading-tight mb-1.5 line-clamp-2">
            {displayName}
          </div>
          <div className="mt-2 space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-pink-700/70">策略</span>
              <span className="px-2 py-0.5 bg-pink-200/60 text-pink-800 text-xs font-medium rounded">
                {strategy}
              </span>
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-pink-700/70">合并</span>
              <span className="px-2 py-0.5 bg-pink-200/60 text-pink-800 text-xs font-medium rounded">
                {mergeModeLabels[mergeMode] || mergeMode}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-2">
              {enableSearch && (
                <span className="px-2 py-0.5 bg-cyan-200/70 text-cyan-800 rounded-md text-xs font-medium shadow-sm">
                  搜索
                </span>
              )}
              {enableGraph && (
                <span className="px-2 py-0.5 bg-purple-200/70 text-purple-800 rounded-md text-xs font-medium shadow-sm">
                  图谱
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-pink-400 !border-2 !border-white"
        style={{ bottom: -6 }}
      />
    </div>
  );
}
