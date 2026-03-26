'use client';

import React from 'react';
import { MetadataCard } from './MetadataCard';

interface MetadataItem {
  id: string | number;
  name: string;
  display_name?: string;
  description?: string;
  type?: string;
  asset_type?: string;
  status?: string;
  classification?: string;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
  tags?: string[];
  [key: string]: any;
}

type MetadataType = 'all' | 'data-assets' | 'workflows' | 'ai-models' | 'business-entities';

interface CardGridViewProps {
  items: MetadataItem[];
  type: MetadataType;
  onItemClick?: (item: MetadataItem) => void;
  loading?: boolean;
  emptyMessage?: string;
}

export function CardGridView({
  items,
  type,
  onItemClick,
  loading = false,
  emptyMessage = '暂无数据',
}: CardGridViewProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-gray-600">加载中...</span>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
        <p className="text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {items.map((item) => (
        <MetadataCard key={`${type}-${item.id}`} item={item} type={type} onClick={onItemClick} />
      ))}
    </div>
  );
}
