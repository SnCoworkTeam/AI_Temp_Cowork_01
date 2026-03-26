'use client';

import Image from 'next/image';

export function PortalHeader() {
  return (
    <div className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center gap-3">
          <img
            src="/logo.jpg"
            alt="中化国际"
            className="h-10 w-auto object-contain"
            onError={(e) => {
              // 如果logo加载失败，隐藏图片
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
          <h1 className="text-2xl font-bold text-gray-900">Lumina AIOS</h1>
        </div>
      </div>
    </div>
  );
}
