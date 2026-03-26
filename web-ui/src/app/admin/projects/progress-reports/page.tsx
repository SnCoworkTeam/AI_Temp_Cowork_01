'use client';

import { useState, useEffect, useMemo } from 'react';
import { getAccessToken } from '@/lib/auth';
import { Download, Filter, Calendar, TrendingUp } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  project_code: string;
  status: string;
  progress_percent: number;
}

interface WeeklyReport {
  id: string;
  project_id: string;
  project_name: string;
  report_date: string;
  week_number?: number;
  content_achievement: string;
  content_plan: string;
  issues_risks: string;
  next_week_plan: string;
  week_start_date?: string;
  week_end_date?: string;
}

interface MonthlyReport {
  id: string;
  project_id: string;
  project_name: string;
  report_month: string;
  achievements: string;
  challenges: string;
  next_month_plan: string;
}

// 里程碑类型
interface Milestone {
  id: string;
  project_id: string;
  name: string;
  category_name?: string; // 基础数据分类名称
  target_date: string;
  status: string;
  actual_date?: string;
}

// 月份和周的数据结构
interface MonthWeekData {
  month: string;
  monthLabel: string;
  weeks: WeekData[];
}

interface WeekData {
  weekLabel: string;
  dateRange: string;
  reports: WeeklyReport[];
}

