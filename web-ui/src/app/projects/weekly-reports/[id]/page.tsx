'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import {
  ArrowLeft,
  Calendar,
  TrendingUp,
  AlertTriangle,
  FileText,
  Edit,
  Clock,
  User,
} from 'lucide-react';
import Link from 'next/link';

interface WeeklyReport {
  id: string;
  project_id: string;
  project_name: string;
  week_start_date: string;
  week_end_date: string;
  report_date: string;
  week_number?: number;
  content_plan: string;
  content_achievement: string;
  issues_risks: string;
  next_week_plan: string;
  progress_percent?: number;
  created_at: string;
  updated_at: string;
}

export default function WeeklyReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params?.id as string;

  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (reportId) {
      fetchReport();
    }
  }, [reportId]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/weekly-reports/${reportId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setReport(data);
      } else if (response.status === 404) {
        setError('周报不存在');
      } else {
        setError('加载周报失败');
      }
    } catch (error) {
      console.error('获取周报详情失败:', error);
      setError('加载周报失败');
    } finally {
      setLoading(false);
    }
  };

  const getWeekLabel = (startDate: string, endDate: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    return `${start.getMonth() + 1}月${start.getDate()}日 - ${end.getMonth() + 1}月${end.getDate()}日`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
          <p className="font-semibold mb-2">{error || '周报不存在'}</p>
          <Link href="/projects/weekly-reports" className="text-blue-600 hover:underline">
            返回周报列表
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* 返回按钮和操作按钮 */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>返回</span>
        </button>
        <div className="flex gap-3">
          <Link
            href={`/projects/weekly-reports?edit=${report.id}`}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Edit className="w-4 h-4" />
            <span>编辑</span>
          </Link>
        </div>
      </div>

      {/* 周报头部信息卡片 */}
      <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl shadow-lg border-2 border-blue-200 overflow-hidden">
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl shadow-lg">
                <Calendar className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  {report.project_name} - 周报
                </h1>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-4 h-4" />
                    {getWeekLabel(report.week_start_date, report.week_end_date)}
                  </span>
                  {report.week_number && (
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">
                      第 {report.week_number} 周
                    </span>
                  )}
                </div>
              </div>
            </div>
            {report.progress_percent !== undefined && (
              <div className="flex items-center gap-3 px-4 py-2 bg-white rounded-xl shadow-md border border-blue-200">
                <TrendingUp className="w-5 h-5 text-green-600" />
                <div>
                  <p className="text-xs text-gray-600">项目进度</p>
                  <p className="text-2xl font-bold text-green-600">
                    {report.progress_percent.toFixed(0)}%
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* 进度条 */}
          {report.progress_percent !== undefined && (
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 to-indigo-600 h-3 rounded-full transition-all duration-500 shadow-sm"
                style={{ width: `${report.progress_percent}%` }}
              />
            </div>
          )}
        </div>
      </div>

      {/* 周报内容区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 本周计划内容 */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <div className="p-1.5 bg-blue-100 rounded-lg">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              本周计划内容
            </h2>
          </div>
          <div className="p-6">
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                {report.content_plan || '暂无内容'}
              </p>
            </div>
          </div>
        </div>

        {/* 本周完成成果 */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <div className="p-1.5 bg-green-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-green-600" />
              </div>
              本周完成成果
            </h2>
          </div>
          <div className="p-6">
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                {report.content_achievement || '暂无内容'}
              </p>
            </div>
          </div>
        </div>

        {/* 问题与风险 */}
        {report.issues_risks && (
          <div className="bg-white rounded-xl shadow-md border border-orange-200 overflow-hidden">
            <div className="bg-gradient-to-r from-orange-50 to-red-50 px-6 py-4 border-b border-orange-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <div className="p-1.5 bg-orange-100 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-orange-600" />
                </div>
                问题与风险
              </h2>
            </div>
            <div className="p-6">
              <div className="prose max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {report.issues_risks}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 下周计划 */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <div className="p-1.5 bg-purple-100 rounded-lg">
                <Calendar className="w-5 h-5 text-purple-600" />
              </div>
              下周计划
            </h2>
          </div>
          <div className="p-6">
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                {report.next_week_plan || '暂无内容'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 时间信息卡片 */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Clock className="w-4 h-4" />
              <span>创建时间: {new Date(report.created_at).toLocaleString('zh-CN')}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Clock className="w-4 h-4" />
              <span>更新时间: {new Date(report.updated_at).toLocaleString('zh-CN')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
