'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export function HTTPNode({ data }: NodeProps) {
  // 优先使用业务名称，如果没有则使用 label，最后才使用默认值
  const displayName = data.name || data.label || 'HTTP请求';
  const method = data.config?.method || 'GET';
  const methodColors: Record<string, string> = {
    GET: 'from-green-500 to-green-600',
    POST: 'from-blue-500 to-blue-600',
    PUT: 'from-yellow-500 to-yellow-600',
    DELETE: 'from-red-500 to-red-600',
    PATCH: 'from-purple-500 to-purple-600',
  };
  const methodColor = methodColors[method] || 'from-gray-500 to-gray-600';

  return (
    <div className="group relative px-5 py-4 bg-gradient-to-br from-teal-50 to-cyan-50 border-2 border-teal-300 rounded-xl shadow-md hover:shadow-xl transition-all duration-200 min-w-[220px] backdrop-blur-sm">
      <div className="absolute inset-0 bg-gradient-to-br from-teal-400/10 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-teal-400 !border-2 !border-white"
        style={{ top: -6 }}
      />

      <div className="relative flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-lg flex items-center justify-center text-white text-lg shadow-md">
          🌐
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-teal-900 text-sm leading-tight mb-1.5 line-clamp-2">
            {displayName}
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span
              className={`inline-flex items-center px-2 py-0.5 bg-gradient-to-r ${methodColor} text-white text-xs font-bold rounded-md shadow-sm`}
            >
              {method}
            </span>
            {data.config?.url && (
              <span className="text-xs text-teal-700/80 font-mono truncate max-w-[120px]">
                {data.config.url.substring(0, 20)}...
              </span>
            )}
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-teal-400 !border-2 !border-white"
        style={{ bottom: -6 }}
      />
    </div>
  );
}
