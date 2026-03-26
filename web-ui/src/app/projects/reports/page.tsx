'use client';

import ErrorMessage from '@/components/ErrorMessage';
import { apiGatewayClient } from '@/lib/api/client';
import { getAccessToken, isAuthenticated } from '@/lib/auth';
import {
  Bot,
  Calendar,
  CheckCircle2,
  Download,
  FileText,
  Filter,
  Folder,
  Loader2,
  Sparkles,
  XCircle
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface Project {
  id: string;
  name: string;
  project_code?: string;
}

interface ReportSummary {
  id: string;
  project_ids: string[];
  report_type: 'weekly' | 'monthly';
  period: string;
  summary: string;
  created_at: string;
  status: 'pending' | 'completed' | 'failed';
}

export default function ReportsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjects, setSelectedProjects] = useState<string[]>([]);
  const [reportType, setReportType] = useState<'weekly' | 'monthly'>('weekly');
  const [selectedWeek, setSelectedWeek] = useState('');
  const [selectedMonth, setSelectedMonth] = useState('');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear().toString());
  const [generating, setGenerating] = useState(false);
  const [summary, setSummary] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [agentId, setAgentId] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    fetchProjects();
    findOrCreateAgent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchProjects = async () => {
    try {
      const data = await apiGatewayClient.get<{ items: Project[] }>('/api/v1/projects?limit=1000');
      setProjects(data.items || []);
    } catch (error: any) {
      console.error('获取项目列表失败:', error);
      if (error?.statusCode === 401) {
        router.push('/login');
      }
    }
  };

  // 查找或创建智能体
  const findOrCreateAgent = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      // 先查找是否已存在
      const listResponse = await fetch(`${apiUrl}/api/v1/agents`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (listResponse.ok) {
        const agents = await listResponse.json();
        const existingAgent = Array.isArray(agents)
          ? agents.find((a: any) => a.name === '项目周月报告智能体')
          : agents.agents?.find((a: any) => a.name === '项目周月报告智能体');

        if (existingAgent) {
          setAgentId(existingAgent.id);
          return;
        }
      }

      // 如果不存在，创建智能体
      const createResponse = await fetch(`${apiUrl}/api/v1/agents`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: '项目周月报告智能体',
          description: '智能生成多个项目的周报和月报总结报告，支持批量分析和汇总',
          capabilities: ['document_processing', 'data_analysis', 'task_planning'],
          status: 'active',
          system_prompt: `你是一个专业的项目报告分析智能体，专门负责生成项目周报和月报的总结报告。

你的主要职责是：
1. 分析多个项目的周报或月报数据
2. 提取关键信息，包括进度、完成情况、风险、问题等
3. 生成结构化的总结报告，包括：
   - 总体概况
   - 各项目进展情况
   - 关键成果和亮点
   - 存在的问题和风险
   - 下一步计划建议

请确保报告内容：
- 准确、客观、专业
- 结构清晰，便于阅读
- 突出重点和关键信息
- 提供有价值的分析和建议`,
          config: {
            model: 'deepseek-chat', // 使用最新的 DeepSeek Chat 模型
            temperature: 0.5, // 平衡效率和准确性（参考SSH智能体默认0.7，报告生成需要更准确，设为0.5）
            max_tokens: 4000, // 优化token数（参考SSH智能体默认2048-4096，报告生成需要更长，设为4000）
            timeout: 300, // 增加超时时间到300秒（参考SSH智能体默认300秒，确保有足够时间生成完整报告）
          },
        }),
      });

      if (createResponse.ok) {
        const newAgent = await createResponse.json();
        setAgentId(newAgent.id);
      } else {
        console.error('创建智能体失败:', await createResponse.text());
      }
    } catch (error) {
      console.error('查找或创建智能体失败:', error);
    }
  };

  // 生成周报日期选项
  const generateWeekOptions = () => {
    const options: string[] = [];
    const currentYear = new Date().getFullYear();
    const currentDate = new Date();

    // 生成当前年份的所有周
    for (let week = 1; week <= 52; week++) {
      const weekStart = new Date(currentYear, 0, 1 + (week - 1) * 7);
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekEnd.getDate() + 6);

      // 只显示当前周及之前的周
      if (weekEnd <= currentDate) {
        const weekStr = `第${week}周 (${weekStart.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })} - ${weekEnd.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })})`;
        options.push(`${currentYear}-W${week.toString().padStart(2, '0')}`);
      }
    }

    return options.reverse(); // 最新的在前
  };

  // 生成月份选项
  const generateMonthOptions = () => {
    const options: string[] = [];
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1;

    for (let month = 1; month <= currentMonth; month++) {
      options.push(`${currentYear}-${month.toString().padStart(2, '0')}`);
    }

    return options.reverse(); // 最新的在前
  };

  const handleProjectToggle = (projectId: string) => {
    setSelectedProjects((prev) =>
      prev.includes(projectId) ? prev.filter((id) => id !== projectId) : [...prev, projectId]
    );
  };

  const handleSelectAll = () => {
    if (selectedProjects.length === projects.length) {
      setSelectedProjects([]);
    } else {
      setSelectedProjects(projects.map((p) => p.id));
    }
  };

  const handleGenerate = async () => {
    if (selectedProjects.length === 0) {
      setError('请至少选择一个项目');
      return;
    }

    if (reportType === 'weekly' && !selectedWeek) {
      setError('请选择周报周期');
      return;
    }

    if (reportType === 'monthly' && !selectedMonth) {
      setError('请选择月份');
      return;
    }

    if (!agentId) {
      setError('智能体未就绪，请稍后重试');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      setSuccess(null);
      setSummary('');

      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      // 获取选定项目的周报或月报数据
      const reportData: any[] = [];

      for (const projectId of selectedProjects) {
        if (reportType === 'weekly') {
          // 获取周报
          const [year, week] = selectedWeek.split('-W');
          const weekNum = parseInt(week);
          const weekStart = new Date(parseInt(year), 0, 1 + (weekNum - 1) * 7);
          const weekEnd = new Date(weekStart);
          weekEnd.setDate(weekEnd.getDate() + 6);

          try {
            const response = await apiGatewayClient.get<{ items: any[] }>(
              `/api/v1/weekly-reports?project_id=${projectId}&week_start_date=${weekStart.toISOString().split('T')[0]}&week_end_date=${weekEnd.toISOString().split('T')[0]}`
            );
            if (response.items && response.items.length > 0) {
              reportData.push({
                project_id: projectId,
                project_name: projects.find((p) => p.id === projectId)?.name || '未知项目',
                reports: response.items,
              });
            }
          } catch (error) {
            console.error(`获取项目 ${projectId} 的周报失败:`, error);
          }
        } else {
          // 获取月报
          try {
            const response = await apiGatewayClient.get<{ items: any[] }>(
              `/api/v1/monthly-reports?project_id=${projectId}&month=${selectedMonth}`
            );
            if (response.items && response.items.length > 0) {
              reportData.push({
                project_id: projectId,
                project_name: projects.find((p) => p.id === projectId)?.name || '未知项目',
                reports: response.items,
              });
            }
          } catch (error) {
            console.error(`获取项目 ${projectId} 的月报失败:`, error);
          }
        }
      }

      if (reportData.length === 0) {
        setError('所选项目在指定时间段内没有报告数据');
        setGenerating(false);
        return;
      }

      // 构建智能体提示词
      const period = reportType === 'weekly' ? selectedWeek : selectedMonth;
      const projectNames = reportData.map((d) => d.project_name).join('、');
      const prompt = `请分析以下${reportType === 'weekly' ? '周报' : '月报'}数据，生成一份综合总结报告。

报告周期：${period}
涉及项目：${projectNames}（共${reportData.length}个项目）

报告数据：
${JSON.stringify(reportData, null, 2)}

请生成一份结构化的总结报告，包括：
1. 总体概况
2. 各项目进展情况
3. 关键成果和亮点
4. 存在的问题和风险
5. 下一步计划建议

报告要求：
- 内容准确、客观、专业
- 结构清晰，便于阅读
- 突出重点和关键信息
- 提供有价值的分析和建议`;

      // 调用智能体，添加超时控制
      // 参考SSH智能体的超时配置（300秒），前端超时设置为350秒（5分50秒），给后端留出缓冲时间
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 350000); // 5分50秒超时

      try {
        const executeResponse = await fetch(`${apiUrl}/api/v1/agents/${agentId}/execute`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            task: prompt,
            context: {
              report_type: reportType,
              period: period,
              project_count: reportData.length,
            },
          }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (executeResponse.ok) {
          const result = await executeResponse.json();
          setSummary(result.response || result.result || '报告生成成功');
          setSuccess('报告生成成功！');
        } else {
          const errorData = await executeResponse.json().catch(() => ({ detail: '生成报告失败' }));
          // 安全地格式化错误消息
          let errorMessage = '生成报告失败';
          if (errorData.detail) {
            if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail;
            } else if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail
                .map((err: any) => {
                  if (typeof err === 'string') return err;
                  if (err.msg) return err.msg;
                  if (err.message) return err.message;
                  return JSON.stringify(err);
                })
                .join('; ');
            } else if (typeof errorData.detail === 'object') {
              errorMessage = errorData.detail.message || errorData.detail.msg || '生成报告失败';
            }
          }
          throw new Error(errorMessage);
        }
      } catch (error: any) {
        clearTimeout(timeoutId);
        console.error('生成报告失败:', error);

        // 处理不同类型的错误
        if (error.name === 'AbortError') {
          setError('请求超时（超过5分50秒），报告生成可能需要更长时间。请减少项目数量或缩短报告周期后重试。');
        } else if (error.message?.includes('Failed to fetch') || error.message?.includes('ERR_EMPTY_RESPONSE')) {
          setError('网络连接失败或服务器响应超时。请检查网络连接或稍后重试。如果问题持续，可能是服务器负载过高，建议减少项目数量。');
        } else {
          setError(error?.message || '生成报告失败，请稍后重试');
        }
      } finally {
        setGenerating(false);
      }
    } catch (error: any) {
      console.error('生成报告过程出错:', error);
      setError('生成报告失败，请稍后重试');
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!summary) return;

    const period = reportType === 'weekly' ? selectedWeek : selectedMonth;
    const projectNames = selectedProjects
      .map((id) => projects.find((p) => p.id === id)?.name)
      .filter(Boolean)
      .join('、');

    const content = `项目${reportType === 'weekly' ? '周报' : '月报'}总结报告

报告周期：${period}
涉及项目：${projectNames}（共${selectedProjects.length}个项目）
生成时间：${new Date().toLocaleString('zh-CN')}

${summary}`;

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `项目${reportType === 'weekly' ? '周报' : '月报'}总结_${period}_${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 页面标题 - 增强美化 */}
        <div className="mb-8">
          <div className="relative bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 rounded-3xl shadow-2xl overflow-hidden p-8 lg:p-10">
            {/* 背景装饰 - 增强 */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl animate-pulse"></div>
              <div className="absolute bottom-0 left-0 w-64 h-64 bg-white rounded-full blur-3xl"></div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-white rounded-full blur-3xl"></div>
            </div>
            {/* 网格背景 */}
            <div className="absolute inset-0 opacity-5" style={{
              backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
              backgroundSize: '50px 50px'
            }}></div>

            <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div className="flex items-center gap-5">
                <div className="relative p-5 bg-white/20 backdrop-blur-md rounded-2xl border-2 border-white/30 shadow-2xl transform hover:scale-105 transition-transform duration-300">
                  <FileText className="w-12 h-12 text-white" />
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-400 rounded-full animate-ping"></div>
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-400 rounded-full"></div>
                </div>
                <div>
                  <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-white mb-3 tracking-tight">
                    报告管理
                  </h1>
                  <p className="text-blue-100 text-lg md:text-xl font-medium flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-yellow-300" />
                    使用AI智能体生成多项目周报和月报总结报告
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="px-5 py-3 bg-white/20 backdrop-blur-md rounded-xl border-2 border-white/30 shadow-lg hover:bg-white/30 transition-all">
                  <div className="flex items-center gap-2">
                    <Bot className="w-6 h-6 text-white" />
                    <span className="text-white font-bold text-lg">AI智能生成</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 错误和成功提示 - 增强美化 */}
        <ErrorMessage message={error} type="error" onClose={() => setError(null)} />
        {success && (
          <div className="mb-6 p-6 bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50 border-2 border-green-300 rounded-2xl shadow-xl flex items-center gap-4 animate-fade-in backdrop-blur-sm">
            <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl shadow-lg">
              <CheckCircle2 className="w-7 h-7 text-white" />
            </div>
            <span className="text-green-800 font-bold text-lg flex-1">{success}</span>
            <button
              onClick={() => setSuccess(null)}
              className="p-2.5 text-green-600 hover:text-green-800 hover:bg-green-100 rounded-xl transition-all hover:scale-110"
            >
              <XCircle className="w-6 h-6" />
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：配置面板 - 增强美化 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-3xl shadow-2xl border-2 border-gray-200 overflow-hidden hover:shadow-3xl transition-shadow duration-300">
              {/* 顶部装饰条 - 增强 */}
              <div className="h-3 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
              </div>

              <div className="p-6 lg:p-8">
                <div className="flex items-center gap-4 mb-8">
                  <div className="relative p-4 bg-gradient-to-br from-blue-100 via-indigo-100 to-purple-100 rounded-2xl shadow-lg border-2 border-blue-200">
                    <Filter className="w-7 h-7 text-blue-600" />
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                  </div>
                  <div>
                    <h2 className="text-2xl lg:text-3xl font-extrabold text-gray-900">生成配置</h2>
                    <p className="text-sm text-gray-600 mt-1.5 font-medium">选择项目和报告周期</p>
                  </div>
                </div>

              {/* 智能体状态 - 增强美化 */}
              <div className="mb-6 p-6 bg-gradient-to-br from-purple-50 via-indigo-50 to-pink-50 rounded-2xl border-2 border-purple-300 shadow-xl relative overflow-hidden">
                {/* 背景装饰 */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-purple-200/30 rounded-full blur-2xl"></div>
                <div className="relative">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="relative p-3 bg-gradient-to-br from-purple-500 via-indigo-600 to-pink-600 rounded-xl shadow-lg border-2 border-purple-400">
                      <Bot className="w-6 h-6 text-white" />
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
                    </div>
                    <div className="flex-1">
                      <span className="font-extrabold text-gray-900 block text-lg">项目周月报告智能体</span>
                      <span className="text-xs text-gray-600 font-medium">AI智能分析引擎</span>
                    </div>
                  </div>
                  {agentId ? (
                    <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-green-100 to-emerald-100 rounded-xl border-2 border-green-300 shadow-md">
                      <div className="p-1.5 bg-green-500 rounded-lg">
                        <CheckCircle2 className="w-5 h-5 text-white" />
                      </div>
                      <span className="text-sm font-bold text-green-800">已就绪，可以生成报告</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-yellow-100 to-amber-100 rounded-xl border-2 border-yellow-300 shadow-md">
                      <div className="p-1.5 bg-yellow-500 rounded-lg">
                        <Loader2 className="w-5 h-5 text-white animate-spin" />
                      </div>
                      <span className="text-sm font-bold text-yellow-800">初始化中，请稍候...</span>
                    </div>
                  )}
                </div>
              </div>

              {/* 报告类型选择 - 增强美化 */}
              <div className="mb-6">
                <label className="block text-sm font-extrabold text-gray-800 mb-4 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-600" />
                  <span className="text-base">报告类型</span>
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setReportType('weekly')}
                    className={`p-6 rounded-2xl border-2 transition-all duration-300 shadow-lg hover:shadow-2xl transform ${
                      reportType === 'weekly'
                        ? 'border-blue-500 bg-gradient-to-br from-blue-50 via-blue-100 to-indigo-50 text-blue-700 font-extrabold shadow-xl scale-105 ring-4 ring-blue-200'
                        : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300 hover:bg-blue-50 hover:scale-102'
                    }`}
                  >
                    <div className="flex flex-col items-center gap-3">
                      <div className={`p-3 rounded-xl shadow-md ${reportType === 'weekly' ? 'bg-gradient-to-br from-blue-400 to-blue-600' : 'bg-gray-100'}`}>
                        <Calendar className={`w-7 h-7 ${reportType === 'weekly' ? 'text-white' : 'text-gray-500'}`} />
                      </div>
                      <div className="font-bold text-base">周报</div>
                    </div>
                  </button>
                  <button
                    onClick={() => setReportType('monthly')}
                    className={`p-6 rounded-2xl border-2 transition-all duration-300 shadow-lg hover:shadow-2xl transform ${
                      reportType === 'monthly'
                        ? 'border-purple-500 bg-gradient-to-br from-purple-50 via-purple-100 to-pink-50 text-purple-700 font-extrabold shadow-xl scale-105 ring-4 ring-purple-200'
                        : 'border-gray-200 bg-white text-gray-700 hover:border-purple-300 hover:bg-purple-50 hover:scale-102'
                    }`}
                  >
                    <div className="flex flex-col items-center gap-3">
                      <div className={`p-3 rounded-xl shadow-md ${reportType === 'monthly' ? 'bg-gradient-to-br from-purple-400 to-purple-600' : 'bg-gray-100'}`}>
                        <Calendar className={`w-7 h-7 ${reportType === 'monthly' ? 'text-white' : 'text-gray-500'}`} />
                      </div>
                      <div className="font-bold text-base">月报</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* 时间选择 - 美化 */}
              <div className="mb-6">
                <label className="block text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-indigo-600" />
                  <span>{reportType === 'weekly' ? '选择周' : '选择月份'}</span>
                </label>
                {reportType === 'weekly' ? (
                  <div className="relative">
                    <select
                      value={selectedWeek}
                      onChange={(e) => setSelectedWeek(e.target.value)}
                      className="w-full px-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 font-medium shadow-sm hover:border-gray-300 transition-all appearance-none cursor-pointer"
                    >
                      <option value="">请选择周</option>
                      {generateWeekOptions().map((week) => {
                        const [year, weekNum] = week.split('-W');
                        const weekStart = new Date(parseInt(year), 0, 1 + (parseInt(weekNum) - 1) * 7);
                        const weekEnd = new Date(weekStart);
                        weekEnd.setDate(weekEnd.getDate() + 6);
                        return (
                          <option key={week} value={week}>
                            {week} ({weekStart.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })} -{' '}
                            {weekEnd.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })})
                          </option>
                        );
                      })}
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                      <Calendar className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                ) : (
                  <div className="relative">
                    <select
                      value={selectedMonth}
                      onChange={(e) => setSelectedMonth(e.target.value)}
                      className="w-full px-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white text-gray-900 font-medium shadow-sm hover:border-gray-300 transition-all appearance-none cursor-pointer"
                    >
                      <option value="">请选择月份</option>
                      {generateMonthOptions().map((month) => {
                        const [year, mon] = month.split('-');
                        return (
                          <option key={month} value={month}>
                            {year}年{parseInt(mon)}月
                          </option>
                        );
                      })}
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                      <Calendar className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                )}
              </div>

              {/* 项目选择 - 美化 */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-bold text-gray-700 flex items-center gap-2">
                    <Folder className="w-4 h-4 text-indigo-600" />
                    <span>选择项目</span>
                  </label>
                  <button
                    onClick={handleSelectAll}
                    className="px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 font-semibold bg-blue-50 hover:bg-blue-100 rounded-lg transition-all"
                  >
                    {selectedProjects.length === projects.length ? '取消全选' : '全选'}
                  </button>
                </div>
                <div className="max-h-64 overflow-y-auto border-2 border-gray-200 rounded-xl p-3 space-y-2 bg-gray-50/50">
                  {projects.map((project) => (
                    <label
                      key={project.id}
                      className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200 ${
                        selectedProjects.includes(project.id)
                          ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 shadow-md'
                          : 'bg-white border-2 border-gray-200 hover:border-blue-200 hover:bg-blue-50/50 hover:shadow-sm'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedProjects.includes(project.id)}
                        onChange={() => handleProjectToggle(project.id)}
                        className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-gray-900 truncate">{project.name}</div>
                        {project.project_code && (
                          <div className="text-xs text-gray-500 font-mono mt-0.5">{project.project_code}</div>
                        )}
                      </div>
                      {selectedProjects.includes(project.id) && (
                        <CheckCircle2 className="w-5 h-5 text-blue-600 flex-shrink-0" />
                      )}
                    </label>
                  ))}
                </div>
                <div className="mt-3 px-3 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
                  <div className="text-sm text-gray-700 flex items-center justify-between">
                    <span>已选择项目</span>
                    <span className="font-bold text-blue-600 text-lg">{selectedProjects.length}</span>
                  </div>
                </div>
              </div>

              {/* 生成按钮 - 增强美化 */}
              <button
                onClick={handleGenerate}
                disabled={generating || !agentId || selectedProjects.length === 0}
                className="w-full py-5 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white rounded-2xl font-extrabold shadow-2xl hover:shadow-3xl hover:scale-[1.03] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-2xl flex items-center justify-center gap-3 text-lg relative overflow-hidden group border-2 border-white/20"
              >
                {/* 按钮背景动画 - 增强 */}
                <div className="absolute inset-0 bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-700 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
                <div className="relative flex items-center gap-3">
                  {generating ? (
                    <>
                      <Loader2 className="w-7 h-7 animate-spin" />
                      <span className="text-xl">AI正在生成中...</span>
                    </>
                  ) : (
                    <>
                      <div className="p-2 bg-white/20 rounded-xl shadow-lg">
                        <Sparkles className="w-6 h-6" />
                      </div>
                      <span className="text-xl">生成总结报告</span>
                    </>
                  )}
                </div>
              </button>
              </div>
            </div>
          </div>

          {/* 右侧：报告展示 - 增强美化 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-3xl shadow-2xl border-2 border-gray-200 overflow-hidden hover:shadow-3xl transition-shadow duration-300">
              {/* 顶部装饰条 - 增强 */}
              <div className="h-3 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
              </div>

              <div className="p-6 lg:p-8">
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-4">
                    <div className="relative p-4 bg-gradient-to-br from-indigo-100 via-purple-100 to-pink-100 rounded-2xl shadow-lg border-2 border-indigo-200">
                      <FileText className="w-7 h-7 text-indigo-600" />
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-indigo-500 rounded-full animate-pulse"></div>
                    </div>
                    <div>
                      <h2 className="text-2xl lg:text-3xl font-extrabold text-gray-900">总结报告</h2>
                      <p className="text-sm text-gray-600 mt-1.5 font-medium">AI智能生成的综合分析报告</p>
                    </div>
                  </div>
                  {summary && (
                    <button
                      onClick={handleDownload}
                      className="px-6 py-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:via-indigo-700 hover:to-purple-700 transition-all shadow-xl hover:shadow-2xl hover:scale-105 flex items-center gap-2 font-bold text-base border-2 border-white/20"
                    >
                      <Download className="w-5 h-5" />
                      <span>下载报告</span>
                    </button>
                  )}
                </div>

                {summary ? (
                  <div className="prose max-w-none">
                    <div className="bg-gradient-to-br from-gray-50 via-blue-50/40 to-indigo-50/30 rounded-3xl p-8 lg:p-10 border-2 border-gray-300 shadow-inner relative overflow-hidden">
                      {/* 背景装饰 */}
                      <div className="absolute top-0 right-0 w-64 h-64 bg-blue-100/20 rounded-full blur-3xl"></div>
                      <div className="absolute bottom-0 left-0 w-48 h-48 bg-indigo-100/20 rounded-full blur-3xl"></div>
                      <div className="relative">
                        <div className="whitespace-pre-wrap text-gray-800 leading-relaxed text-base lg:text-lg font-medium">
                          {summary}
                        </div>
                      </div>
                    </div>

                    {/* 报告信息卡片 - 增强美化 */}
                    <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-5">
                      <div className="bg-gradient-to-br from-blue-50 via-blue-100 to-indigo-50 rounded-2xl p-5 border-2 border-blue-300 shadow-lg hover:shadow-xl hover:scale-105 transition-all">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="p-2 bg-blue-500 rounded-lg">
                            <FileText className="w-5 h-5 text-white" />
                          </div>
                          <div className="text-xs text-gray-600 font-bold uppercase tracking-wide">报告类型</div>
                        </div>
                        <div className="text-2xl font-extrabold text-blue-700">
                          {reportType === 'weekly' ? '周报' : '月报'}
                        </div>
                      </div>
                      <div className="bg-gradient-to-br from-purple-50 via-purple-100 to-pink-50 rounded-2xl p-5 border-2 border-purple-300 shadow-lg hover:shadow-xl hover:scale-105 transition-all">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="p-2 bg-purple-500 rounded-lg">
                            <Folder className="w-5 h-5 text-white" />
                          </div>
                          <div className="text-xs text-gray-600 font-bold uppercase tracking-wide">涉及项目</div>
                        </div>
                        <div className="text-2xl font-extrabold text-purple-700">
                          {selectedProjects.length} 个
                        </div>
                      </div>
                      <div className="bg-gradient-to-br from-green-50 via-emerald-100 to-teal-50 rounded-2xl p-5 border-2 border-green-300 shadow-lg hover:shadow-xl hover:scale-105 transition-all">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="p-2 bg-green-500 rounded-lg">
                            <Calendar className="w-5 h-5 text-white" />
                          </div>
                          <div className="text-xs text-gray-600 font-bold uppercase tracking-wide">生成时间</div>
                        </div>
                        <div className="text-2xl font-extrabold text-green-700">
                          {new Date().toLocaleDateString('zh-CN')}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-24 lg:py-32 text-center">
                    <div className="relative mb-8">
                      <div className="p-10 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 rounded-3xl shadow-2xl border-2 border-blue-300 transform hover:scale-105 transition-transform duration-300">
                        <FileText className="w-24 h-24 text-blue-300" />
                      </div>
                      <div className="absolute -top-3 -right-3 p-3 bg-gradient-to-br from-yellow-400 via-orange-500 to-pink-500 rounded-full shadow-2xl animate-pulse">
                        <Sparkles className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <h3 className="text-3xl font-extrabold text-gray-900 mb-3">等待生成报告</h3>
                    <p className="text-gray-600 text-lg max-w-lg leading-relaxed mb-6">
                      请选择项目和报告周期，然后点击"生成总结报告"按钮，AI智能体将为您生成综合分析报告
                    </p>
                    <div className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border-2 border-blue-200 shadow-md">
                      <Bot className="w-5 h-5 text-blue-600" />
                      <span className="text-sm font-bold text-gray-700">使用AI智能体自动分析和汇总</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

