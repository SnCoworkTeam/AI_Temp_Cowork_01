'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Save, X, Calendar } from 'lucide-react';

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
        router.push('/projects/monthly-reports');
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
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* 页面标题和操作栏 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            新建月报
          </h1>
          <p className="text-sm text-gray-600 mt-2 flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            创建项目月报
          </p>
        </div>
        <button
          onClick={() => router.back()}
          className="px-5 py-2.5 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 flex items-center gap-2 font-medium shadow-sm hover:shadow-md"
        >
          <X className="h-5 w-5" />
          取消
        </button>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-lg border-2 border-gray-200 overflow-hidden"
      >
        <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-rose-50 px-6 py-5 border-b-2 border-gray-200">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg shadow-md">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            月报信息
          </h2>
        </div>
        <div className="p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                项目 <span className="text-red-500">*</span>
              </label>
              <select
                required
                value={formData.project_id}
                onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
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
              <label className="block text-sm font-bold text-gray-700 mb-2">
                报告月份 <span className="text-red-500">*</span>
              </label>
              <input
                type="month"
                required
                value={formData.report_month}
                onChange={(e) => setFormData({ ...formData, report_month: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">月度总结</label>
            <textarea
              value={formData.summary}
              onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
              rows={4}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="本月项目进展总结..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">主要成果</label>
            <textarea
              value={formData.achievements}
              onChange={(e) => setFormData({ ...formData, achievements: e.target.value })}
              rows={5}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述本月完成的主要工作成果..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">挑战与问题</label>
            <textarea
              value={formData.challenges}
              onChange={(e) => setFormData({ ...formData, challenges: e.target.value })}
              rows={4}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述本月遇到的挑战和问题..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">下月计划</label>
            <textarea
              value={formData.next_month_plan}
              onChange={(e) => setFormData({ ...formData, next_month_plan: e.target.value })}
              rows={5}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述下月计划完成的工作内容..."
            />
          </div>
        </div>
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-8 py-6 border-t-2 border-gray-200 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium shadow-sm hover:shadow-md"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 text-white rounded-xl hover:from-purple-700 hover:via-pink-700 hover:to-rose-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Save className="h-5 w-5" />
            {loading ? '创建中...' : '创建月报'}
          </button>
        </div>
      </form>
    </div>
  );
}
