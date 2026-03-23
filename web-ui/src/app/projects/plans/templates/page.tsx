'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Eye, Plus, ArrowLeft, Edit, Trash2, FileText, AlertCircle, X } from 'lucide-react';
import { getAccessToken } from '@/lib/auth';
import { apiGatewayClient } from '@/lib/api/client';
import type { ProjectTemplate } from '@/types/project';
import Link from 'next/link';
import ErrorMessage from '@/components/ErrorMessage';

export default function ProjectTemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchText, setSearchText] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<ProjectTemplate | null>(null);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    fetchTemplates();
  }, [filterActive]);

  const fetchTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      let url = '/api/v1/project-templates';
      const params = new URLSearchParams();
      if (filterActive !== null) {
        params.append('is_active', String(filterActive));
      }
      if (params.toString()) {
        url += '?' + params.toString();
      }
      const data = await apiGatewayClient.get<{ items: ProjectTemplate[] }>(url);
      setTemplates(data.items || []);
    } catch (error: any) {
      console.error('获取模板列表失败:', error);
      setError(error?.message || '获取模板列表失败');
    } finally {
      setLoading(false);
    }
  };

  const filteredTemplates = templates.filter((template) => {
    if (searchText) {
      return (
        template.name.toLowerCase().includes(searchText.toLowerCase()) ||
        template.template_code?.toLowerCase().includes(searchText.toLowerCase())
      );
    }
    return true;
  });

  const handlePreview = (template: ProjectTemplate) => {
    setPreviewTemplate(template);
    setPreviewVisible(true);
  };

  const handleDelete = async (templateId: string) => {
    setDeleteConfirm(templateId);
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;
    try {
      await apiGatewayClient.delete(`/api/v1/project-templates/${deleteConfirm}`);
      setDeleteConfirm(null);
      await fetchTemplates();
    } catch (error: any) {
      console.error('删除模板失败:', error);
      setError(error?.message || '删除失败');
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* 头部 - 美化 */}
      <div className="bg-gradient-to-r from-indigo-50 via-blue-50 to-purple-50 rounded-2xl shadow-xl border-2 border-indigo-200 p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-white/50 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-700" />
            </button>
            <div className="p-3 bg-indigo-500 rounded-xl shadow-lg">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">计划模板管理</h1>
              <p className="text-gray-600 mt-1">管理和查看项目计划模板</p>
            </div>
          </div>
          <button
            onClick={() => router.push('/projects/plans/templates/create')}
            className="px-6 py-3 bg-gradient-to-r from-indigo-600 via-blue-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:via-blue-700 hover:to-purple-700 transition-all duration-200 flex items-center gap-2 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Plus className="h-5 w-5" />
            创建模板
          </button>
        </div>
      </div>

      {error && (
        <ErrorMessage message={error} type="error" onClose={() => setError(null)} />
      )}

      {/* 搜索和筛选 - 美化 */}
      <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="搜索模板名称或编码"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all duration-200 bg-white"
            />
          </div>
          <select
            value={filterActive === null ? '' : String(filterActive)}
            onChange={(e) => setFilterActive(e.target.value === '' ? null : e.target.value === 'true')}
            className="px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all duration-200 bg-white min-w-[150px]"
          >
            <option value="">全部状态</option>
            <option value="true">启用</option>
            <option value="false">禁用</option>
          </select>
        </div>
      </div>

      {/* 模板列表 */}
      {loading ? (
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-16 text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          <p className="text-gray-500 mt-4">加载中...</p>
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-100 p-16 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 mb-4">
            <FileText className="h-10 w-10 text-gray-400" />
          </div>
          <p className="text-gray-600 font-semibold text-lg mb-2">暂无模板</p>
          <p className="text-sm text-gray-500 mb-6">开始创建您的第一个模板</p>
          <button
            onClick={() => router.push('/projects/plans/templates/create')}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Plus className="h-5 w-5" />
            创建第一个模板
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template) => (
            <div
              key={template.id}
              className="group relative bg-white rounded-2xl shadow-lg border-2 border-gray-200 p-6 hover:shadow-2xl hover:border-indigo-400 transition-all duration-300 overflow-hidden transform hover:scale-[1.02]"
            >
              {/* 顶部渐变装饰条 */}
              <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-indigo-500 via-blue-500 to-purple-500"></div>

              <div className="space-y-4 mt-2">
                <div className="flex items-start justify-between">
                  <h3 className="font-bold text-xl text-gray-900 group-hover:text-indigo-600 transition-colors">
                    {template.name}
                  </h3>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      template.is_active
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {template.is_active ? '启用' : '禁用'}
                  </span>
                </div>

                {template.template_code && (
                  <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium">
                    {template.template_code}
                  </span>
                )}

                {template.description && (
                  <p className="text-gray-600 text-sm line-clamp-2">{template.description}</p>
                )}

                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    使用次数: {template.usage_count || 0}
                  </span>
                  {template.category_name && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                      {template.category_name}
                    </span>
                  )}
                </div>

                {template.template_structure && template.template_structure.length > 0 && (
                  <div className="text-sm text-gray-500 flex items-center gap-1">
                    <FileText className="w-4 h-4" />
                    包含 {template.template_structure.length} 个阶段
                  </div>
                )}

                {/* 操作按钮 */}
                <div className="flex items-center gap-2 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => handlePreview(template)}
                    className="flex-1 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors flex items-center justify-center gap-2 font-medium"
                  >
                    <Eye className="w-4 h-4" />
                    预览
                  </button>
                  <button
                    onClick={() => router.push(`/projects/plans/templates/${template.id}/edit`)}
                    className="flex-1 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors flex items-center justify-center gap-2 font-medium"
                  >
                    <Edit className="w-4 h-4" />
                    编辑
                  </button>
                  <button
                    onClick={() => handleDelete(template.id)}
                    className="px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors flex items-center justify-center gap-2 font-medium"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 预览模态框 */}
      {previewVisible && previewTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="bg-gradient-to-r from-indigo-50 via-blue-50 to-purple-50 px-8 py-5 border-b-2 border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-md">
                  <Eye className="w-5 h-5 text-white" />
                </div>
                模板预览
              </h2>
              <button
                onClick={() => {
                  setPreviewVisible(false);
                  setPreviewTemplate(null);
                }}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-8 space-y-6">
              <div>
                <h3 className="font-bold text-2xl text-gray-900">{previewTemplate.name}</h3>
                {previewTemplate.template_code && (
                  <span className="inline-block mt-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium">
                    {previewTemplate.template_code}
                  </span>
                )}
              </div>
              {previewTemplate.description && (
                <p className="text-gray-600">{previewTemplate.description}</p>
              )}
              <div className="flex items-center gap-4 text-sm">
                <span className="flex items-center gap-1">
                  <Eye className="w-4 h-4" />
                  使用次数: {previewTemplate.usage_count || 0}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    previewTemplate.is_active
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  }`}
                >
                  {previewTemplate.is_active ? '启用' : '禁用'}
                </span>
              </div>
              {previewTemplate.template_structure && previewTemplate.template_structure.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-4 text-lg">模板结构:</h4>
                  <div className="space-y-3">
                    {previewTemplate.template_structure.map((phase, index) => (
                      <div key={index} className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                        <div className="font-medium text-gray-900">{phase.name}</div>
                        {phase.sequence !== undefined && (
                          <div className="text-sm text-gray-500 mt-1">顺序: {phase.sequence}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-8 py-6 border-t-2 border-gray-200 flex justify-end sticky bottom-0">
              <button
                onClick={() => {
                  setPreviewVisible(false);
                  setPreviewTemplate(null);
                }}
                className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 删除确认模态框 */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-red-100 rounded-xl">
                <AlertCircle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">确认删除</h3>
                <p className="text-sm text-gray-600 mt-1">确定要删除这个模板吗？此操作不可恢复。</p>
              </div>
            </div>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-6 py-2.5 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors font-medium"
              >
                取消
              </button>
              <button
                onClick={confirmDelete}
                className="px-6 py-2.5 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-xl hover:from-red-700 hover:to-red-800 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

