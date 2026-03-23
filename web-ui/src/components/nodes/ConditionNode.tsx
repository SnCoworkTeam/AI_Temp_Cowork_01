'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export function ConditionNode({ data }: NodeProps) {
  // 优先使用业务名称，如果没有则使用 label，最后才使用默认值
  const displayName = data.name || data.label || '条件判断';

  return (
    <div className="group relative px-5 py-4 bg-gradient-to-br from-amber-50 via-yellow-50 to-amber-100 border-2 border-amber-300 rounded-xl shadow-md hover:shadow-xl transition-all duration-200 min-w-[220px] backdrop-blur-sm">
      <div className="absolute inset-0 bg-gradient-to-br from-amber-400/10 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-amber-400 !border-2 !border-white"
        style={{ top: -6 }}
      />

      <div className="relative flex items-start gap-3 mb-3">
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-amber-500 to-yellow-600 rounded-lg flex items-center justify-center text-white text-lg shadow-md">
          ❓
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-amber-900 text-sm leading-tight mb-1.5 line-clamp-2">
            {displayName}
          </div>
          {data.config?.condition && (
            <div className="mt-2 text-xs text-amber-700/80 font-mono bg-amber-100/50 px-2 py-1 rounded line-clamp-1">
              {data.config.condition.substring(0, 35)}...
            </div>
          )}
        </div>
      </div>

      <div className="relative flex items-center justify-between mt-3 pt-3 border-t border-amber-200">
        <div className="flex items-center gap-2">
          <Handle
            type="source"
            position={Position.Bottom}
            id="true"
            className="!w-3 !h-3 !bg-green-500 !border-2 !border-white"
            style={{ left: '25%', bottom: -6 }}
          />
          <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-0.5 rounded">
            真
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Handle
            type="source"
            position={Position.Bottom}
            id="false"
            className="!w-3 !h-3 !bg-red-500 !border-2 !border-white"
            style={{ left: '75%', bottom: -6 }}
          />
          <span className="text-xs font-medium text-red-700 bg-red-100 px-2 py-0.5 rounded">
            假
          </span>
        </div>
      </div>
    </div>
  );
}
