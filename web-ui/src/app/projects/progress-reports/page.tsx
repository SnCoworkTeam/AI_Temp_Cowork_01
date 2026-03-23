'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { getAccessToken } from '@/lib/auth';
import { useAuth } from '@/contexts/AuthContext';
import { apiGatewayClient } from '@/lib/api/client';
import { Download, Filter, Calendar, TrendingUp } from 'lucide-react';

interface BasicDataCategory {
  id: string;
  category_type: string;
  code: string;
  name: string;
  description?: string;
}

interface Project {
  id: string;
  name: string;
  project_code: string;
  status: string;
  progress_percent: number;
  reporter_id?: string; // 填报人ID
  reporter_name?: string; // 填报人
  basic_data_categories?: BasicDataCategory[]; // 基础数据分类
}

interface Todo {
  id: string;
  title: string;
  description?: string;
  status: string;
  priority: string;
  due_date?: string;
  completed_at?: string;
  user_id?: string; // 分配给的用户ID
  metadata?: any;
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
  const { user } = useAuth(); // 获取当前用户信息
  const [reportType, setReportType] = useState<'weekly' | 'monthly'>('weekly');
  // 分类选择：基设网安、业务经营、管理应用、生产运营、瑞恒基地
  const [selectedCategory, setSelectedCategory] = useState<string>('all'); // 'all' 表示所有分类
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
  const [todos, setTodos] = useState<Record<string, Todo[]>>({}); // 按项目ID存储待办列表
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState('all');
  const [editingTodoProjectId, setEditingTodoProjectId] = useState<string | null>(null);
  const [newTodoTitle, setNewTodoTitle] = useState('');
  const [isFetchingTodos, setIsFetchingTodos] = useState(false); // 防止并发请求

  // 获取当前用户ID
  const currentUserId = user?.user_id || user?.id || '';

  // 判断待办是否是自己创建的
  const isTodoCreatedByMe = (todo: Todo): boolean => {
    // 如果metadata中有created_by，使用它
    if (todo.metadata?.created_by) {
      return todo.metadata.created_by === currentUserId;
    }
    // 如果user_id等于当前用户ID，且没有created_by，认为是自己创建的（兼容旧数据）
    if (todo.user_id) {
      return todo.user_id === currentUserId;
    }
    // 默认返回false，表示不是自己创建的
    return false;
  };

  // 分类列表
  const categories = [
    { value: 'all', label: '全部' },
    { value: '基设网安', label: '基设网安' },
    { value: '业务经营', label: '业务经营' },
    { value: '管理应用', label: '管理应用' },
    { value: '生产运营', label: '生产运营' },
    { value: '瑞恒基地', label: '瑞恒基地' },
  ];

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

  // 获取项目的待办列表 - 当项目列表、报告列表或报告类型更新时重新获取
  // 使用防抖，避免频繁调用
  // 使用 useRef 来跟踪上次获取的项目ID集合，避免重复获取
  const lastFetchedProjectIdsRef = useRef<Set<string>>(new Set());
  const lastReportTypeRef = useRef<string>(reportType);

