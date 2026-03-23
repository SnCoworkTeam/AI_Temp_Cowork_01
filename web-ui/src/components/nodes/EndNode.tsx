'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export function EndNode({ data }: NodeProps) {
  // 优先使用业务名称，如果没有则使用 label，最后才使用默认值
  const displayName = data.name || data.label || '结束';

  return (
    <div className="group relative px-5 py-4 bg-gradient-to-br from-red-50 via-rose-50 to-red-100 border-2 border-red-400 rounded-full shadow-md hover:shadow-xl transition-all duration-200 min-w-[160px] backdrop-blur-sm">
      <div className="absolute inset-0 bg-gradient-to-br from-red-400/20 to-transparent rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>

      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-red-400 !border-2 !border-white"
        style={{ top: -6 }}
      />

      <div className="relative flex items-center gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-red-500 to-rose-600 rounded-full flex items-center justify-center text-white text-lg shadow-lg">
          ■
        </div>
        <div className="font-semibold text-red-900 text-sm leading-tight">{displayName}</div>
      </div>
    </div>
  );
}
