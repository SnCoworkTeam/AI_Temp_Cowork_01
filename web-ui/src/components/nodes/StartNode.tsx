'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export function StartNode({ data }: NodeProps) {
  // 优先使用业务名称，如果没有则使用 label，最后才使用默认值
  const displayName = data.name || data.label || '开始';

  return (
    <div className="group relative px-5 py-4 bg-gradient-to-br from-green-50 via-emerald-50 to-green-100 border-2 border-green-400 rounded-full shadow-md hover:shadow-xl transition-all duration-200 min-w-[160px] backdrop-blur-sm">
      <div className="absolute inset-0 bg-gradient-to-br from-green-400/20 to-transparent rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>

      <div className="relative flex items-center gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white text-lg shadow-lg">
          ▶
        </div>
        <div className="font-semibold text-green-900 text-sm leading-tight">{displayName}</div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-green-400 !border-2 !border-white"
        style={{ bottom: -6 }}
      />
    </div>
  );
}
