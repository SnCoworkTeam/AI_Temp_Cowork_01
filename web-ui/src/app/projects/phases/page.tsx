'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import { Plus, Filter, Calendar } from 'lucide-react';
import CreatePhaseModal from './create-modal';

interface Phase {
  id: string;
  project_id: string;
  project_name: string;
  name: string;
  description: string;
  sequence: number;
  start_date: string;
  end_date: string;
  progress_percent: number;
  created_at: string;
}

interface Project {
  id: string;
  name: string;
  project_code: string;
}

export default function PhasesPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams?.get('project_id');
  const [phases, setPhases] = useState<Phase[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(projectId || 'all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    fetchProjects();
    fetchPhases();
  }, [selectedProject]);

  const fetchProjects = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      const response = await fetch(`${apiUrl}/api/v1/projects`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(data.items || []);
      }
    } catch (error) {
      console.error('获取项目列表失败:', error);
    }
  };

  const fetchPhases = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      let url = `${apiUrl}/api/v1/project-phases`;
      if (selectedProject && selectedProject !== 'all') {
        url += `?project_id=${selectedProject}`;
      }
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setPhases(data.items || []);
      }
    } catch (error) {
      console.error('获取阶段列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">项目阶段管理</h1>
          <p className="text-sm text-gray-600 mt-1">管理项目各阶段进度</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 flex items-center gap-2 font-medium shadow-md hover:shadow-md hover:border-blue-300 transition-all duration-200"
        >
          <Plus className="h-4 w-4" />
          新建阶段
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div className="flex items-center gap-2 text-gray-700 font-semibold mb-4">
          <div className="p-1.5 bg-blue-100 rounded-lg">
            <Filter className="w-4 h-4 text-blue-600" />
          </div>
          <span>筛选条件</span>
        </div>
        <select
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="w-full md:w-auto px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">所有项目</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-500">
          加载中...
        </div>
      ) : phases.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">暂无项目阶段</p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            创建第一个阶段
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {phases
            .sort((a, b) => a.sequence - b.sequence)
            .map((phase) => (
              <div
                key={phase.id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all duration-200 transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded">
                        阶段 {phase.sequence}
                      </span>
                      <h3 className="text-lg font-semibold text-gray-900">{phase.name}</h3>
                    </div>
                    {phase.description && (
                      <p className="text-sm text-gray-600 mb-3">{phase.description}</p>
                    )}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-500">
                      <div>项目: {phase.project_name}</div>
                      {phase.start_date && (
                        <div>开始日期: {new Date(phase.start_date).toLocaleDateString()}</div>
                      )}
                      {phase.end_date && (
                        <div>结束日期: {new Date(phase.end_date).toLocaleDateString()}</div>
                      )}
                    </div>
                  </div>
                  <div className="ml-4 min-w-[150px]">
                    <div className="text-sm text-gray-600 mb-1">进度</div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-1">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${phase.progress_percent}%` }}
                      />
                    </div>
                    <div className="text-sm font-medium text-gray-900 text-right">
                      {phase.progress_percent.toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="text-sm text-gray-600">总阶段数</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{phases.length}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="text-sm text-gray-600">进行中</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {phases.filter((p) => p.progress_percent > 0 && p.progress_percent < 100).length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="text-sm text-gray-600">已完成</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {phases.filter((p) => p.progress_percent >= 100).length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="text-sm text-gray-600">平均进度</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {phases.length > 0
              ? (phases.reduce((sum, p) => sum + p.progress_percent, 0) / phases.length).toFixed(0)
              : 0}
            %
          </div>
        </div>
      </div>

      <CreatePhaseModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        projectId={selectedProject !== 'all' ? selectedProject : undefined}
        onSuccess={() => {
          fetchPhases();
          setShowCreateModal(false);
        }}
      />
    </div>
  );
}
