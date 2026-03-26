'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export function AgentNode({ data }: NodeProps) {
  // 优先使用业务名称，如果没有则使用 label，最后才使用默认值
  const displayName = data.name || data.label || '智能体节点';

  return (
    <div className="group relative px-5 py-4 bg-gradient-to-br from-emerald-50 to-teal-50 border-2 border-emerald-300 rounded-xl shadow-md hover:shadow-xl transition-all duration-200 min-w-[220px] backdrop-blur-sm">
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-400/10 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-emerald-400 !border-2 !border-white"
        style={{ top: -6 }}
      />

      <div className="relative flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center text-white text-lg shadow-md">
          🤖
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-emerald-900 text-sm leading-tight mb-1.5 line-clamp-2">
            {displayName}
          </div>
          <div className="mt-2">
            <span className="inline-flex items-center px-2 py-0.5 bg-emerald-200/60 text-emerald-800 text-xs font-medium rounded-md">
              {data.config?.agent_id
                ? `智能体: ${data.config.agent_id.substring(0, 12)}...`
                : '未配置智能体'}
            </span>
          </div>
          {data.config?.description && (
            <div className="mt-2 text-xs text-emerald-700/80 line-clamp-2 italic">
              {data.config.description}
            </div>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-emerald-400 !border-2 !border-white"
        style={{ bottom: -6 }}
      />
    </div>
  );
}