export default function ProgressReportsPage() {
  const [reportType, setReportType] = useState<'weekly' | 'monthly'>('weekly');
  // 周报模式：自动使用当前月份
  const currentMonth = new Date().toISOString().slice(0, 7);
  const [selectedMonth, setSelectedMonth] = useState(currentMonth);
  // 月报模式：自动使用当前年份
  const currentYear = new Date().getFullYear().toString();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [projects, setProjects] = useState<Project[]>([]);
  const [weeklyReports, setWeeklyReports] = useState<WeeklyReport[]>([]);
  const [monthlyReports, setMonthlyReports] = useState<MonthlyReport[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState('all');

  // 当切换页签时，自动设置为当前月份/年份
  useEffect(() => {
    if (reportType === 'weekly') {
      setSelectedMonth(currentMonth);
    } else {
      setSelectedYear(currentYear);
    }
  }, [reportType]);

  useEffect(() => {
    fetchProjects();
    fetchMilestones();
    if (reportType === 'weekly') {
      fetchWeeklyReports();
    } else {
      fetchMonthlyReports();
    }
  }, [reportType, selectedMonth, selectedYear, selectedProject]);

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

  const fetchMilestones = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/milestones`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMilestones(data.items || []);
      }
    } catch (error) {
      console.error('获取里程碑列表失败:', error);
    }
  };

  const fetchWeeklyReports = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      let url = `${apiUrl}/api/v1/weekly-reports`;
      const params = [];
      if (selectedProject && selectedProject !== 'all') {
        params.push(`project_id=${selectedProject}`);
      }
      if (selectedMonth) {
        params.push(`month=${selectedMonth}`);
      }
      if (params.length > 0) {
        url += '?' + params.join('&');
      }

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setWeeklyReports(data.items || []);
      }
    } catch (error) {
      console.error('获取周报列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMonthlyReports = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      let url = `${apiUrl}/api/v1/monthly-reports`;
      const params = [];
      if (selectedProject && selectedProject !== 'all') {
        params.push(`project_id=${selectedProject}`);
      }
      if (selectedYear) {
        params.push(`year=${selectedYear}`);
      }
      if (params.length > 0) {
        url += '?' + params.join('&');
      }

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMonthlyReports(data.items || []);
      }
    } catch (error) {
      console.error('获取月报列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 日期格式化函数（需要在 useMemo 之前定义）
  const formatDate = (date: Date | string) => {
    const d = typeof date === 'string' ? new Date(date) : date;
    const month = d.getMonth() + 1;
    const day = d.getDate();
    return `${month}/${day}`;
  };

  // 计算月份的所有周（自动计算，从第一周到最后一周，按日期顺序连续显示）
  const calculateWeeksInMonth = (year: number, month: number): WeekData[] => {
    const weeks: WeekData[] = [];
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
        const weekLabel = `第${weekNumber}周`;
        const dateRange = `${formatDate(weekStart)}-${formatDate(weekEnd)}`;

        // 查找该周是否有周报
        const weekReports = weeklyReports.filter((report) => {
          const reportDate = new Date(report.report_date);
          return reportDate >= weekStart && reportDate <= weekEnd;
        });

        weeks.push({ weekLabel, dateRange, reports: weekReports });
        weekNumber++;
      }

      // 移动到下一周的开始（下周一）
      currentDate.setDate(weekEnd.getDate() + 1);
    }

    return weeks;
  };

  // 组织周报数据：自动计算每个月的周数
  const organizedWeeklyData = useMemo(() => {
    if (!selectedMonth) {
      return [];
    }

    const [year, month] = selectedMonth.split('-').map(Number);
    const monthLabel = `${year}年${month}月`;

    // 自动计算该月的所有周
    const weeks = calculateWeeksInMonth(year, month);

    return [{ month: selectedMonth, monthLabel, weeks }];
  }, [weeklyReports, selectedMonth]);

  // 组织月报数据：按年份和月份分组（只显示当前年份）
  const organizedMonthlyData = useMemo(() => {
    const yearMap = new Map<string, Map<string, MonthlyReport[]>>();
    const currentYearNum = parseInt(selectedYear);

    // 只处理当前年份的数据
    monthlyReports.forEach((report) => {
      // 从report_month中提取年份和月份（格式：2024-12）
      const reportMonth = report.report_month || '';
      const [year, month] = reportMonth.split('-');
      const yearNum = parseInt(year || '0');

      // 只处理当前年份的数据
      if (yearNum !== currentYearNum) {
        return;
      }

      const yearKey = year || selectedYear;
      const monthKey = month || '';
      const monthLabel = month ? `${parseInt(month)}月` : '';

      if (!yearMap.has(yearKey)) {
        yearMap.set(yearKey, new Map());
      }
      const monthMap = yearMap.get(yearKey)!;
      if (!monthMap.has(monthKey)) {
        monthMap.set(monthKey, []);
      }
      monthMap.get(monthKey)!.push(report);
    });

    // 转换为数组格式
    const result: Array<{
      year: string;
      yearLabel: string;
      months: Array<{ month: string; monthLabel: string; reports: MonthlyReport[] }>;
    }> = [];
    yearMap.forEach((monthMap, yearKey) => {
      const yearLabel = `${yearKey}年`;
      const months: Array<{ month: string; monthLabel: string; reports: MonthlyReport[] }> = [];

      monthMap.forEach((reports, monthKey) => {
        const monthLabel = monthKey ? `${parseInt(monthKey)}月` : '';
        months.push({ month: monthKey, monthLabel, reports });
      });

      // 按月份排序
      months.sort((a, b) => {
        const monthA = parseInt(a.month || '0');
        const monthB = parseInt(b.month || '0');
        return monthA - monthB;
      });

      result.push({ year: yearKey, yearLabel, months });
    });

    // 按年份排序（虽然应该只有一个）
    result.sort((a, b) => a.year.localeCompare(b.year));

    return result;
  }, [monthlyReports, selectedYear]);

  // 获取项目的里程碑（重要里程碑：实施启动、方案确认、交付上线、项目验收）
  const getProjectMilestones = (projectId: string) => {
    const projectMilestones = milestones.filter((m) => m.project_id === projectId);
    const milestoneMap: Record<string, Milestone> = {};

    // 按里程碑名称或category_name匹配（优先使用category_name）
    projectMilestones.forEach((m) => {
      const milestoneName = (m as any).category_name || m.name;
      if (milestoneName.includes('实施启动') || milestoneName.includes('启动')) {
        milestoneMap['实施启动'] = m;
      } else if (milestoneName.includes('方案确认') || milestoneName.includes('确认')) {
        milestoneMap['方案确认'] = m;
      } else if (milestoneName.includes('交付上线') || milestoneName.includes('上线')) {
        milestoneMap['交付上线'] = m;
      } else if (milestoneName.includes('项目验收') || milestoneName.includes('验收')) {
        milestoneMap['项目验收'] = m;
      }
    });

    return milestoneMap;
  };

  const handleExport = () => {
    // TODO: 实现Excel导出功能
    alert('Excel导出功能开发中...');
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      planning: 'bg-gray-100 text-gray-800',
      active: 'bg-green-100 text-green-800',
      delayed: 'bg-red-100 text-red-800',
      completed: 'bg-blue-100 text-blue-800',
      cancelled: 'bg-gray-100 text-gray-500',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  // 获取所有唯一的项目（用于表格行）
  const uniqueProjects = useMemo(() => {
    const projectMap = new Map<string, Project>();
    projects.forEach((p) => projectMap.set(p.id, p));

    // 周报模式：包含有周报的项目
    if (reportType === 'weekly') {
      weeklyReports.forEach((r) => {
        if (!projectMap.has(r.project_id)) {
          projectMap.set(r.project_id, {
            id: r.project_id,
            name: r.project_name || '未知项目',
            project_code: '',
            status: '',
            progress_percent: 0,
          });
        }
      });
    } else {
      // 月报模式：包含有月报的项目
      monthlyReports.forEach((r) => {
        if (!projectMap.has(r.project_id)) {
          projectMap.set(r.project_id, {
            id: r.project_id,
            name: r.project_name || '未知项目',
            project_code: '',
            status: '',
            progress_percent: 0,
          });
        }
      });
    }

    return Array.from(projectMap.values());
  }, [projects, weeklyReports, monthlyReports, reportType]);

  return (
    <div className="space-y-6">
      {/* 标题和操作 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">周月进度报告</h1>
          <p className="text-gray-600 mt-1">项目周报和月报汇总展示（支持两行表头）</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            导出Excel
          </button>
        </div>
      </div>

      {/* 报告类型切换 */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              setReportType('weekly');
              fetchWeeklyReports();
            }}
            className={`px-4 py-2 rounded-lg transition-colors ${
              reportType === 'weekly'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            周报
          </button>
          <button
            onClick={() => {
              setReportType('monthly');
              fetchMonthlyReports();
            }}
            className={`px-4 py-2 rounded-lg transition-colors ${
              reportType === 'monthly'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            月报
          </button>
        </div>
      </div>

      {/* 筛选条件 */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-4 space-y-4">
        <div className="flex items-center gap-2 text-gray-700 font-medium">
          <Filter className="w-4 h-4" />
          <span>筛选条件</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">所有项目</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>

          {reportType === 'weekly' ? (
            <div className="px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg text-gray-700">
              {selectedMonth
                ? `${selectedMonth.split('-')[0]}年${parseInt(selectedMonth.split('-')[1])}月`
                : '当前月份'}
            </div>
          ) : (
            <div className="px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg text-gray-700">
              {selectedYear}年
            </div>
          )}
        </div>
      </div>

      {/* Excel样式表格 - 两行表头 */}
      {loading ? (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-12 text-center text-gray-500">
          加载中...
        </div>
      ) : reportType === 'weekly' ? (
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse border border-gray-300">
              {/* 第一行表头：基础信息和月份 */}
              <thead className="bg-gray-50">
                <tr>
                  <th
                    rowSpan={2}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-gray-100"
                  >
                    项目名称
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-gray-100"
                  >
                    项目编码
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-gray-100"
                  >
                    项目状态
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-gray-100"
                  >
                    进度
                  </th>
                  {organizedWeeklyData.map((monthData) => (
                    <th
                      key={monthData.month}
                      colSpan={monthData.weeks.length}
                      className="px-2 py-2 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-blue-50"
                    >
                      {monthData.monthLabel}
                    </th>
                  ))}
                  <th
                    colSpan={4}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-yellow-50"
                  >
                    重要里程碑
                  </th>
                </tr>
                {/* 第二行表头：周 */}
                <tr>
                  {organizedWeeklyData.map((monthData) =>
                    monthData.weeks.map((week, idx) => (
                      <th
                        key={`${monthData.month}-${idx}`}
                        className="px-2 py-2 text-center text-xs font-medium text-gray-600 border border-gray-300 bg-blue-100"
                      >
                        <div>{week.weekLabel}</div>
                        <div className="text-xs text-gray-500">({week.dateRange})</div>
                      </th>
                    ))
                  )}
                  {/* 里程碑子列 */}
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border border-gray-300 bg-yellow-100">
                    实施启动
                  </th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border border-gray-300 bg-yellow-100">
                    方案确认
                  </th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border border-gray-300 bg-yellow-100">
                    交付上线
                  </th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border border-gray-300 bg-yellow-100">
                    项目验收
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {uniqueProjects.length === 0 ? (
                  <tr>
                    <td
                      colSpan={100}
                      className="px-6 py-4 text-center text-gray-500 border border-gray-300"
                    >
                      暂无数据
                    </td>
                  </tr>
                ) : (
                  uniqueProjects.map((project) => {
                    const projectMilestones = getProjectMilestones(project.id);
                    return (
                      <tr key={project.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-900 border border-gray-300">
                          {project.name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 border border-gray-300">
                          {project.project_code || '-'}
                        </td>
                        <td className="px-4 py-3 text-center border border-gray-300">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(project.status)}`}
                          >
                            {project.status === 'active'
                              ? '进行中'
                              : project.status === 'completed'
                                ? '已完成'
                                : project.status === 'delayed'
                                  ? '已延迟'
                                  : project.status === 'cancelled'
                                    ? '已取消'
                                    : '规划中'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center border border-gray-300">
                          <div className="flex items-center justify-center gap-2">
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-500 h-2 rounded-full"
                                style={{ width: `${project.progress_percent || 0}%` }}
                              />
                            </div>
                            <span className="text-xs text-gray-600">
                              {project.progress_percent || 0}%
                            </span>
                          </div>
                        </td>
                        {/* 周报数据 */}
                        {organizedWeeklyData.map((monthData) =>
                          monthData.weeks.map((week, idx) => {
                            const weekReport = week.reports.find(
                              (r) => r.project_id === project.id
                            );
                            return (
                              <td
                                key={`${monthData.month}-${idx}`}
                                className="px-2 py-2 text-xs text-gray-600 border border-gray-300 min-w-[120px]"
                              >
                                {weekReport ? (
                                  <div className="space-y-1">
                                    <div className="font-medium text-gray-900">成果:</div>
                                    <div className="line-clamp-2 text-gray-600">
                                      {weekReport.content_achievement || '-'}
                                    </div>
                                    <div className="font-medium text-gray-900 mt-1">风险:</div>
                                    <div className="line-clamp-1 text-red-600">
                                      {weekReport.issues_risks || '-'}
                                    </div>
                                  </div>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                            );
                          })
                        )}
                        {/* 里程碑数据 */}
                        <td className="px-2 py-2 text-xs text-center border border-gray-300">
                          {projectMilestones['实施启动'] ? (
                            <div>
                              <div className="text-gray-900">
                                {formatDate(projectMilestones['实施启动'].target_date)}
                              </div>
                              <div
                                className={`text-xs ${projectMilestones['实施启动'].status === 'completed' ? 'text-green-600' : 'text-orange-600'}`}
                              >
                                {projectMilestones['实施启动'].status === 'completed'
                                  ? '已完成'
                                  : '进行中'}
                              </div>
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-2 py-2 text-xs text-center border border-gray-300">
                          {projectMilestones['方案确认'] ? (
                            <div>
                              <div className="text-gray-900">
                                {formatDate(projectMilestones['方案确认'].target_date)}
                              </div>
                              <div
                                className={`text-xs ${projectMilestones['方案确认'].status === 'completed' ? 'text-green-600' : 'text-orange-600'}`}
                              >
                                {projectMilestones['方案确认'].status === 'completed'
                                  ? '已完成'
                                  : '进行中'}
                              </div>
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-2 py-2 text-xs text-center border border-gray-300">
                          {projectMilestones['交付上线'] ? (
                            <div>
                              <div className="text-gray-900">
                                {formatDate(projectMilestones['交付上线'].target_date)}
                              </div>
                              <div
                                className={`text-xs ${projectMilestones['交付上线'].status === 'completed' ? 'text-green-600' : 'text-orange-600'}`}
                              >
                                {projectMilestones['交付上线'].status === 'completed'
                                  ? '已完成'
                                  : '进行中'}
                              </div>
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-2 py-2 text-xs text-center border border-gray-300">
                          {projectMilestones['项目验收'] ? (
                            <div>
                              <div className="text-gray-900">
                                {formatDate(projectMilestones['项目验收'].target_date)}
                              </div>
                              <div
                                className={`text-xs ${projectMilestones['项目验收'].status === 'completed' ? 'text-green-600' : 'text-orange-600'}`}
                              >
                                {projectMilestones['项目验收'].status === 'completed'
                                  ? '已完成'
                                  : '进行中'}
                              </div>
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        // 月报视图：按年份显示各个月份
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse border border-gray-300">
              {/* 第一行表头：基础信息和年份 */}
              <thead className="bg-gray-50">
                <tr>
                  <th
                    rowSpan={2}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-gray-100"
                  >
                    项目名称
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-gray-100"
                  >
                    项目编码
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-gray-100"
                  >
                    项目状态
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-gray-100"
                  >
                    进度
                  </th>
                  {organizedMonthlyData.map((yearData) => (
                    <th
                      key={yearData.year}
                      colSpan={yearData.months.length}
                      className="px-2 py-2 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-blue-50"
                    >
                      {yearData.yearLabel}
                    </th>
                  ))}
                  <th
                    colSpan={4}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase border border-gray-300 bg-yellow-50"
                  >
                    重要里程碑
                  </th>
                </tr>
                {/* 第二行表头：月份 */}
                <tr>
                  {organizedMonthlyData.map((yearData) =>
                    yearData.months.map((month, idx) => (
                      <th
                        key={`${yearData.year}-${month.month}-${idx}`}
                        className="px-2 py-2 text-center text-xs font-medium text-gray-600 border border-gray-300 bg-blue-100"
                      >
                        {month.monthLabel}
                      </th>
                    ))
                  )}
                  {/* 里程碑子列 */}
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border border-gray-300 bg-yellow-100">
                    实施启动
                  </th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border border-gray-300 bg-yellow-100">
                    方案确认
                  </th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border border-gray-300 bg-yellow-100">
                    交付上线
                  </th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-600 border border-gray-300 bg-yellow-100">
                    项目验收
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {uniqueProjects.length === 0 ? (
                  <tr>
                    <td
                      colSpan={100}
                      className="px-6 py-4 text-center text-gray-500 border border-gray-300"
                    >
                      暂无数据
                    </td>
                  </tr>
                ) : (
                  uniqueProjects.map((project) => {
                    const projectMilestones = getProjectMilestones(project.id);
                    return (
                      <tr key={project.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-900 border border-gray-300">
                          {project.name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 border border-gray-300">
                          {project.project_code || '-'}
                        </td>
                        <td className="px-4 py-3 text-center border border-gray-300">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(project.status)}`}
                          >
                            {project.status === 'active'
                              ? '进行中'
                              : project.status === 'completed'
                                ? '已完成'
                                : project.status === 'delayed'
                                  ? '已延迟'
                                  : project.status === 'cancelled'
                                    ? '已取消'
                                    : '规划中'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center border border-gray-300">
                          <div className="flex items-center justify-center gap-2">
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-500 h-2 rounded-full"
                                style={{ width: `${project.progress_percent || 0}%` }}
                              />
                            </div>
                            <span className="text-xs text-gray-600">
                              {project.progress_percent || 0}%
                            </span>
                          </div>
                        </td>
                        {/* 月报数据 */}
                        {organizedMonthlyData.map((yearData) =>
                          yearData.months.map((month, idx) => {
                            const monthReport = month.reports.find(
                              (r) => r.project_id === project.id
                            );
                            return (
                              <td
                                key={`${yearData.year}-${month.month}-${idx}`}
                                className="px-2 py-2 text-xs text-gray-600 border border-gray-300 min-w-[120px]"
                              >
                                {monthReport ? (
                                  <div className="space-y-1">
                                    <div className="font-medium text-gray-900">成果:</div>
                                    <div className="line-clamp-2 text-gray-600">
                                      {monthReport.achievements || '-'}
                                    </div>
                                    <div className="font-medium text-gray-900 mt-1">挑战:</div>
                                    <div className="line-clamp-1 text-red-600">
                                      {monthReport.challenges || '-'}
                                    </div>
                                  </div>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                            );
                          })
                        )}
                        {/* 里程碑数据 */}
                        <td className="px-2 py-2 text-xs text-center border border-gray-300">
                          {projectMilestones['实施启动'] ? (
                            <div>
                              <div className="text-gray-900">
                                {formatDate(projectMilestones['实施启动'].target_date)}
                              </div>
                              <div
                                className={`text-xs ${projectMilestones['实施启动'].status === 'completed' ? 'text-green-600' : 'text-orange-600'}`}
                              >
                                {projectMilestones['实施启动'].status === 'completed'
                                  ? '已完成'
                                  : '进行中'}
                              </div>
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-2 py-2 text-xs text-center border border-gray-300">
                          {projectMilestones['方案确认'] ? (
                            <div>
                              <div className="text-gray-900">
                                {formatDate(projectMilestones['方案确认'].target_date)}
                              </div>
                              <div
                                className={`text-xs ${projectMilestones['方案确认'].status === 'completed' ? 'text-green-600' : 'text-orange-600'}`}
                              >
                                {projectMilestones['方案确认'].status === 'completed'
                                  ? '已完成'
                                  : '进行中'}
                              </div>
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-2 py-2 text-xs text-center border border-gray-300">
                          {projectMilestones['交付上线'] ? (
                            <div>
                              <div className="text-gray-900">
                                {formatDate(projectMilestones['交付上线'].target_date)}
                              </div>
                              <div
                                className={`text-xs ${projectMilestones['交付上线'].status === 'completed' ? 'text-green-600' : 'text-orange-600'}`}
                              >
                                {projectMilestones['交付上线'].status === 'completed'
                                  ? '已完成'
                                  : '进行中'}
                              </div>
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-2 py-2 text-xs text-center border border-gray-300">
                          {projectMilestones['项目验收'] ? (
                            <div>
                              <div className="text-gray-900">
                                {formatDate(projectMilestones['项目验收'].target_date)}
                              </div>
                              <div
                                className={`text-xs ${projectMilestones['项目验收'].status === 'completed' ? 'text-green-600' : 'text-orange-600'}`}
                              >
                                {projectMilestones['项目验收'].status === 'completed'
                                  ? '已完成'
                                  : '进行中'}
                              </div>
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 统计信息 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Calendar className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">
                {reportType === 'weekly' ? '总周报数' : '总月报数'}
              </p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {reportType === 'weekly' ? weeklyReports.length : monthlyReports.length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">平均进度</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {projects.length > 0
                  ? Math.round(
                      projects.reduce((sum, p) => sum + (p.progress_percent || 0), 0) /
                        projects.length
                    )
                  : 0}
                %
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-orange-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">进行中项目</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {projects.filter((p) => p.status === 'active').length}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
