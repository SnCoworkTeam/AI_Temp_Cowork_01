'use client';

import { useEffect, useMemo, useState } from 'react';
import { getTools } from '@/lib/api/tools';

type ToolItem = {
  name: string;
  description: string;
  tool_type?: string;
  status?: string;
  metadata?: Record<string, any>;
};

export default function ToolsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [tools, setTools] = useState<ToolItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getTools();
        setTools(Array.isArray(res) ? res : []);
      } catch (e: any) {
        console.error('Failed to load tools', e);
        setError('加载工具列表失败');
        setTools([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filteredTools = useMemo(() => {
    if (!Array.isArray(tools)) return [];
    return tools.filter((tool) => {
      const term = searchTerm.toLowerCase();
      return (
        tool.name?.toLowerCase().includes(term) || tool.description?.toLowerCase().includes(term)
      );
    });
  }, [tools, searchTerm]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">MCP工具管理</h1>
          <p className="text-gray-600 mt-1">管理和配置MCP工具</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          + 注册工具
        </button>
      </div>

      {/* 搜索栏 */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <input
          type="text"
          placeholder="搜索工具..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* 工具列表 */}
      {loading ? (
        <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
          <p className="text-gray-500">加载中...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
          <p className="text-red-600 mb-2">{error}</p>
          <p className="text-gray-500">请稍后重试</p>
        </div>
      ) : filteredTools.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
          <p className="text-gray-500 mb-4">未找到匹配的工具</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredTools.map((tool) => {
            const status = (tool.status || 'active').toLowerCase();
            const category =
              tool.metadata?.category || tool.metadata?.service || tool.tool_type || 'general';
            return (
              <div
                key={tool.name}
                className="bg-white rounded-lg shadow border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">{tool.name}</h3>
                    <p className="text-sm text-gray-600 mb-2">{tool.description}</p>
                    <span className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                      {category}
                    </span>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded ${
                      status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {status === 'active' ? '活跃' : '非活跃'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
