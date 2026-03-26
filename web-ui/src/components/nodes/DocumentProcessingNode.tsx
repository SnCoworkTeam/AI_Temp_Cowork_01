'use client';

import React from 'react';
import { Handle, Position } from 'reactflow';

interface DocumentProcessingNodeProps {
  data: {
    label?: string;
    config?: {
      process_type?: string;
      input_field?: string;
      extract_metadata?: boolean;
    };
  };
  selected?: boolean;
}

export function DocumentProcessingNode({ data, selected }: DocumentProcessingNodeProps) {
  // 优先使用业务名称，如果没有则使用 label，最后才使用默认值
  const displayName = (data as any).name || data.label || '文档处理';
  const config = data.config || {};
  const processType = config.process_type || 'parse';
  const inputField = config.input_field || 'document_id';

  const processTypeLabels: Record<string, string> = {
    upload: '上传',
    parse: '解析',
    extract_metadata: '提取元数据',
  };

  return (
    <div
      className={`group relative px-5 py-4 bg-gradient-to-br from-amber-50 to-yellow-50 border-2 rounded-xl shadow-md hover:shadow-xl transition-all duration-200 min-w-[220px] backdrop-blur-sm ${
        selected ? 'border-blue-500 ring-2 ring-blue-300' : 'border-amber-300'
      }`}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-amber-400/10 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-amber-400 !border-2 !border-white"
        style={{ top: -6 }}
      />

      <div className="relative flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-amber-500 to-yellow-600 rounded-lg flex items-center justify-center text-white text-lg shadow-md">
          📄
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-amber-900 text-sm leading-tight mb-1.5 line-clamp-2">
            {displayName}
          </div>
          <div className="mt-2 space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-amber-700/70">类型</span>
              <span className="px-2 py-0.5 bg-amber-200/60 text-amber-800 text-xs font-medium rounded">
                {processTypeLabels[processType] || processType}
              </span>
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-amber-700/70">字段</span>
              <span className="text-xs font-medium text-amber-800 font-mono">{inputField}</span>
            </div>
            {config.extract_metadata && (
              <div className="flex items-center gap-1.5 mt-2">
                <span className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center text-white text-xs">
                  ✓
                </span>
                <span className="text-xs text-green-700 font-medium">提取元数据</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-amber-400 !border-2 !border-white"
        style={{ bottom: -6 }}
      />
    </div>
  );
}
