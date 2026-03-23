'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export function LLMNode({ data }: NodeProps) {
  // 优先使用业务名称，如果没有则使用 label，最后才使用默认值
  const displayName = data.name || data.label || 'LLM节点';
  const model = data.config?.model || process.env.NEXT_PUBLIC_LLM_MODEL || 'deepseek-chat';

  return (
    <div className="group relative px-5 py-4 bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-300 rounded-xl shadow-md hover:shadow-xl transition-all duration-200 min-w-[220px] backdrop-blur-sm">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400/10 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-blue-400 !border-2 !border-white"
        style={{ top: -6 }}
      />

      <div className="relative flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white text-lg shadow-md">
          🤖
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-blue-900 text-sm leading-tight mb-1.5 line-clamp-2">
            {displayName}
          </div>
          <div className="flex items-center gap-1.5 mt-2">
            <span className="inline-flex items-center px-2 py-0.5 bg-blue-200/60 text-blue-800 text-xs font-medium rounded-md">
              <span className="w-1.5 h-1.5 bg-blue-600 rounded-full mr-1.5"></span>
              {model}
            </span>
          </div>
          {data.config?.prompt_template && (
            <div className="mt-2 text-xs text-blue-700/80 line-clamp-1 italic">
              "{data.config.prompt_template.substring(0, 35)}..."
            </div>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-blue-400 !border-2 !border-white"
        style={{ bottom: -6 }}
      />
    </div>
  );
}
