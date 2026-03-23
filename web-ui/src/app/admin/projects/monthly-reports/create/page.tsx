'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Save, X } from 'lucide-react';

interface Project {
  id: string;
  name: string;
}

export default function CreateMonthlyReportPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [formData, setFormData] = useState({
    project_id: '',
    report_month: new Date().toISOString().slice(0, 7), // YYYY-MM格式
    summary: '',
    achievements: '',
    challenges: '',
    next_month_plan: '',
  });

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProjects(data.items || []);
      }
    } catch (error) {
      console.error('获取项目列表失败:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/monthly-reports`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        router.push('/admin/projects/monthly-reports');
      } else {
        const error = await response.json();
        alert(error.detail || '创建月报失败');
      }
    } catch (error) {
      console.error('创建月报失败:', error);
      alert('创建月报失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">新建月报</h1>
          <p className="text-gray-600 mt-1">创建项目月报</p>
        </div>
        <button
          onClick={() => router.back()}
          className="px-4 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium shadow-sm flex items-center gap-2"
        >
          <X className="h-4 w-4" />
          取消
        </button>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              项目 <span className="text-red-500">*</span>
            </label>
            <select
              required
              value={formData.project_id}
              onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
              className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">请选择项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              报告月份 <span className="text-red-500">*</span>
            </label>
            <input
              type="month"
              required
              value={formData.report_month}
              onChange={(e) => setFormData({ ...formData, report_month: e.target.value })}
              className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">月度总结</label>
          <textarea
            value={formData.summary}
            onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
            rows={3}
            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="本月项目进展总结..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">主要成果</label>
          <textarea
            value={formData.achievements}
            onChange={(e) => setFormData({ ...formData, achievements: e.target.value })}
            rows={4}
            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="描述本月完成的主要工作成果..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">挑战与问题</label>
          <textarea
            value={formData.challenges}
            onChange={(e) => setFormData({ ...formData, challenges: e.target.value })}
            rows={3}
            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="描述本月遇到的挑战和问题..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">下月计划</label>
          <textarea
            value={formData.next_month_plan}
            onChange={(e) => setFormData({ ...formData, next_month_plan: e.target.value })}
            rows={4}
            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="描述下月计划完成的工作内容..."
          />
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium shadow-sm transition-colors"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-medium shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {loading ? '创建中...' : '创建月报'}
          </button>
        </div>
      </form>
    </div>
  );
}
