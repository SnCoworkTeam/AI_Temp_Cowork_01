'use client';

import { useState, useEffect } from 'react';
import { getAccessToken } from '@/lib/auth';
import { X } from 'lucide-react';

interface CreatePhaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId?: string;
  onSuccess: () => void;
}

interface ProjectPhaseCategory {
  id: string;
  name: string;
  code: string;
}

export default function CreatePhaseModal({
  isOpen,
  onClose,
  projectId,
  onSuccess,
}: CreatePhaseModalProps) {
  const [loading, setLoading] = useState(false);
  const [phaseCategories, setPhaseCategories] = useState<ProjectPhaseCategory[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [formData, setFormData] = useState({
    project_id: projectId || '',
    category_id: '', // 改为使用category_id
    description: '',
    start_date: '',
    end_date: '',
  });

  // 加载项目阶段基础数据
  useEffect(() => {
    if (isOpen) {
      loadPhaseCategories();
    }
  }, [isOpen]);

  const loadPhaseCategories = async () => {
    try {
      setLoadingCategories(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(
        `${apiUrl}/api/v1/basic-data/categories?category_type=project_phase&limit=1000`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setPhaseCategories(data.items || []);
      }
    } catch (error) {
      console.error('加载项目阶段分类失败:', error);
    } finally {
      setLoadingCategories(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.project_id || !formData.category_id) {
      alert('请选择项目和阶段分类');
      return;
    }

    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/project-phases`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: formData.project_id,
          category_id: formData.category_id, // 直接使用category_id
          description: formData.description || null,
          start_date: formData.start_date || null,
          end_date: formData.end_date || null,
        }),
      });

      if (response.ok) {
        onSuccess();
        onClose();
        // 重置表单
        setFormData({
          project_id: projectId || '',
          category_id: '',
          description: '',
          start_date: '',
          end_date: '',
        });
      } else {
        const error = await response.json();
        alert(error.detail || '创建阶段失败');
      }
    } catch (error) {
      console.error('创建阶段失败:', error);
      alert('创建阶段失败');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">新建项目阶段</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                项目ID <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.project_id}
                onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="项目ID"
                disabled={!!projectId}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                项目阶段 <span className="text-red-500">*</span>
              </label>
              {loadingCategories ? (
                <p className="text-sm text-gray-500">加载阶段选项...</p>
              ) : phaseCategories.length > 0 ? (
                <select
                  required
                  value={formData.category_id}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">请选择项目阶段</option>
                  {phaseCategories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="text-sm text-red-500">
                  未找到可用的项目阶段分类，请先在基础数据中配置
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">阶段描述</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="阶段描述"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">开始日期</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">结束日期</label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? '创建中...' : '创建阶段'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