  useEffect(() => {
    // 如果正在获取中，跳过
    if (isFetchingTodos) {
      return;
    }

    // 收集当前需要获取待办的项目ID
    const currentProjectIds = new Set<string>();
    projects.forEach((p) => {
      if (p.id) currentProjectIds.add(p.id);
    });
    if (reportType === 'weekly') {
      weeklyReports.forEach((r) => {
        if (r.project_id) currentProjectIds.add(r.project_id);
      });
    } else {
      monthlyReports.forEach((r) => {
        if (r.project_id) currentProjectIds.add(r.project_id);
      });
    }

    // 检查是否需要重新获取：
    // 1. 项目ID集合发生变化
    // 2. 报告类型发生变化
    // 3. 有数据但还没有获取过
    const projectIdsChanged =
      currentProjectIds.size !== lastFetchedProjectIdsRef.current.size ||
      Array.from(currentProjectIds).some((id) => !lastFetchedProjectIdsRef.current.has(id)) ||
      Array.from(lastFetchedProjectIdsRef.current).some((id) => !currentProjectIds.has(id));
    const reportTypeChanged = lastReportTypeRef.current !== reportType;
    const hasDataButNotFetched = currentProjectIds.size > 0 && lastFetchedProjectIdsRef.current.size === 0;

    if (projectIdsChanged || reportTypeChanged || hasDataButNotFetched) {
      // 延迟500ms执行，避免在数据快速更新时频繁调用
      const timer = setTimeout(() => {
        lastFetchedProjectIdsRef.current = new Set(currentProjectIds);
        lastReportTypeRef.current = reportType;
        fetchTodosForProjects();
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [projects, weeklyReports, monthlyReports, reportType, isFetchingTodos]);

  const fetchProjects = async () => {
    try {
      // 使用 apiGatewayClient 以获得更好的错误处理和认证
      let allProjects: Project[] = [];
      let skip = 0;
      const limit = 1000; // 每次获取1000条
      let hasMore = true;

      while (hasMore) {
        try {
          const data = await apiGatewayClient.get<{ items: Project[]; total?: number }>(
            `/api/v1/projects?skip=${skip}&limit=${limit}`
          );
          const items = data.items || [];
          allProjects = [...allProjects, ...items];

          // 如果返回的项目数少于limit，说明已经获取完所有数据
          if (items.length < limit || (data.total && allProjects.length >= data.total)) {
            hasMore = false;
          } else {
            skip += limit;
          }
        } catch (error: any) {
          // 401 错误会被 apiGatewayClient 自动处理（重定向到登录页）
          if (error?.statusCode === 401) {
            return; // 静默处理，避免在控制台显示过多错误信息
          }
          console.error('获取项目列表失败:', error);
          hasMore = false;
        }
      }

      setProjects(allProjects);
      console.log(`已获取 ${allProjects.length} 个项目`);
    } catch (error: any) {
      // 401 错误会被 apiGatewayClient 自动处理（重定向到登录页）
      if (error?.statusCode !== 401) {
        console.error('获取项目列表失败:', error);
      }
    }
  };

  const fetchMilestones = async () => {
    try {
      // 使用 apiGatewayClient 以获得更好的错误处理和认证
      const data = await apiGatewayClient.get<{ items: Milestone[] }>('/api/v1/milestones');
      setMilestones(data.items || []);
    } catch (error: any) {
      // 401 错误会被 apiGatewayClient 自动处理（重定向到登录页）
      if (error?.statusCode !== 401) {
        console.error('获取里程碑列表失败:', error);
      }
      setMilestones([]);
    }
  };

  // 获取所有项目的待办列表 - 包括所有在表格中显示的项目
  const fetchTodosForProjects = async () => {
    // 防止并发请求
    if (isFetchingTodos) {
      console.log('待办列表正在获取中，跳过重复请求');
      return;
    }

    try {
      setIsFetchingTodos(true);
      const token = getAccessToken();
      if (!token) {
        setIsFetchingTodos(false);
        return;
      }

      const todosMap: Record<string, Todo[]> = {};

      // 收集所有需要获取待办的项目ID（包括在projects中的和只在reports中的）
      const projectIds = new Set<string>();

      // 添加所有projects中的项目ID
      projects.forEach((p) => {
        if (p.id) projectIds.add(p.id);
      });

      // 添加所有周报/月报中的项目ID（可能不在projects列表中）
      if (reportType === 'weekly') {
        weeklyReports.forEach((r) => {
          if (r.project_id) projectIds.add(r.project_id);
        });
      } else {
        monthlyReports.forEach((r) => {
          if (r.project_id) projectIds.add(r.project_id);
        });
      }

      // 为每个项目获取待办列表，添加延迟避免429错误
      // 优化：获取到一个项目的待办后立即更新状态，实现逐步显示
      const projectIdArray = Array.from(projectIds);
      console.log(`开始获取 ${projectIdArray.length} 个项目的待办列表...`);

      // 初始化所有项目的待办为空数组，实现逐步填充
      const initialTodosMap: Record<string, Todo[]> = {};
      projectIdArray.forEach((pid) => {
        if (pid) initialTodosMap[pid] = [];
      });
      setTodos(initialTodosMap);

      for (let i = 0; i < projectIdArray.length; i++) {
        const projectId = projectIdArray[i];
        if (!projectId) continue;

        try {
          // 添加延迟，避免请求过快导致429错误 - 增加到1200ms
          if (i > 0) {
            await new Promise((resolve) => setTimeout(resolve, 1200)); // 每个请求间隔1200ms
          }

          // 使用 apiGatewayClient 以获得更好的错误处理和超时控制
          const data = await apiGatewayClient.get<{ items: Todo[] }>(
            `/api/v1/todos?project_id=${projectId}&limit=1000`
          );
          const allTodos = data.items || [];
            // 仅在开发环境输出详细日志
            if (process.env.NODE_ENV === 'development') {
              console.log(
                `项目 ${projectId} 获取到 ${allTodos.length} 个待办，当前报告类型: ${reportType}`
              );
            }

            // 根据当前报告类型过滤待办：
            // 1. report_visible必须为true（或未设置，兼容旧数据）
            // 2. report_type必须匹配当前的reportType（周表格创建的只显示在周表格，月表格创建的只显示在月表格）
            // 3. 如果没有report_type字段（旧数据），则同时显示在周表格和月表格中（兼容旧数据）
            const visibleTodos = allTodos.filter((todo: Todo) => {
              // 首先检查report_visible
              if (todo.metadata?.report_visible === false) {
                return false;
              }
              // 如果有report_type字段，必须匹配当前的reportType
              if (todo.metadata?.report_type) {
                return todo.metadata.report_type === reportType;
              }
              // 如果没有report_type字段（旧数据），则显示（兼容旧数据）
              return true;
            });

            // 仅在开发环境输出详细日志
            if (process.env.NODE_ENV === 'development') {
              console.log(`项目 ${projectId} 过滤后剩余 ${visibleTodos.length} 个待办`);
            }

            // 立即更新状态，实现逐步显示
            setTodos((prevTodos) => ({
              ...prevTodos,
              [projectId]: visibleTodos,
            }));
        } catch (error: any) {
          // 静默处理错误，避免在控制台显示过多错误信息
          // 401 错误会被 apiGatewayClient 自动处理（重定向到登录页）
          if (error?.statusCode !== 401) {
            // 只在非认证错误时静默记录
            if (process.env.NODE_ENV === 'development') {
              console.error(`获取项目 ${projectId} 的待办列表失败:`, error);
            }
          }
          // 设置为空数组，避免页面崩溃
          setTodos((prevTodos) => ({
            ...prevTodos,
            [projectId]: [],
          }));
        }
      }

      // 最终汇总日志
      const finalTodos = todos;
      const totalTodos = Object.values(finalTodos).reduce((sum, todos) => sum + todos.length, 0);
      console.log(`完成获取 ${projectIdArray.length} 个项目的待办列表，共 ${totalTodos} 个待办`);
    } catch (error) {
      console.error('获取待办列表失败:', error);
    } finally {
      setIsFetchingTodos(false);
    }
  };

  // 创建待办事项
  const handleCreateTodo = async (projectId: string, reporterId?: string) => {
    if (!newTodoTitle.trim()) {
      alert('请输入待办内容');
      return;
    }

    if (!reporterId) {
      alert('该项目没有填报人，无法创建待办');
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      if (!token) {
        alert('请先登录');
        return;
      }

      const response = await fetch(`${apiUrl}/api/v1/todos`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newTodoTitle.trim(),
          description: '',
          category: 'project',
          priority: 'medium',
          project_id: projectId,
          user_id: reporterId, // 分配给填报人
          metadata: {
            report_visible: true,
            report_type: reportType, // 标记是在周表格还是月表格创建的：'weekly' 或 'monthly'
            created_by: currentUserId, // 记录创建者ID
          },
        }),
      });

      if (response.ok) {
        const newTodo = await response.json();
        // 立即更新本地状态，将新待办添加到对应项目的待办列表中
        setTodos((prevTodos) => {
          const updatedTodos = { ...prevTodos };
          if (!updatedTodos[projectId]) {
            updatedTodos[projectId] = [];
          }
          // 检查是否已存在（避免重复添加）
          const exists = updatedTodos[projectId].some((t) => t.id === newTodo.id);
          if (!exists) {
            updatedTodos[projectId] = [...updatedTodos[projectId], newTodo];
          }
          return updatedTodos;
        });
        setNewTodoTitle('');
        setEditingTodoProjectId(null);
        // 重新获取待办列表以确保数据同步
        await fetchTodosForProjects();
      } else {
        const errorData = await response.json();
        alert(errorData.detail || '创建待办失败');
      }
    } catch (error) {
      console.error('创建待办失败:', error);
      alert('创建待办失败');
    }
  };

  // 删除待办（软删除，只隐藏显示）
  const handleDeleteTodo = async (todoId: string, projectId: string) => {
    if (!confirm('确定要删除这条待办吗？删除后不会在报告中显示，但待办仍然存在于系统中。')) {
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();
      if (!token) {
        alert('请先登录');
        return;
      }

      const response = await fetch(`${apiUrl}/api/v1/todos/${todoId}/hide-from-report`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        // 重新获取待办列表
        await fetchTodosForProjects();
      } else {
        const errorData = await response.json();
        alert(errorData.detail || '删除待办失败');
      }
    } catch (error) {
      console.error('删除待办失败:', error);
      alert('删除待办失败');
    }
  };

  const fetchWeeklyReports = async () => {
    try {
      setLoading(true);
      // 使用 apiGatewayClient 以获得更好的错误处理和认证

      // 分页获取所有周报数据，确保不遗漏
      let allWeeklyReports: WeeklyReport[] = [];
      let skip = 0;
      const limit = 1000;
      let hasMore = true;

      while (hasMore) {
        try {
          const params = [`skip=${skip}`, `limit=${limit}`];
          if (selectedProject && selectedProject !== 'all') {
            params.push(`project_id=${selectedProject}`);
          }
          // 不添加month参数，获取所有周报数据，然后在前端按周范围过滤
          // 这样可以确保跨月的周也能正确显示数据
          const url = `/api/v1/weekly-reports?${params.join('&')}`;

          const data = await apiGatewayClient.get<{ items: WeeklyReport[]; total?: number }>(url);
          const items = data.items || [];
          allWeeklyReports = [...allWeeklyReports, ...items];

          // 如果返回的周报数少于limit，说明已经获取完所有数据
          if (items.length < limit || (data.total && allWeeklyReports.length >= data.total)) {
            hasMore = false;
          } else {
            skip += limit;
          }
        } catch (error: any) {
          // 401 错误会被 apiGatewayClient 自动处理（重定向到登录页）
          if (error?.statusCode === 401) {
            return; // 静默处理，避免在控制台显示过多错误信息
          }
          console.error('获取周报列表失败:', error);
          hasMore = false;
        }
      }

      setWeeklyReports(allWeeklyReports);
      console.log(`已获取 ${allWeeklyReports.length} 条周报`);
    } catch (error: any) {
      // 401 错误会被 apiGatewayClient 自动处理（重定向到登录页）
      if (error?.statusCode !== 401) {
        console.error('获取周报列表失败:', error);
      }
      setWeeklyReports([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchMonthlyReports = async () => {
    try {
      setLoading(true);
      // 使用 apiGatewayClient 以获得更好的错误处理和认证
      let allMonthlyReports: MonthlyReport[] = [];
      let skip = 0;
      const limit = 1000;
      let hasMore = true;

      while (hasMore) {
        try {
          const params = [`skip=${skip}`, `limit=${limit}`];
          if (selectedProject && selectedProject !== 'all') {
            params.push(`project_id=${selectedProject}`);
          }
          if (selectedYear) {
            params.push(`year=${selectedYear}`);
          }
          const url = `/api/v1/monthly-reports?${params.join('&')}`;

          const data = await apiGatewayClient.get<{ items: MonthlyReport[]; total?: number }>(url);
          const items = data.items || [];
          allMonthlyReports = [...allMonthlyReports, ...items];

          // 如果返回的月报数少于limit，说明已经获取完所有数据
          if (items.length < limit || (data.total && allMonthlyReports.length >= data.total)) {
            hasMore = false;
          } else {
            skip += limit;
          }
        } catch (error: any) {
          // 401 错误会被 apiGatewayClient 自动处理（重定向到登录页）
          if (error?.statusCode === 401) {
            return; // 静默处理，避免在控制台显示过多错误信息
          }
          console.error('获取月报列表失败:', error);
          hasMore = false;
        }
      }

      setMonthlyReports(allMonthlyReports);
      console.log(`已获取 ${allMonthlyReports.length} 条月报`);
    } catch (error: any) {
      // 401 错误会被 apiGatewayClient 自动处理（重定向到登录页）
      if (error?.statusCode !== 401) {
        console.error('获取月报列表失败:', error);
      }
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

  // 获取ISO周数（修正版本，正确处理跨年周）
  const getISOWeek = (date: Date): number => {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);

    // ISO周：找到包含该日期的周的周四
    const dayOfWeek = d.getDay() || 7; // 0=周日转为7
    const thursday = new Date(d);
    thursday.setDate(d.getDate() + (4 - dayOfWeek));

    // 找到该周四所在年份的1月1日
    const year = thursday.getFullYear();
    const jan1 = new Date(year, 0, 1);
    const jan1DayOfWeek = jan1.getDay() || 7;

    // 找到第一周的周一（包含1月4日的那一周）
    let firstWeekMonday = new Date(year, 0, 4);
    const jan4DayOfWeek = firstWeekMonday.getDay() || 7;
    firstWeekMonday.setDate(4 - (jan4DayOfWeek - 1));

    // 如果1月1日不在第一周，则第一周从1月1日所在周的周一开始
    if (jan1 < firstWeekMonday) {
      firstWeekMonday = new Date(jan1);
      firstWeekMonday.setDate(1 - (jan1DayOfWeek - 1));
    }

    // 计算周数
    const daysDiff = Math.floor(
      (thursday.getTime() - firstWeekMonday.getTime()) / (24 * 60 * 60 * 1000)
    );
    const week = Math.floor(daysDiff / 7) + 1;

    return week;
  };

  // 获取指定年份的最后一周的周数
  const getLastWeekOfYear = (year: number): number => {
    const dec31 = new Date(year, 11, 31);
    return getISOWeek(dec31);
  };

  // 计算月份的所有周（自动计算，从第一周到最后一周，连续）
  const calculateWeeksInMonth = (year: number, month: number): WeekData[] => {
    const weeks: WeekData[] = [];
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0); // 月份的最后一天

    // 找到该月1号所在的周的周一（ISO周从周一开始）
    const weekStart = new Date(firstDay);
    const dayOfWeek = weekStart.getDay(); // 0=周日, 1=周一, ..., 6=周六
    // 计算回到周一的天数
    const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    weekStart.setDate(weekStart.getDate() - daysToMonday);

    // 生成该月的所有周（从1号所在的周开始，到31号所在的周结束）
    while (weekStart <= lastDay) {
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekEnd.getDate() + 6); // 周日

      // 只包含与该月有交集的周
      const weekStartInMonth = weekStart < firstDay ? firstDay : weekStart;
      const weekEndInMonth = weekEnd > lastDay ? lastDay : weekEnd;

      // 如果周与该月有交集，则添加
      if (weekStartInMonth <= weekEndInMonth) {
        // 计算ISO周数（使用该月内的日期）
        let weekNumber = getISOWeek(weekStartInMonth);

        // 特殊处理：如果12月最后几天显示为第1周，说明是跨年周
        // 应该显示为当前年份的最后一周（第52或53周）
        if (month === 12 && weekNumber === 1) {
          // 检查这是否是跨年周：如果12月31日也是第1周，说明这是下一年的第1周
          const dec31Week = getISOWeek(new Date(year, 11, 31));
          if (dec31Week === 1) {
            // 这是跨年周，应该显示为当前年份的最后一周
            // 计算上一周的周数
            const prevWeekStart = new Date(weekStart);
            prevWeekStart.setDate(prevWeekStart.getDate() - 7);
            const prevWeekNumber = getISOWeek(prevWeekStart);
            // 如果上一周是第52或53周，使用它；否则使用当前年份的最后一周
            if (prevWeekNumber >= 52) {
              weekNumber = prevWeekNumber;
            } else {
              weekNumber = getLastWeekOfYear(year);
            }
          }
        }

        const weekLabel = `第${weekNumber}周`;
        const dateRange = `${formatDate(weekStartInMonth)}-${formatDate(weekEndInMonth)}`;

        // 查找该周是否有周报数据（使用完整的周范围）
        // 注意：weekStart和weekEnd是Date对象，需要正确比较
        const weekReports = weeklyReports.filter((report) => {
          if (!report.report_date) return false;
          try {
            const reportDate = new Date(report.report_date);
            // 重置时间部分，只比较日期
            const reportDateOnly = new Date(
              reportDate.getFullYear(),
              reportDate.getMonth(),
              reportDate.getDate()
            );
            const weekStartOnly = new Date(
              weekStart.getFullYear(),
              weekStart.getMonth(),
              weekStart.getDate()
            );
            const weekEndOnly = new Date(
              weekEnd.getFullYear(),
              weekEnd.getMonth(),
              weekEnd.getDate()
            );
            return reportDateOnly >= weekStartOnly && reportDateOnly <= weekEndOnly;
          } catch (error) {
            console.error('解析周报日期失败:', report.report_date, error);
            return false;
          }
        });

        weeks.push({ weekLabel, dateRange, reports: weekReports });
      }

      // 下一周（从下一个周一开始）
      weekStart.setDate(weekStart.getDate() + 7);
    }

    return weeks;
  };

  // 组织周报数据：自动计算该月份的所有周
  const organizedWeeklyData = useMemo(() => {
    if (!selectedMonth) {
      return [];
    }

    const [year, month] = selectedMonth.split('-');
    const yearNum = parseInt(year);
    const monthNum = parseInt(month);
    const monthLabel = `${yearNum}年${monthNum}月`;

    // 自动计算该月的所有周
    const weeks = calculateWeeksInMonth(yearNum, monthNum);

    return [
      {
        month: selectedMonth,
        monthLabel,
        weeks,
      },
    ];
  }, [weeklyReports, selectedMonth]);

  // 组织月报数据：按年份和月份分组（只显示当前年份）
  // 确保所有项目都显示1-12月，即使没有月报数据
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

    // 始终生成当前年份的1-12月，无论是否有数据
    const yearLabel = `${selectedYear}年`;
    const months: Array<{ month: string; monthLabel: string; reports: MonthlyReport[] }> = [];

    // 生成1-12月
    for (let i = 1; i <= 12; i++) {
      const monthKey = i.toString().padStart(2, '0');
      const monthLabel = `${i}月`;
      // 从yearMap中获取该月份的数据（如果有）
      const monthReports = yearMap.get(selectedYear)?.get(monthKey) || [];
      months.push({ month: monthKey, monthLabel, reports: monthReports });
    }

    result.push({ year: selectedYear, yearLabel, months });

    // 按年份排序（虽然应该只有一个）
    result.sort((a, b) => a.year.localeCompare(b.year));

    return result;
  }, [monthlyReports, selectedYear]);

  // 获取项目的里程碑（重要里程碑）
  const getProjectMilestones = (projectId: string) => {
    const projectMilestones = milestones.filter((m) => m.project_id === projectId);
    const milestoneMap: Record<string, Milestone> = {};

    // 按里程碑名称匹配
    projectMilestones.forEach((m) => {
      if (m.name.includes('实施启动') || m.name.includes('启动')) {
        milestoneMap['实施启动'] = m;
      } else if (m.name.includes('方案确认') || m.name.includes('确认')) {
        milestoneMap['方案确认'] = m;
      } else if (m.name.includes('交付上线') || m.name.includes('上线')) {
        milestoneMap['交付上线'] = m;
      } else if (m.name.includes('项目验收') || m.name.includes('验收')) {
        milestoneMap['项目验收'] = m;
      }
    });

    return milestoneMap;
  };

  // 获取项目的项目阶段
  const getProjectPhase = (project: Project): string => {
    if (!project.basic_data_categories || project.basic_data_categories.length === 0) {
      return '-';
    }

    const phaseCategory = project.basic_data_categories.find(
      (cat) => cat.category_type === 'project_phase'
    );

    return phaseCategory ? phaseCategory.name : '-';
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

  // 获取项目的分类（项目分类）
  const getProjectCategory = (project: Project): string | null => {
    if (!project.basic_data_categories || project.basic_data_categories.length === 0) {
      return null;
    }

    const categoryCategory = project.basic_data_categories.find(
      (cat) => cat.category_type === 'project_category'
    );

    return categoryCategory ? categoryCategory.name : null;
  };

  // 获取所有唯一的项目（用于表格行），并根据分类过滤
  const uniqueProjects = useMemo(() => {
    const projectMap = new Map<string, Project>();

    // 首先添加所有projects中的项目（完整信息）
    projects.forEach((p) => {
      if (p.id) {
        projectMap.set(p.id, p);
      }
    });

    // 周报模式：包含有周报的项目
    if (reportType === 'weekly') {
      weeklyReports.forEach((r) => {
        if (r.project_id && !projectMap.has(r.project_id)) {
          // 从projects数组中查找对应的项目信息
          const project = projects.find((p) => p.id === r.project_id);
          // 如果projects中没有，创建一个基础项目对象
          projectMap.set(r.project_id, {
            id: r.project_id,
            name: r.project_name || '未知项目',
            project_code: project?.project_code || '',
            status: project?.status || 'active',
            progress_percent: project?.progress_percent || 0,
            reporter_id: project?.reporter_id,
            reporter_name: project?.reporter_name || '',
            basic_data_categories: project?.basic_data_categories || [],
          });
        } else if (r.project_id && projectMap.has(r.project_id)) {
          // 如果已存在，确保使用最新的项目信息（从projects中获取）
          const project = projects.find((p) => p.id === r.project_id);
          if (project) {
            projectMap.set(r.project_id, project);
          }
        }
      });
    } else {
      // 月报模式：包含有月报的项目
      monthlyReports.forEach((r) => {
        if (r.project_id && !projectMap.has(r.project_id)) {
          // 从projects数组中查找对应的项目信息
          const project = projects.find((p) => p.id === r.project_id);
          // 如果projects中没有，创建一个基础项目对象
          projectMap.set(r.project_id, {
            id: r.project_id,
            name: r.project_name || '未知项目',
            project_code: project?.project_code || '',
            status: project?.status || 'active',
            progress_percent: project?.progress_percent || 0,
            reporter_id: project?.reporter_id,
            reporter_name: project?.reporter_name || '',
            basic_data_categories: project?.basic_data_categories || [],
          });
        } else if (r.project_id && projectMap.has(r.project_id)) {
          // 如果已存在，确保使用最新的项目信息（从projects中获取）
          const project = projects.find((p) => p.id === r.project_id);
          if (project) {
            projectMap.set(r.project_id, project);
          }
        }
      });
    }

    // 根据选择的分类过滤项目
    let filteredProjects = Array.from(projectMap.values());

    if (selectedCategory !== 'all') {
      filteredProjects = filteredProjects.filter((project) => {
        const projectCategory = getProjectCategory(project);
        return projectCategory === selectedCategory;
      });
    }

    return filteredProjects;
  }, [projects, weeklyReports, monthlyReports, reportType, selectedCategory]);

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

      {/* 分类页签 */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
        <div className="mb-2 text-sm font-medium text-gray-700">项目分类</div>
        <div className="flex items-center gap-2 flex-wrap">
          {categories.map((category) => (
            <button
              key={category.value}
              onClick={() => setSelectedCategory(category.value)}
              className={`px-4 py-2 rounded-lg transition-colors font-medium ${
                selectedCategory === category.value
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category.label}
            </button>
          ))}
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
                {uniqueProjects.length > 0
                  ? Math.round(
                      uniqueProjects.reduce((sum, p) => sum + (p.progress_percent || 0), 0) /
                        uniqueProjects.length
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
                {uniqueProjects.filter((p) => p.status === 'active').length}
              </p>
            </div>
          </div>
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
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-0">
              {/* 第一行表头：基础信息和月份 */}
              <thead>
                <tr>
                  <th
                    rowSpan={2}
                    className="sticky left-0 z-20 px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300 shadow-sm"
                  >
                    序号
                  </th>
                  <th
                    rowSpan={2}
                    className="sticky left-[60px] z-10 px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300 shadow-sm"
                  >
                    <div className="flex items-center justify-center gap-1">
                      <span>项目名称</span>
                    </div>
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300"
                  >
                    项目编码
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300"
                  >
                    填报人
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300"
                  >
                    项目状态
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300"
                  >
                    项目阶段
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-purple-100 to-purple-50 border-r border-b border-gray-300 min-w-[200px]"
                  >
                    <div className="flex items-center justify-center">
                      <span className="text-purple-900">待办及重点提示</span>
                    </div>
                  </th>
                  {organizedWeeklyData.map((monthData) => (
                    <th
                      key={monthData.month}
                      colSpan={monthData.weeks.length}
                      className="px-3 py-3 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-blue-100 to-blue-50 border-r border-b border-gray-300"
                    >
                      <div className="flex items-center justify-center">
                        <span className="text-blue-900">{monthData.monthLabel}</span>
                      </div>
                    </th>
                  ))}
                  <th
                    colSpan={4}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-amber-100 to-amber-50 border-r border-b border-gray-300"
                  >
                    <div className="flex items-center justify-center">
                      <span className="text-amber-900">重要里程碑</span>
                    </div>
                  </th>
                </tr>
                {/* 第二行表头：周 */}
                <tr>
                  {organizedWeeklyData.map((monthData) =>
                    monthData.weeks.map((week, idx) => (
                      <th
                        key={`${monthData.month}-${idx}`}
                        className="px-2 py-2.5 text-center text-xs font-medium text-gray-700 bg-gradient-to-b from-blue-50 to-blue-100/50 border-r border-b border-gray-300"
                      >
                        <div className="font-semibold text-blue-900">{week.weekLabel}</div>
                        <div className="text-xs text-gray-600 mt-0.5">({week.dateRange})</div>
                      </th>
                    ))
                  )}
                  {/* 里程碑子列 */}
                  <th className="px-2 py-2.5 text-center text-xs font-medium text-gray-700 bg-gradient-to-b from-amber-50 to-amber-100/50 border-r border-b border-gray-300">
                    <span className="text-amber-900">实施启动</span>
                  </th>
                  <th className="px-2 py-2.5 text-center text-xs font-medium text-gray-700 bg-gradient-to-b from-amber-50 to-amber-100/50 border-r border-b border-gray-300">
                    <span className="text-amber-900">方案确认</span>
                  </th>
                  <th className="px-2 py-2.5 text-center text-xs font-medium text-gray-700 bg-gradient-to-b from-amber-50 to-amber-100/50 border-r border-b border-gray-300">
                    <span className="text-amber-900">交付上线</span>
                  </th>
                  <th className="px-2 py-2.5 text-center text-xs font-medium text-gray-700 bg-gradient-to-b from-amber-50 to-amber-100/50 border-r border-b border-gray-300">
                    <span className="text-amber-900">项目验收</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {uniqueProjects.length === 0 ? (
                  <tr>
                    <td
                      colSpan={100}
                      className="px-6 py-8 text-center text-gray-500 border-b border-gray-200"
                    >
                      <div className="flex flex-col items-center justify-center gap-2">
                        <span className="text-lg">暂无数据</span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  uniqueProjects.map((project, idx) => {
                    const projectMilestones = getProjectMilestones(project.id);
                    return (
                      <tr
                        key={project.id}
                        className="hover:bg-blue-50/30 transition-colors duration-150"
                      >
                        <td className="sticky left-0 z-10 px-4 py-3 text-center text-sm font-medium text-gray-900 bg-white border-r border-b border-gray-200 shadow-sm hover:bg-blue-50/30">
                          {idx + 1}
                        </td>
                        <td className="sticky left-[60px] z-10 px-4 py-3 text-sm font-medium text-gray-900 bg-white border-r border-b border-gray-200 shadow-sm hover:bg-blue-50/30">
                          {project.name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 border-r border-b border-gray-200">
                          {project.project_code || '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700 border-r border-b border-gray-200">
                          {project.reporter_name || <span className="text-gray-400">-</span>}
                        </td>
                        <td className="px-4 py-3 text-center border-r border-b border-gray-200">
                          <span
                            className={`inline-flex px-2.5 py-1 text-xs font-semibold rounded-full shadow-sm ${getStatusColor(project.status)}`}
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
                        <td className="px-4 py-3 text-sm text-gray-700 border-r border-b border-gray-200">
                          {getProjectPhase(project)}
                        </td>
                        {/* 待办及重点提示 */}
                        <td className="px-3 py-3 text-sm border-r border-b border-gray-200 bg-purple-50/30 min-w-[200px]">
                          <div className="space-y-2">
                            {/* 待办列表 */}
                            {(() => {
                              const projectTodos = todos[project.id] || [];
                              // 移除调试日志，避免控制台输出过多
                              return projectTodos.map((todo) => {
                                const isCompleted = todo.status === 'completed';
                                return (
                                  <div
                                    key={todo.id}
                                    className={`p-2 rounded-lg border-l-4 ${
                                      isCompleted
                                        ? 'bg-gray-100 border-gray-400 opacity-75'
                                        : todo.priority === 'high'
                                          ? 'bg-red-50 border-red-500'
                                          : 'bg-yellow-50 border-yellow-500'
                                    }`}
                                  >
                                    <div className="flex items-start justify-between gap-2">
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                          <div
                                            className={`text-xs font-medium ${
                                              isCompleted
                                                ? 'line-through text-gray-500'
                                                : 'text-gray-900'
                                            }`}
                                          >
                                            {todo.title}
                                          </div>
                                        </div>
                                      </div>
                                      {/* 只有自己创建的待办才显示删除按钮 */}
                                      {isCompleted && isTodoCreatedByMe(todo) && (
                                        <button
                                          onClick={() => handleDeleteTodo(todo.id, project.id)}
                                          className="text-red-500 hover:text-red-700 text-xs px-1.5 py-0.5 rounded hover:bg-red-100 transition-colors"
                                          title="删除待办"
                                        >
                                          删除
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                );
                              });
                            })()}

                            {/* 新增待办按钮 */}
                            {editingTodoProjectId === project.id ? (
                              <div className="space-y-2 p-2 bg-white border border-purple-300 rounded-lg">
                                <input
                                  type="text"
                                  value={newTodoTitle}
                                  onChange={(e) => setNewTodoTitle(e.target.value)}
                                  placeholder="输入待办内容..."
                                  className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                                  autoFocus
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                      handleCreateTodo(project.id, project.reporter_id);
                                    } else if (e.key === 'Escape') {
                                      setEditingTodoProjectId(null);
                                      setNewTodoTitle('');
                                    }
                                  }}
                                />
                                <div className="flex items-center gap-2">
                                  <button
                                    onClick={() =>
                                      handleCreateTodo(project.id, project.reporter_id)
                                    }
                                    className="flex-1 px-2 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
                                  >
                                    保存
                                  </button>
                                  <button
                                    onClick={() => {
                                      setEditingTodoProjectId(null);
                                      setNewTodoTitle('');
                                    }}
                                    className="flex-1 px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                                  >
                                    取消
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <button
                                onClick={() => {
                                  setEditingTodoProjectId(project.id);
                                  setNewTodoTitle('');
                                }}
                                className="w-full px-2 py-1.5 text-xs text-purple-700 bg-purple-100 border border-purple-300 rounded-lg hover:bg-purple-200 transition-colors flex items-center justify-center gap-1"
                              >
                                <span>+</span>
                                <span>新增待办</span>
                              </button>
                            )}
                          </div>
                        </td>
                        {/* 周报数据 */}
                        {organizedWeeklyData.map((monthData) =>
                          monthData.weeks.map((week, weekIdx) => {
                            const weekReport = week.reports.find(
                              (r) => r.project_id === project.id
                            );
                            return (
                              <td
                                key={`${monthData.month}-${weekIdx}`}
                                className="px-2 py-2.5 text-xs border-r border-b border-gray-200 min-w-[140px] bg-gray-50/50"
                              >
                                {weekReport ? (
                                  <div className="space-y-2">
                                    {/* 本周计划 */}
                                    <div className="bg-gradient-to-r from-blue-50 to-blue-100/50 border-l-4 border-blue-500 p-2.5 rounded-r shadow-sm hover:shadow transition-shadow">
                                      <div className="flex items-center gap-1.5 mb-1.5">
                                        <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 shadow-sm"></div>
                                        <div className="text-xs font-bold text-blue-800">
                                          本周计划
                                        </div>
                                      </div>
                                      <div className="text-xs text-gray-800 line-clamp-3 leading-relaxed pl-3.5">
                                        {weekReport.content_plan || '-'}
                                      </div>
                                    </div>

                                    {/* 本周成果 */}
                                    <div className="bg-gradient-to-r from-green-50 to-green-100/50 border-l-4 border-green-500 p-2.5 rounded-r shadow-sm hover:shadow transition-shadow">
                                      <div className="flex items-center gap-1.5 mb-1.5">
                                        <div className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0 shadow-sm"></div>
                                        <div className="text-xs font-bold text-green-800">
                                          本周成果
                                        </div>
                                      </div>
                                      <div className="text-xs text-gray-800 line-clamp-3 leading-relaxed pl-3.5">
                                        {weekReport.content_achievement || '-'}
                                      </div>
                                    </div>
                                  </div>
                                ) : (
                                  <span className="text-gray-400 text-center block">-</span>
                                )}
                              </td>
                            );
                          })
                        )}
                        {/* 里程碑数据 */}
                        <td className="px-2 py-2.5 text-xs text-center border-r border-b border-gray-200 bg-amber-50/30">
                          {projectMilestones['实施启动'] ? (
                            <div className="space-y-1">
                              <div className="font-semibold text-gray-900">
                                {formatDate(projectMilestones['实施启动'].target_date)}
                              </div>
                              <div
                                className={`text-xs font-medium px-1.5 py-0.5 rounded ${projectMilestones['实施启动'].status === 'completed' ? 'text-green-700 bg-green-100' : 'text-orange-700 bg-orange-100'}`}
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
                        <td className="px-2 py-2.5 text-xs text-center border-r border-b border-gray-200 bg-amber-50/30">
                          {projectMilestones['方案确认'] ? (
                            <div className="space-y-1">
                              <div className="font-semibold text-gray-900">
                                {formatDate(projectMilestones['方案确认'].target_date)}
                              </div>
                              <div
                                className={`text-xs font-medium px-1.5 py-0.5 rounded ${projectMilestones['方案确认'].status === 'completed' ? 'text-green-700 bg-green-100' : 'text-orange-700 bg-orange-100'}`}
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
                        <td className="px-2 py-2.5 text-xs text-center border-r border-b border-gray-200 bg-amber-50/30">
                          {projectMilestones['交付上线'] ? (
                            <div className="space-y-1">
                              <div className="font-semibold text-gray-900">
                                {formatDate(projectMilestones['交付上线'].target_date)}
                              </div>
                              <div
                                className={`text-xs font-medium px-1.5 py-0.5 rounded ${projectMilestones['交付上线'].status === 'completed' ? 'text-green-700 bg-green-100' : 'text-orange-700 bg-orange-100'}`}
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
                        <td className="px-2 py-2.5 text-xs text-center border-r border-b border-gray-200 bg-amber-50/30">
                          {projectMilestones['项目验收'] ? (
                            <div className="space-y-1">
                              <div className="font-semibold text-gray-900">
                                {formatDate(projectMilestones['项目验收'].target_date)}
                              </div>
                              <div
                                className={`text-xs font-medium px-1.5 py-0.5 rounded ${projectMilestones['项目验收'].status === 'completed' ? 'text-green-700 bg-green-100' : 'text-orange-700 bg-orange-100'}`}
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
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-0">
              {/* 第一行表头：基础信息和年份 */}
              <thead>
                <tr>
                  <th
                    rowSpan={2}
                    className="sticky left-0 z-20 px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300 shadow-sm"
                  >
                    序号
                  </th>
                  <th
                    rowSpan={2}
                    className="sticky left-[60px] z-10 px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300 shadow-sm"
                  >
                    <div className="flex items-center justify-center gap-1">
                      <span>项目名称</span>
                    </div>
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300"
                  >
                    项目编码
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300"
                  >
                    填报人
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300"
                  >
                    项目状态
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-gray-100 to-gray-50 border-r border-b border-gray-300"
                  >
                    项目阶段
                  </th>
                  <th
                    rowSpan={2}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-purple-100 to-purple-50 border-r border-b border-gray-300 min-w-[200px]"
                  >
                    <div className="flex items-center justify-center">
                      <span className="text-purple-900">待办及重点提示</span>
                    </div>
                  </th>
                  {organizedMonthlyData.map((yearData) => (
                    <th
                      key={yearData.year}
                      colSpan={yearData.months.length}
                      className="px-3 py-3 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-blue-100 to-blue-50 border-r border-b border-gray-300"
                    >
                      <div className="flex items-center justify-center">
                        <span className="text-blue-900">{yearData.yearLabel}</span>
                      </div>
                    </th>
                  ))}
                  <th
                    colSpan={4}
                    className="px-4 py-3.5 text-center text-xs font-semibold text-gray-800 bg-gradient-to-b from-amber-100 to-amber-50 border-r border-b border-gray-300"
                  >
                    <div className="flex items-center justify-center">
                      <span className="text-amber-900">重要里程碑</span>
                    </div>
                  </th>
                </tr>
                {/* 第二行表头：月份 */}
                <tr>
                  {organizedMonthlyData.map((yearData) =>
                    yearData.months.map((month, idx) => (
                      <th
                        key={`${yearData.year}-${month.month}-${idx}`}
                        className="px-2 py-2.5 text-center text-xs font-medium text-gray-700 bg-gradient-to-b from-blue-50 to-blue-100/50 border-r border-b border-gray-300"
                      >
                        <span className="font-semibold text-blue-900">{month.monthLabel}</span>
                      </th>
                    ))
                  )}
                  {/* 里程碑子列 */}
                  <th className="px-2 py-2.5 text-center text-xs font-medium text-gray-700 bg-gradient-to-b from-amber-50 to-amber-100/50 border-r border-b border-gray-300">
                    <span className="text-amber-900">实施启动</span>
                  </th>
                  <th className="px-2 py-2.5 text-center text-xs font-medium text-gray-700 bg-gradient-to-b from-amber-50 to-amber-100/50 border-r border-b border-gray-300">
                    <span className="text-amber-900">方案确认</span>
                  </th>
                  <th className="px-2 py-2.5 text-center text-xs font-medium text-gray-700 bg-gradient-to-b from-amber-50 to-amber-100/50 border-r border-b border-gray-300">
                    <span className="text-amber-900">交付上线</span>
                  </th>
                  <th className="px-2 py-2.5 text-center text-xs font-medium text-gray-700 bg-gradient-to-b from-amber-50 to-amber-100/50 border-r border-b border-gray-300">
                    <span className="text-amber-900">项目验收</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {uniqueProjects.length === 0 ? (
                  <tr>
                    <td
                      colSpan={100}
                      className="px-6 py-8 text-center text-gray-500 border-b border-gray-200"
                    >
                      <div className="flex flex-col items-center justify-center gap-2">
                        <span className="text-lg">暂无数据</span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  uniqueProjects.map((project, idx) => {
                    const projectMilestones = getProjectMilestones(project.id);
                    return (
                      <tr
                        key={project.id}
                        className="hover:bg-blue-50/30 transition-colors duration-150"
                      >
                        <td className="sticky left-0 z-10 px-4 py-3 text-center text-sm font-medium text-gray-900 bg-white border-r border-b border-gray-200 shadow-sm hover:bg-blue-50/30">
                          {idx + 1}
                        </td>
                        <td className="sticky left-[60px] z-10 px-4 py-3 text-sm font-medium text-gray-900 bg-white border-r border-b border-gray-200 shadow-sm hover:bg-blue-50/30">
                          {project.name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 border-r border-b border-gray-200">
                          {project.project_code || '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700 border-r border-b border-gray-200">
                          {project.reporter_name || <span className="text-gray-400">-</span>}
                        </td>
                        <td className="px-4 py-3 text-center border-r border-b border-gray-200">
                          <span
                            className={`inline-flex px-2.5 py-1 text-xs font-semibold rounded-full shadow-sm ${getStatusColor(project.status)}`}
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
                        <td className="px-4 py-3 text-sm text-gray-700 border-r border-b border-gray-200">
                          {getProjectPhase(project)}
                        </td>
                        {/* 待办及重点提示 */}
                        <td className="px-3 py-3 text-sm border-r border-b border-gray-200 bg-purple-50/30 min-w-[200px]">
                          <div className="space-y-2">
                            {/* 待办列表 */}
                            {(() => {
                              const projectTodos = todos[project.id] || [];
                              // 移除调试日志，避免控制台输出过多
                              return projectTodos.map((todo) => {
                                const isCompleted = todo.status === 'completed';
                                return (
                                  <div
                                    key={todo.id}
                                    className={`p-2 rounded-lg border-l-4 ${
                                      isCompleted
                                        ? 'bg-gray-100 border-gray-400 opacity-75'
                                        : todo.priority === 'high'
                                          ? 'bg-red-50 border-red-500'
                                          : 'bg-yellow-50 border-yellow-500'
                                    }`}
                                  >
                                    <div className="flex items-start justify-between gap-2">
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                          <div
                                            className={`text-xs font-medium ${
                                              isCompleted
                                                ? 'line-through text-gray-500'
                                                : 'text-gray-900'
                                            }`}
                                          >
                                            {todo.title}
                                          </div>
                                        </div>
                                      </div>
                                      {/* 只有自己创建的待办才显示删除按钮 */}
                                      {isCompleted && isTodoCreatedByMe(todo) && (
                                        <button
                                          onClick={() => handleDeleteTodo(todo.id, project.id)}
                                          className="text-red-500 hover:text-red-700 text-xs px-1.5 py-0.5 rounded hover:bg-red-100 transition-colors"
                                          title="删除待办"
                                        >
                                          删除
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                );
                              });
                            })()}

                            {/* 新增待办按钮 */}
                            {editingTodoProjectId === project.id ? (
                              <div className="space-y-2 p-2 bg-white border border-purple-300 rounded-lg">
                                <input
                                  type="text"
                                  value={newTodoTitle}
                                  onChange={(e) => setNewTodoTitle(e.target.value)}
                                  placeholder="输入待办内容..."
                                  className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                                  autoFocus
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                      handleCreateTodo(project.id, project.reporter_id);
                                    } else if (e.key === 'Escape') {
                                      setEditingTodoProjectId(null);
                                      setNewTodoTitle('');
                                    }
                                  }}
                                />
                                <div className="flex items-center gap-2">
                                  <button
                                    onClick={() =>
                                      handleCreateTodo(project.id, project.reporter_id)
                                    }
                                    className="flex-1 px-2 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
                                  >
                                    保存
                                  </button>
                                  <button
                                    onClick={() => {
                                      setEditingTodoProjectId(null);
                                      setNewTodoTitle('');
                                    }}
                                    className="flex-1 px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                                  >
                                    取消
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <button
                                onClick={() => {
                                  setEditingTodoProjectId(project.id);
                                  setNewTodoTitle('');
                                }}
                                className="w-full px-2 py-1.5 text-xs text-purple-700 bg-purple-100 border border-purple-300 rounded-lg hover:bg-purple-200 transition-colors flex items-center justify-center gap-1"
                              >
                                <span>+</span>
                                <span>新增待办</span>
                              </button>
                            )}
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
                                className="px-2 py-2.5 text-xs border-r border-b border-gray-200 min-w-[140px] bg-gray-50/50"
                              >
                                {monthReport ? (
                                  <div className="space-y-2">
                                    <div className="bg-gradient-to-r from-green-50 to-green-100/50 border-l-4 border-green-500 p-2 rounded-r shadow-sm">
                                      <div className="font-semibold text-green-800 mb-1">成果:</div>
                                      <div className="line-clamp-2 text-gray-800 text-xs leading-relaxed">
                                        {monthReport.achievements || '-'}
                                      </div>
                                    </div>
                                    {monthReport.challenges && (
                                      <div className="bg-gradient-to-r from-red-50 to-red-100/50 border-l-4 border-red-500 p-2 rounded-r shadow-sm">
                                        <div className="font-semibold text-red-800 mb-1">挑战:</div>
                                        <div className="line-clamp-1 text-red-700 text-xs leading-relaxed">
                                          {monthReport.challenges}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-gray-400 text-center block">-</span>
                                )}
                              </td>
                            );
                          })
                        )}
                        {/* 里程碑数据 */}
                        <td className="px-2 py-2.5 text-xs text-center border-r border-b border-gray-200 bg-amber-50/30">
                          {projectMilestones['实施启动'] ? (
                            <div className="space-y-1">
                              <div className="font-semibold text-gray-900">
                                {formatDate(projectMilestones['实施启动'].target_date)}
                              </div>
                              <div
                                className={`text-xs font-medium px-1.5 py-0.5 rounded ${projectMilestones['实施启动'].status === 'completed' ? 'text-green-700 bg-green-100' : 'text-orange-700 bg-orange-100'}`}
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
                        <td className="px-2 py-2.5 text-xs text-center border-r border-b border-gray-200 bg-amber-50/30">
                          {projectMilestones['方案确认'] ? (
                            <div className="space-y-1">
                              <div className="font-semibold text-gray-900">
                                {formatDate(projectMilestones['方案确认'].target_date)}
                              </div>
                              <div
                                className={`text-xs font-medium px-1.5 py-0.5 rounded ${projectMilestones['方案确认'].status === 'completed' ? 'text-green-700 bg-green-100' : 'text-orange-700 bg-orange-100'}`}
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
                        <td className="px-2 py-2.5 text-xs text-center border-r border-b border-gray-200 bg-amber-50/30">
                          {projectMilestones['交付上线'] ? (
                            <div className="space-y-1">
                              <div className="font-semibold text-gray-900">
                                {formatDate(projectMilestones['交付上线'].target_date)}
                              </div>
                              <div
                                className={`text-xs font-medium px-1.5 py-0.5 rounded ${projectMilestones['交付上线'].status === 'completed' ? 'text-green-700 bg-green-100' : 'text-orange-700 bg-orange-100'}`}
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
                        <td className="px-2 py-2.5 text-xs text-center border-r border-b border-gray-200 bg-amber-50/30">
                          {projectMilestones['项目验收'] ? (
                            <div className="space-y-1">
                              <div className="font-semibold text-gray-900">
                                {formatDate(projectMilestones['项目验收'].target_date)}
                              </div>
                              <div
                                className={`text-xs font-medium px-1.5 py-0.5 rounded ${projectMilestones['项目验收'].status === 'completed' ? 'text-green-700 bg-green-100' : 'text-orange-700 bg-orange-100'}`}
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
    </div>
  );
}

