'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface PromptTemplate {
  id: number;
  name: string;
  category: string;
  description?: string;
  system_prompt?: string;
  is_active: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

export default function PromptsPage() {
  const router = useRouter();
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<boolean | null>(null);
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    fetchPrompts();
    fetchCategories();
  }, [categoryFilter, activeFilter]);

  const fetchPrompts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (categoryFilter) params.append('category', categoryFilter);
      if (activeFilter !== null) params.append('is_active', activeFilter.toString());

      // 添加超时控制
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时

      try {
        const response = await fetch(`/api/v1/prompts?${params}`, {
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (response.ok) {
          const data = await response.json();
          setPrompts(data || []);
        } else if (response.status === 404) {
          // 如果表不存在，返回空数组
          setPrompts([]);
        } else {
          console.error('Failed to fetch prompts:', response.status, response.statusText);
          setPrompts([]);
        }
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          console.error('Request timeout');
        } else {
          console.error('Failed to fetch prompts:', fetchError);
        }
        setPrompts([]);
      }
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
      setPrompts([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      // 添加超时控制
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5秒超时

      try {
        const response = await fetch(`/api/v1/prompts/categories/list`, {
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (response.ok) {
          const data = await response.json();
          setCategories(data || []);
        } else if (response.status === 404) {
          // 如果表不存在，返回空数组
          setCategories([]);
        } else {
          console.error('Failed to fetch categories:', response.status, response.statusText);
          setCategories([]);
        }
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        if (fetchError.name !== 'AbortError') {
          console.error('Failed to fetch categories:', fetchError);
        }
        setCategories([]);
      }
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      setCategories([]);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个提示词模板吗？')) return;

    try {
      const response = await fetch(`/api/v1/prompts/${id}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        fetchPrompts();
      }
    } catch (error) {
      console.error('Failed to delete prompt:', error);
    }
  };

  // 按分类分组
  const groupedPrompts = prompts.reduce(
    (acc, prompt) => {
      const category = prompt.category || '未分类';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(prompt);
      return acc;
    },
    {} as Record<string, PromptTemplate[]>
  );

  // 分类显示名称映射
  const categoryLabels: Record<string, string> = {
    general: '通用',
    workflow: '工作流',
    knowledge: '知识库',
    document: '文档处理',
    code: '代码',
    business: '业务分析',
    analysis: '数据分析',
    enterprise_architecture: '企业架构',
    project_management: '项目管理',
    operations: '运维',
    integration: '集成',
    testing: '测试',
    security: '安全',
  };

  // 分类颜色映射
  const categoryColors: Record<string, string> = {
    general: 'bg-blue-100 text-blue-800',
    workflow: 'bg-purple-100 text-purple-800',
    knowledge: 'bg-green-100 text-green-800',
    document: 'bg-yellow-100 text-yellow-800',
    code: 'bg-indigo-100 text-indigo-800',
    business: 'bg-pink-100 text-pink-800',
    analysis: 'bg-orange-100 text-orange-800',
    enterprise_architecture: 'bg-teal-100 text-teal-800',
    project_management: 'bg-cyan-100 text-cyan-800',
    operations: 'bg-red-100 text-red-800',
    integration: 'bg-violet-100 text-violet-800',
    testing: 'bg-emerald-100 text-emerald-800',
    security: 'bg-rose-100 text-rose-800',
  };

  // 过滤提示词
  const filteredPrompts = prompts.filter(
    (prompt) =>
      (prompt.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        prompt.description?.toLowerCase().includes(searchTerm.toLowerCase())) &&
      (!categoryFilter || prompt.category === categoryFilter) &&
      (activeFilter === null || prompt.is_active === activeFilter)
  );

  // 过滤后的分组
  const filteredGroupedPrompts = filteredPrompts.reduce(
    (acc, prompt) => {
      const category = prompt.category || '未分类';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(prompt);
      return acc;
    },
    {} as Record<string, PromptTemplate[]>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">提示词管理</h1>
          <p className="text-gray-600 mt-1">管理和配置AI提示词模板</p>
        </div>
        <Link
          href="/admin/prompts/create"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + 创建提示词
        </Link>
      </div>

      {/* 分类统计卡片 */}
      {categories.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {categories.map((category) => {
            const count = prompts.filter((p) => p.category === category).length;
            return (
              <div
                key={category}
                className={`bg-white rounded-lg shadow border border-gray-200 p-4 cursor-pointer transition-all hover:shadow-md ${
                  categoryFilter === category ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => setCategoryFilter(categoryFilter === category ? '' : category)}
              >
                <div
                  className={`inline-block px-2 py-1 rounded text-xs font-medium mb-2 ${categoryColors[category] || 'bg-gray-100 text-gray-800'}`}
                >
                  {categoryLabels[category] || category}
                </div>
                <div className="text-2xl font-bold text-gray-900">{count}</div>
                <div className="text-xs text-gray-500">个模板</div>
              </div>
            );
          })}
          <div
            className={`bg-white rounded-lg shadow border border-gray-200 p-4 cursor-pointer transition-all hover:shadow-md ${
              categoryFilter === '' ? 'ring-2 ring-blue-500' : ''
            }`}
            onClick={() => setCategoryFilter('')}
          >
            <div className="inline-block px-2 py-1 rounded text-xs font-medium mb-2 bg-gray-100 text-gray-800">
              全部
            </div>
            <div className="text-2xl font-bold text-gray-900">{prompts.length}</div>
            <div className="text-xs text-gray-500">个模板</div>
          </div>
        </div>
      )}

      {/* 搜索和筛选 */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200 space-y-4">
        <input
          type="text"
          placeholder="搜索提示词..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />

        <div className="flex gap-4">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">所有分类</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {categoryLabels[cat] || cat}
              </option>
            ))}
          </select>

          <select
            value={activeFilter === null ? '' : activeFilter.toString()}
            onChange={(e) =>
              setActiveFilter(e.target.value === '' ? null : e.target.value === 'true')
            }
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">全部状态</option>
            <option value="true">激活</option>
            <option value="false">未激活</option>
          </select>
        </div>
      </div>

      {/* 提示词列表 - 按分类分组展示 */}
      {loading ? (
        <div className="text-center py-8">加载中...</div>
      ) : filteredPrompts.length === 0 ? (
        <div className="text-center py-8 text-gray-500">没有找到提示词模板</div>
      ) : (
        <div className="space-y-6">
          {Object.entries(filteredGroupedPrompts).map(([category, categoryPrompts]) => (
            <div
              key={category}
              className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden"
            >
              <div
                className={`px-6 py-3 border-b ${categoryColors[category] || 'bg-gray-100 text-gray-800'}`}
              >
                <h3 className="text-sm font-semibold">
                  {categoryLabels[category] || category} ({categoryPrompts.length})
                </h3>
              </div>
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      名称
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      描述
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      版本
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      状态
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      更新时间
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {categoryPrompts.map((prompt) => (
                    <tr key={prompt.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{prompt.name}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {prompt.description || '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">v{prompt.version}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${
                            prompt.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {prompt.is_active ? '激活' : '未激活'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(prompt.updated_at).toLocaleString('zh-CN')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                        <Link
                          href={`/admin/prompts/${prompt.id}`}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          编辑
                        </Link>
                        <Link
                          href={`/admin/prompts/${prompt.id}/test`}
                          className="text-green-600 hover:text-green-900"
                        >
                          测试
                        </Link>
                        <button
                          onClick={() => handleDelete(prompt.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
