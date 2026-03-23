'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export function LogNode({ data }: NodeProps) {
  // 优先使用业务名称，如果没有则使用 label，最后才使用默认值
  const displayName = data.name || data.label || '日志';
  const logLevel = data.config?.log_level || 'INFO';
  const levelColors: Record<string, string> = {
    INFO: 'bg-blue-200/60 text-blue-800',
    WARN: 'bg-yellow-200/60 text-yellow-800',
    ERROR: 'bg-red-200/60 text-red-800',
    DEBUG: 'bg-gray-200/60 text-gray-800',
  };
  const levelColor = levelColors[logLevel] || 'bg-orange-200/60 text-orange-800';

  return (
    <div className="group relative px-5 py-4 bg-gradient-to-br from-orange-50 to-amber-50 border-2 border-orange-300 rounded-xl shadow-md hover:shadow-xl transition-all duration-200 min-w-[220px] backdrop-blur-sm">
      <div className="absolute inset-0 bg-gradient-to-br from-orange-400/10 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-orange-400 !border-2 !border-white"
        style={{ top: -6 }}
      />

      <div className="relative flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-orange-500 to-amber-600 rounded-lg flex items-center justify-center text-white text-lg shadow-md">
          📝
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-orange-900 text-sm leading-tight mb-1.5 line-clamp-2">
            {displayName}
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span
              className={`inline-flex items-center px-2 py-0.5 ${levelColor} text-xs font-bold rounded-md`}
            >
              {logLevel}
            </span>
          </div>
          {data.config?.message && (
            <div className="mt-2 text-xs text-orange-700/80 line-clamp-1 italic bg-orange-100/50 px-2 py-1 rounded">
              "{data.config.message.substring(0, 35)}..."
            </div>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-orange-400 !border-2 !border-white"
        style={{ bottom: -6 }}
      />
    </div>
  );
}
