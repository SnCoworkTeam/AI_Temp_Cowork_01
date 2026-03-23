'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Save, X, Calendar } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  project_code: string;
}

export default function CreateWeeklyReportPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [formData, setFormData] = useState({
    project_id: '',
    week_number: '',
    report_date: new Date().toISOString().split('T')[0],
    content_plan: '',
    content_achievement: '',
    issues_risks: '',
    next_week_plan: '',
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

      const payload = {
        ...formData,
        week_number: formData.week_number ? parseInt(formData.week_number) : null,
      };

      const response = await fetch(`${apiUrl}/api/v1/weekly-reports`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        router.push('/admin/projects/weekly-reports');
      } else {
        const error = await response.json();
        alert(error.detail || '创建周报失败');
      }
    } catch (error) {
      console.error('创建周报失败:', error);
      alert('创建周报失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">新建周报</h1>
          <p className="text-gray-600 mt-1">创建项目周报</p>
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
                  {project.name} ({project.project_code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              报告日期 <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              required
              value={formData.report_date}
              onChange={(e) => setFormData({ ...formData, report_date: e.target.value })}
              className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">周数</label>
            <input
              type="number"
              min="1"
              max="53"
              value={formData.week_number}
              onChange={(e) => setFormData({ ...formData, week_number: e.target.value })}
              className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="可选，如：1-53"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">本周计划内容</label>
          <textarea
            value={formData.content_plan}
            onChange={(e) => setFormData({ ...formData, content_plan: e.target.value })}
            rows={4}
            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="描述本周计划完成的工作内容..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">本周完成成果</label>
          <textarea
            value={formData.content_achievement}
            onChange={(e) => setFormData({ ...formData, content_achievement: e.target.value })}
            rows={4}
            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="描述本周实际完成的工作成果..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">问题与风险</label>
          <textarea
            value={formData.issues_risks}
            onChange={(e) => setFormData({ ...formData, issues_risks: e.target.value })}
            rows={3}
            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="描述本周遇到的问题和风险..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">下周计划</label>
          <textarea
            value={formData.next_week_plan}
            onChange={(e) => setFormData({ ...formData, next_week_plan: e.target.value })}
            rows={4}
            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="描述下周计划完成的工作内容..."
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
            {loading ? '创建中...' : '创建周报'}
          </button>
        </div>
      </form>
    </div>
  );
}
