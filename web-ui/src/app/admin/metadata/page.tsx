'use client';

import React, { useState, useEffect } from 'react';
import { AuthGuard } from '@/components/AuthGuard';
import {
  MagnifyingGlassIcon,
  EyeIcon,
  InformationCircleIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { MetadataViewEngine } from '@/components/metadata';
import { ClassificationDimensionEditor } from '@/components/metadata/ClassificationDimensionEditor';
import {
  extractUniqueClassifications,
  getClassificationDisplayName,
} from '@/lib/metadata-classification';

interface MetadataItem {
  id: string | number;
  name: string;
  display_name?: string;
  description?: string;
  type?: string;
  asset_type?: string;
  status?: string;
  classification?: string;
  classification_dimensions?: {
    primary?: string;
    business?: { domain?: string; criticality?: string };
    technical?: { source?: string; format?: string; framework?: string };
    lifecycle?: { stage?: string; status?: string; freshness?: string };
    governance?: { security?: string; quality?: string; compliance?: string[] };
  };
  standardized_tags?: string[];
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
  tags?: string[];
  [key: string]: any;
}

type MetadataType = 'all' | 'data-assets' | 'workflows' | 'ai-models' | 'business-entities';

export default function MetadataManagementPage() {
  const [activeTab, setActiveTab] = useState<MetadataType>('data-assets');
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedClassification, setSelectedClassification] = useState<string>('all');
  const [metadata, setMetadata] = useState<{
    data_assets: MetadataItem[];
    workflows: MetadataItem[];
    ai_models: MetadataItem[];
    business_entities: MetadataItem[];
  }>({
    data_assets: [],
    workflows: [],
    ai_models: [],
    business_entities: [],
  });
  const [summary, setSummary] = useState({
    data_assets: 0,
    workflows: 0,
    ai_models: 0,
    business_entities: 0,
  });
  const [selectedItem, setSelectedItem] = useState<MetadataItem | null>(null);
  const [classifications, setClassifications] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    // 切换标签或搜索时重置到第一页
    setCurrentPage(1);
  }, [activeTab, searchQuery, selectedClassification]);

  useEffect(() => {
    // 当页码、每页数量、标签、搜索或分类变化时，重新获取数据
    // 注意：fetchMetadata 函数内部会使用这些状态，所以不需要作为依赖
    fetchMetadata();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, pageSize, activeTab, searchQuery, selectedClassification]);

  const fetchMetadata = async () => {
    try {
      setLoading(true);

      if (activeTab === 'all') {
        // 获取汇总信息
        const response = await fetch('/api/metadata');
        if (response.ok) {
          const data = await response.json();
          const summaryData = data.summary || {};
          setSummary({
            data_assets: summaryData.data_assets || summaryData.dataAssets || 0,
            workflows: summaryData.workflows || 0,
            ai_models: summaryData.ai_models || summaryData.aiModels || 0,
            business_entities: summaryData.business_entities || summaryData.businessEntities || 0,
          });
          setMetadata({
            data_assets: data.recent?.data_assets || [],
            workflows: data.recent?.workflows || [],
            ai_models: data.recent?.ai_models || [],
            business_entities: data.recent?.business_entities || [],
          });
        }
      } else if (activeTab === 'data-assets') {
        // 获取当前页数据（分页）
        const skip = (currentPage - 1) * pageSize;
        const url = `/api/metadata?type=${activeTab}&skip=${skip}&limit=${pageSize}${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}${selectedClassification !== 'all' ? `&classification=${selectedClassification}` : ''}`;

        // 调试日志：记录请求URL和参数
        console.log('Fetching data assets with URL:', url);
        console.log('Request params:', { skip, limit: pageSize, currentPage, pageSize });

        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          const items = data.items || [];
          const hasMore = data.hasMore || false;

          // 调试日志
          console.log('Fetched data assets:', {
            itemsCount: items.length,
            totalFromData: data.total,
            hasMore,
            skip,
            limit: pageSize,
            url: url,
            responseData: data,
          });

          // 如果返回的数据少于预期，记录警告
          if (items.length < pageSize && items.length < data.total) {
            console.warn(
              `Warning: Expected ${pageSize} items but got ${items.length}. Total: ${data.total}`
            );
          }

          // 从响应头或响应数据中获取总数
          const totalCountHeader = response.headers.get('X-Total-Count');
          if (totalCountHeader) {
            setTotalCount(parseInt(totalCountHeader));
          } else if (data.total) {
            setTotalCount(data.total);
          } else if (hasMore) {
            // 如果还有更多数据，估算总数
            setTotalCount(skip + items.length + pageSize);
          } else {
            // 如果没有更多数据，使用实际数量
            setTotalCount(skip + items.length);
          }

          // 获取所有分类（用于筛选，只在第一页或分类列表为空时获取）
          if (classifications.length === 0 && currentPage === 1) {
            const allClassificationsUrl = `/api/metadata?type=${activeTab}&limit=1000`;
            const allResponse = await fetch(allClassificationsUrl);
            if (allResponse.ok) {
              const allData = await allResponse.json();
              const allItems = allData.items || [];
              // 使用工具函数提取分类，支持多种数据源（从type字段、asset_type、model_type等推断）
              const uniqueClassifications = extractUniqueClassifications(allItems, activeTab);
              // 如果没有从数据中提取到分类，使用预定义的分类列表作为备选
              if (uniqueClassifications.length === 0) {
                const { getAllClassifications } = await import('@/lib/metadata-classification');
                const predefinedClassifications = getAllClassifications(activeTab);
                setClassifications(['all', ...predefinedClassifications]);
              } else {
                setClassifications(['all', ...uniqueClassifications]);
              }
            }
          }

          // 直接设置当前标签页的数据，确保数据正确更新
          // 将 activeTab (如 'data-assets') 转换为 metadata 的键 (如 'data_assets')
          const metadataKey = activeTab.replace('-', '_') as keyof typeof metadata;
          setMetadata((prev) => {
            const newMetadata = { ...prev };
            newMetadata[metadataKey] = items;
            return newMetadata;
          });

          // 更新汇总
          setSummary((prev) => ({
            ...prev,
            data_assets: totalCount || items.length,
          }));
        }
      } else {
        // 获取其他类型的元数据（使用大limit触发分页获取，支持分类筛选）
        const classificationParam =
          selectedClassification !== 'all'
            ? `&classification=${encodeURIComponent(selectedClassification)}`
            : '';
        const response = await fetch(
          `/api/metadata?type=${activeTab}&limit=50000${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}${classificationParam}`
        );
        if (response.ok) {
          const data = await response.json();
          const items = data.items || [];

          // 获取所有分类（用于筛选）
          if (classifications.length === 0) {
            const uniqueClassifications = extractUniqueClassifications(items, activeTab);
            // 如果没有从数据中提取到分类，使用预定义的分类列表作为备选
            if (uniqueClassifications.length === 0) {
              const { getAllClassifications } = await import('@/lib/metadata-classification');
              const predefinedClassifications = getAllClassifications(activeTab);
              setClassifications(['all', ...predefinedClassifications]);
            } else {
              setClassifications(['all', ...uniqueClassifications]);
            }
          }

          // 将 activeTab (如 'ai-models') 转换为 metadata 的键 (如 'ai_models')
          const metadataKey = activeTab.replace('-', '_') as keyof typeof metadata;
          setMetadata((prev) => {
            const newMetadata = { ...prev };
            newMetadata[metadataKey] = items;
            return newMetadata;
          });

          // 更新总数
          setSummary((prev) => ({
            ...prev,
            [activeTab.replace('-', '_')]: items.length,
          }));
        }
      }
    } catch (error) {
      console.error('Failed to fetch metadata:', error);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'all' as MetadataType, name: '全部', icon: '📊' },
    { id: 'data-assets' as MetadataType, name: '数据资产', icon: '💾' },
    { id: 'workflows' as MetadataType, name: '工作流', icon: '🔄' },
    { id: 'ai-models' as MetadataType, name: 'AI模型', icon: '🤖' },
    { id: 'business-entities' as MetadataType, name: '业务实体', icon: '🏢' },
  ];

  const getTypeLabel = (type: MetadataType) => {
    const tab = tabs.find((t) => t.id === type);
    return tab?.name || type;
  };

  const getTypeIcon = (type: MetadataType) => {
    const tab = tabs.find((t) => t.id === type);
    return tab?.icon || '📋';
  };

  // 获取当前页的数据资产（已按分类筛选）
  const getCurrentPageAssets = () => {
    return metadata.data_assets || [];
  };

  const renderMetadataCard = (item: MetadataItem, type: MetadataType) => {
    return (
      <div
        key={`${type}-${item.id}`}
        className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
        onClick={() => setSelectedItem({ ...item, _type: type })}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {item.display_name || item.name}
            </h3>
            {item.name && item.name !== item.display_name && (
              <p className="text-sm text-gray-500 mb-2">{item.name}</p>
            )}
          </div>
          <span className="text-2xl">{getTypeIcon(type)}</span>
        </div>

        {item.description && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">{item.description}</p>
        )}

        <div className="flex flex-wrap gap-2 mb-2">
          {item.classification && (
            <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">
              {item.classification}
            </span>
          )}
          {item.asset_type && (
            <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-800">
              {item.asset_type}
            </span>
          )}
        </div>

        <div className="flex items-center justify-between text-xs text-gray-500">
          {item.status && (
            <span
              className={`px-2 py-1 rounded ${
                item.status === 'active'
                  ? 'bg-green-100 text-green-800'
                  : item.status === 'inactive'
                    ? 'bg-gray-100 text-gray-800'
                    : 'bg-yellow-100 text-yellow-800'
              }`}
            >
              {item.status}
            </span>
          )}
          {item.created_at && <span>{new Date(item.created_at).toLocaleDateString('zh-CN')}</span>}
        </div>
      </div>
    );
  };

  const renderMetadataDetail = () => {
    if (!selectedItem) return null;

    const item = selectedItem;
    const type = item._type as MetadataType;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {getTypeIcon(type)} {getTypeLabel(type)} - {item.display_name || item.name}
              </h2>
              {item.name && item.name !== item.display_name && (
                <p className="text-sm text-gray-500 mt-1">{item.name}</p>
              )}
            </div>
            <button
              onClick={() => setSelectedItem(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* 基本信息 */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">ID</label>
                  <p className="text-sm text-gray-900 mt-1">{item.id}</p>
                </div>
                {item.type && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">类型</label>
                    <p className="text-sm text-gray-900 mt-1">{item.type}</p>
                  </div>
                )}
                {item.classification && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">分类</label>
                    <p className="text-sm text-gray-900 mt-1">
                      {getClassificationDisplayName(item.classification, type)}
                    </p>
                  </div>
                )}
                {item.asset_type && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">资产类型</label>
                    <p className="text-sm text-gray-900 mt-1">{item.asset_type}</p>
                  </div>
                )}
                {item.status && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">状态</label>
                    <p className="text-sm text-gray-900 mt-1">{item.status}</p>
                  </div>
                )}
                {item.created_at && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">创建时间</label>
                    <p className="text-sm text-gray-900 mt-1">
                      {new Date(item.created_at).toLocaleString('zh-CN')}
                    </p>
                  </div>
                )}
                {item.updated_at && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">更新时间</label>
                    <p className="text-sm text-gray-900 mt-1">
                      {new Date(item.updated_at).toLocaleString('zh-CN')}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* 描述 */}
            {item.description && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">描述</h3>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{item.description}</p>
              </div>
            )}

            {/* 分类维度 */}
            {(item.classification_dimensions || item.standardized_tags) && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">分类维度</h3>
                <ClassificationDimensionEditor
                  type={type}
                  dimensions={item.classification_dimensions}
                  standardizedTags={item.standardized_tags}
                  primaryClassification={
                    item.classification || item.classification_dimensions?.primary
                  }
                  compact={false}
                />
              </div>
            )}

            {/* 标签 */}
            {item.tags && item.tags.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">标签（旧字段）</h3>
                <div className="flex flex-wrap gap-2">
                  {item.tags.map((tag, idx) => (
                    <span key={idx} className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-800">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 标准化标签 */}
            {item.standardized_tags && item.standardized_tags.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">标准化标签</h3>
                <div className="flex flex-wrap gap-2">
                  {item.standardized_tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800 border border-blue-200"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 元数据 */}
            {item.metadata && Object.keys(item.metadata).length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">元数据</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <pre className="text-xs text-gray-700 overflow-x-auto">
                    {JSON.stringify(item.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* 其他字段 */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">详细信息</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="text-xs text-gray-700 overflow-x-auto">
                  {JSON.stringify(
                    item,
                    (key, value) => {
                      // 排除已显示的字段
                      if (key === '_type' || key === 'metadata') return undefined;
                      return value;
                    },
                    2
                  )}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const currentPageAssets = getCurrentPageAssets();

  return (
    <AuthGuard requireAuth>
      <div className="space-y-6">
        {/* 页面标题 */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">元数据管理</h1>
          <p className="mt-2 text-sm text-gray-600">
            查看平台所有元数据信息（只读模式）
            {activeTab === 'data-assets' && totalCount > 0 && (
              <span className="ml-2 text-blue-600">
                共 {totalCount.toLocaleString()} 个数据资产
              </span>
            )}
          </p>
        </div>

        {/* 标签页 */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setSelectedClassification('all');
                }}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
                {activeTab === 'all' && tab.id !== 'all' && (
                  <span className="ml-2 text-xs text-gray-400">
                    ({summary[tab.id.replace('-', '_') as keyof typeof summary] || 0})
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* 搜索栏和分类筛选 */}
        {activeTab === 'data-assets' && (
          <div className="flex gap-4">
            <div className="relative flex-1">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="搜索数据资产..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="relative">
              <FunnelIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <select
                value={selectedClassification}
                onChange={(e) => setSelectedClassification(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white"
              >
                {classifications.map((cls) => (
                  <option key={cls} value={cls}>
                    {cls === 'all' ? '全部分类' : getClassificationDisplayName(cls, activeTab)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {activeTab !== 'data-assets' && activeTab !== 'all' && (
          <div className="flex gap-4">
            <div className="relative flex-1">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="搜索元数据..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            {/* 为其他类型也添加分类筛选 */}
            {classifications.length > 1 && (
              <div className="relative">
                <FunnelIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <select
                  value={selectedClassification}
                  onChange={(e) => setSelectedClassification(e.target.value)}
                  className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white"
                >
                  {classifications.map((cls) => (
                    <option key={cls} value={cls}>
                      {cls === 'all' ? '全部分类' : getClassificationDisplayName(cls, activeTab)}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}

        {/* 内容区域 */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span className="ml-3 text-gray-600">加载中...</span>
          </div>
        ) : activeTab === 'all' ? (
          /* 汇总视图 - 列表展示 */
          <div className="space-y-6">
            {tabs
              .filter((t) => t.id !== 'all')
              .map((tab) => {
                const typeKey = tab.id.replace('-', '_') as keyof typeof metadata;
                const items = metadata[typeKey] || [];
                const count = summary[typeKey] || 0;

                return (
                  <div
                    key={tab.id}
                    className="bg-white rounded-lg border border-gray-200 overflow-hidden"
                  >
                    <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                      <h2 className="text-xl font-semibold text-gray-900">
                        {tab.icon} {tab.name} ({count})
                      </h2>
                      <button
                        onClick={() => setActiveTab(tab.id)}
                        className="text-sm text-blue-600 hover:text-blue-700"
                      >
                        查看全部 →
                      </button>
                    </div>
                    {items.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                名称
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                显示名称
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                类型
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                状态
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                创建时间
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                操作
                              </th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {items.map((item) => (
                              <tr key={item.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <div className="text-sm font-medium text-gray-900">
                                    {item.name}
                                  </div>
                                </td>
                                <td className="px-6 py-4">
                                  <div className="text-sm text-gray-900">
                                    {item.display_name || '-'}
                                  </div>
                                  {item.description && (
                                    <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                                      {item.description}
                                    </div>
                                  )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  {item.type && (
                                    <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-800">
                                      {item.type}
                                    </span>
                                  )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  {item.status && (
                                    <span
                                      className={`px-2 py-1 text-xs rounded ${
                                        item.status === 'active'
                                          ? 'bg-green-100 text-green-800'
                                          : item.status === 'inactive'
                                            ? 'bg-gray-100 text-gray-800'
                                            : 'bg-yellow-100 text-yellow-800'
                                      }`}
                                    >
                                      {item.status}
                                    </span>
                                  )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {item.created_at
                                    ? new Date(item.created_at).toLocaleDateString('zh-CN')
                                    : '-'}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                  <button
                                    onClick={() => setSelectedItem({ ...item, _type: tab.id })}
                                    className="text-blue-600 hover:text-blue-900"
                                  >
                                    查看详情
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="p-8 text-center">
                        <p className="text-gray-500">暂无{tab.name}元数据</p>
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        ) : activeTab === 'data-assets' ? (
          /* 数据资产 - 使用MetadataViewEngine（支持多种视图） */
          <MetadataViewEngine
            items={metadata.data_assets || []}
            type={activeTab}
            onItemClick={(item) => setSelectedItem({ ...item, _type: activeTab })}
            loading={loading}
            emptyMessage={
              searchQuery || selectedClassification !== 'all'
                ? '没有找到匹配的数据资产'
                : '暂无数据资产元数据'
            }
          />
        ) : (
          /* 其他类型视图 - 使用MetadataViewEngine */
          <MetadataViewEngine
            items={(() => {
              const typeKey = activeTab.replace('-', '_') as keyof typeof metadata;
              return metadata[typeKey] || [];
            })()}
            type={activeTab}
            onItemClick={(item) => setSelectedItem({ ...item, _type: activeTab })}
            loading={loading}
            emptyMessage={
              searchQuery ? '没有找到匹配的元数据' : `暂无${getTypeLabel(activeTab)}元数据`
            }
          />
        )}

        {/* 详情弹窗 */}
        {renderMetadataDetail()}
      </div>
    </AuthGuard>
  );
}
