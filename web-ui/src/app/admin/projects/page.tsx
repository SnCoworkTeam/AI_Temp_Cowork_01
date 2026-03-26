'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Plus, Upload, Search } from 'lucide-react';
import { getAccessToken } from '@/lib/auth';
import Link from 'next/link';
import ProjectPhaseProgress from '@/components/ProjectPhaseProgress';

interface BasicDataCategory {
  id: string;
  category_type: string;
  code: string;
  name: string;
}

interface Project {
  id: string;
  project_code: string;
  name: string;
  status: string;
  progress_percent: number;
  created_at: string;
  requires_weekly_report?: boolean;
  basic_data_categories?: BasicDataCategory[];
}

export default function AdminProjectsPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      // 使用环境变量或默认服务器地址
      const apiUrl =
        typeof window !== 'undefined'
          ? process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080'
          : 'http://43.143.139.197:8080';
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
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      planning: 'bg-gray-500',
      active: 'bg-blue-500',
      delayed: 'bg-yellow-500',
      completed: 'bg-green-500',
      cancelled: 'bg-red-500',
    };
    return colors[status] || 'bg-gray-500';
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      planning: '规划中',
      active: '进行中',
      delayed: '已延迟',
      completed: '已完成',
      cancelled: '已取消',
    };
    return texts[status] || status;
  };

  const filteredProjects = projects.filter(
    (project) =>
      project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.project_code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* 页面标题和操作栏 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">项目列表</h1>
          <p className="text-sm text-gray-600 mt-1">管理和查看所有项目</p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/admin/projects/import"
            className="px-4 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 flex items-center gap-2 font-medium shadow-sm"
          >
            <Upload className="h-4 w-4" />
            导入Excel
          </Link>
          <Link
            href="/admin/projects/create"
            className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 flex items-center gap-2 font-medium shadow-md hover:shadow-lg"
          >
            <Plus className="h-4 w-4" />
            新建项目
          </Link>
        </div>
      </div>

      {/* 搜索栏 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <input
            type="text"
            placeholder="搜索项目名称或编码..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-sm"
          />
        </div>
      </div>

      {/* 项目列表 */}
      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-16 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-500 mt-4">加载中...</p>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-16 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
            <Search className="h-8 w-8 text-gray-400" />
          </div>
          <p className="text-gray-600 font-medium mb-2">暂无项目</p>
          <p className="text-sm text-gray-500 mb-6">开始创建您的第一个项目</p>
          <Link
            href="/admin/projects/import"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
          >
            <Upload className="h-4 w-4" />
            导入Excel项目
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
            <Link key={project.id} href={`/admin/projects/${project.id}`}>
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md hover:border-blue-300 transition-all duration-200 cursor-pointer overflow-hidden group">
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate group-hover:text-blue-600 transition-colors">
                        {project.name}
                      </h3>
                      <p className="text-sm text-gray-500 font-mono">{project.project_code}</p>
                    </div>
                    <span
                      className={`px-2.5 py-1 text-xs font-semibold rounded-full ${getStatusColor(project.status)} text-white shadow-sm flex-shrink-0 ml-2`}
                    >
                      {getStatusText(project.status)}
                    </span>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-3">
                        <span className="text-gray-600 font-medium">项目阶段</span>
                      </div>
                      <ProjectPhaseProgress
                        currentPhase={(() => {
                          // 从项目分类中获取项目阶段
                          if (
                            project.basic_data_categories &&
                            project.basic_data_categories.length > 0
                          ) {
                            const phaseCategory = project.basic_data_categories.find(
                              (cat) => cat.category_type === 'project_phase'
                            );
                            if (phaseCategory) {
                              // 优先使用ID，如果没有ID则使用code或name
                              return phaseCategory.id || phaseCategory.code || phaseCategory.name;
                            }
                          }
                          return undefined;
                        })()}
                        className="py-2"
                      />
                    </div>
                    <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                      <p className="text-xs text-gray-500">
                        {new Date(project.created_at).toLocaleDateString('zh-CN')}
                      </p>
                      {project.requires_weekly_report && (
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                          📊 需周报
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
