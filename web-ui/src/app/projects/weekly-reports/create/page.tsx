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
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [formData, setFormData] = useState({
    project_id: '',
    week_number: '',
    report_date: new Date().toISOString().split('T')[0],
    content_plan: '',
    content_achievement: '',
    issues_risks: '',
    next_week_plan: '',
  });

  // 计算指定月份的所有周
  const calculateWeeksInMonth = (year: number, month: number) => {
    const weeks: Array<{ weekNumber: number; weekLabel: string; startDate: Date; endDate: Date }> =
      [];
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0); // 月份的最后一天

    // 从月份第一天开始，按周分组（周一到周日）
    const currentDate = new Date(firstDay);
    let weekNumber = 1;

    while (currentDate <= lastDay) {
      // 找到本周的周一（如果当前日期不是周一，往前找到周一）
      const dayOfWeek = currentDate.getDay(); // 0=周日, 1=周一, ..., 6=周六
      const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1; // 距离周一的天数
      const weekStart = new Date(currentDate);
      weekStart.setDate(weekStart.getDate() - daysToMonday);

      // 如果周一开始日期在月份之前，则从月份第一天开始
      if (weekStart < firstDay) {
        weekStart.setTime(firstDay.getTime());
      }

      // 计算本周的周日
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekEnd.getDate() + 6);

      // 确保周结束日期不超过月份最后一天
      if (weekEnd > lastDay) {
        weekEnd.setTime(lastDay.getTime());
      }

      // 只添加包含月份日期的周
      if (weekStart <= lastDay && weekEnd >= firstDay) {
        const formatDate = (date: Date) => {
          const m = date.getMonth() + 1;
          const d = date.getDate();
          return `${m}月${d}日`;
        };
        const weekLabel = `第${weekNumber}周 (${formatDate(weekStart)} - ${formatDate(weekEnd)})`;

        weeks.push({
          weekNumber,
          weekLabel,
          startDate: new Date(weekStart),
          endDate: new Date(weekEnd),
        });
        weekNumber++;
      }

      // 移动到下一周的开始（下周一）
      currentDate.setDate(weekEnd.getDate() + 1);
    }

    return weeks;
  };

  // 获取当前日期所在的周数
  const getCurrentWeekNumber = (
    weeks: Array<{ weekNumber: number; startDate: Date; endDate: Date }>
  ) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (const week of weeks) {
      const start = new Date(week.startDate);
      start.setHours(0, 0, 0, 0);
      const end = new Date(week.endDate);
      end.setHours(23, 59, 59, 999);

      if (today >= start && today <= end) {
        return week.weekNumber;
      }
    }

    return null;
  };

  // 获取当前月份的周列表
  const getWeeksForMonth = () => {
    const [year, month] = selectedMonth.split('-').map(Number);
    return calculateWeeksInMonth(year, month);
  };

  // 当月份改变时，更新周数和报告日期
  useEffect(() => {
    const weeks = getWeeksForMonth();
    const currentWeek = getCurrentWeekNumber(weeks);

    if (currentWeek && weeks.length > 0) {
      const week = weeks.find((w) => w.weekNumber === currentWeek);
      if (week) {
        setFormData((prev) => ({
          ...prev,
          week_number: currentWeek.toString(),
          report_date: week.startDate.toISOString().split('T')[0],
        }));
      }
    } else if (weeks.length > 0) {
      // 如果没有找到当前周，默认选择第一周
      const firstWeek = weeks[0];
      setFormData((prev) => ({
        ...prev,
        week_number: firstWeek.weekNumber.toString(),
        report_date: firstWeek.startDate.toISOString().split('T')[0],
      }));
    } else {
      // 如果没有周，清空周数
      setFormData((prev) => ({
        ...prev,
        week_number: '',
      }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMonth]);

  useEffect(() => {
    fetchProjects();

    // 初始化当前周的周数
    const weeks = getWeeksForMonth();
    const currentWeek = getCurrentWeekNumber(weeks);
    if (currentWeek) {
      const week = weeks.find((w) => w.weekNumber === currentWeek);
      if (week) {
        setFormData((prev) => ({
          ...prev,
          week_number: currentWeek.toString(),
          report_date: week.startDate.toISOString().split('T')[0],
        }));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        router.push('/projects/weekly-reports');
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
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* 页面标题和操作栏 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            新建周报
          </h1>
          <p className="text-sm text-gray-600 mt-2 flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            创建项目周报
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
        <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-6 py-5 border-b-2 border-gray-200">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg shadow-md">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            周报信息
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
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
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
              <label className="block text-sm font-bold text-gray-700 mb-2">
                选择月份 <span className="text-red-500">*</span>
              </label>
              <input
                type="month"
                required
                value={selectedMonth}
                onChange={(e) => {
                  setSelectedMonth(e.target.value);
                }}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                选择周数 <span className="text-red-500">*</span>
              </label>
              <select
                required
                value={formData.week_number}
                onChange={(e) => {
                  const weekNumber = parseInt(e.target.value);
                  const weeks = getWeeksForMonth();
                  const selectedWeek = weeks.find((w) => w.weekNumber === weekNumber);
                  if (selectedWeek) {
                    setFormData({
                      ...formData,
                      week_number: e.target.value,
                      report_date: selectedWeek.startDate.toISOString().split('T')[0],
                    });
                  }
                }}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
              >
                <option value="">请选择周数</option>
                {getWeeksForMonth().map((week) => (
                  <option key={week.weekNumber} value={week.weekNumber}>
                    {week.weekLabel}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                报告日期 <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                required
                value={formData.report_date}
                onChange={(e) => setFormData({ ...formData, report_date: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">默认为所选周的开始日期，可手动调整</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">本周计划内容</label>
            <textarea
              value={formData.content_plan}
              onChange={(e) => setFormData({ ...formData, content_plan: e.target.value })}
              rows={5}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述本周计划完成的工作内容..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">本周完成成果</label>
            <textarea
              value={formData.content_achievement}
              onChange={(e) => setFormData({ ...formData, content_achievement: e.target.value })}
              rows={5}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述本周实际完成的工作成果..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">问题与风险</label>
            <textarea
              value={formData.issues_risks}
              onChange={(e) => setFormData({ ...formData, issues_risks: e.target.value })}
              rows={4}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述本周遇到的问题和风险..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">下周计划</label>
            <textarea
              value={formData.next_week_plan}
              onChange={(e) => setFormData({ ...formData, next_week_plan: e.target.value })}
              rows={5}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-gray-50 focus:bg-white text-sm resize-none"
              placeholder="描述下周计划完成的工作内容..."
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
            className="px-6 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:via-blue-800 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Save className="h-5 w-5" />
            {loading ? '创建中...' : '创建周报'}
          </button>
        </div>
      </form>
    </div>
  );
}
