'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useEffect, useState } from 'react';
import { getUsers } from '@/lib/api/admin';
import { getWorkflowExecutionStats } from '@/lib/api/monitoring';
import { getTools } from '@/lib/api/tools';
import { Users, GitBranch, Wrench, Zap, FileText } from 'lucide-react';

interface DashboardStats {
  totalUsers: number;
  activeWorkflows: number;
  toolCount: number;
  todayExecutions: number;
}

export default function AdminDashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalUsers: 0,
    activeWorkflows: 0,
    toolCount: 0,
    todayExecutions: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);

        // 获取用户统计（需要管理员权限）
        let totalUsers = 0;
        try {
          const usersResponse = await getUsers({ page: 1, page_size: 1 });
          totalUsers = usersResponse.total || 0;
        } catch (error: any) {
          // 如果是权限错误（403），静默处理，使用默认值0
          if (error?.statusCode === 403) {
            console.warn('User does not have permission to view user statistics');
          } else {
            console.error('Failed to load user stats:', error);
          }
        }

        // 获取工作流统计
        let activeWorkflows = 0;
        let todayExecutions = 0;
        try {
          const workflowStats = await getWorkflowExecutionStats();
          activeWorkflows = workflowStats.workflow_execution_stats?.length || 0;
          todayExecutions =
            workflowStats.workflow_execution_stats?.reduce(
              (sum, stat) => sum + (stat.total_executions || 0),
              0
            ) || 0;
        } catch (error: any) {
          // 如果是权限错误（403），静默处理
          if (error?.statusCode === 403) {
            console.warn('User does not have permission to view workflow statistics');
          } else {
            console.error('Failed to load workflow stats:', error);
          }
        }

        // 获取工具统计
        let toolCount = 0;
        try {
          const toolsResponse = await getTools();
          toolCount = Array.isArray(toolsResponse) ? toolsResponse.length : 0;
        } catch (error: any) {
          // 如果是权限错误（403），静默处理
          if (error?.statusCode === 403) {
            console.warn('User does not have permission to view tool statistics');
          } else {
            console.error('Failed to load tools:', error);
          }
        }

        setStats({
          totalUsers,
          activeWorkflows,
          toolCount,
          todayExecutions,
        });
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const displayStats = [
    { name: '总用户数', value: stats.totalUsers.toLocaleString(), change: '', icon: Users },
    { name: '活跃工作流', value: stats.activeWorkflows.toString(), change: '', icon: GitBranch },
    { name: '工具数量', value: stats.toolCount.toString(), change: '', icon: Wrench },
    { name: '今日执行', value: stats.todayExecutions.toLocaleString(), change: '', icon: Zap },
  ];

  const statColors = ['primary', 'secondary', 'accent', 'primary'] as const;

  return (
    <div className="space-y-6 p-6">
      {/* 欢迎横幅 */}
      <div className="gradient-primary rounded-lg shadow-elevated p-6 text-white animate-fade-in">
        <h1 className="text-2xl font-title font-bold mb-2">
          欢迎回来，{user?.username || '用户'}！
        </h1>
        <p className="text-white/90 font-body">这里是您的管理仪表板，可以查看系统概览和统计数据</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {loading ? (
          <div className="col-span-4 text-center py-8 text-mutedForeground animate-pulse-slow">
            加载中...
          </div>
        ) : (
          displayStats.map((stat, index) => {
            const IconComponent = typeof stat.icon === 'string' ? null : stat.icon;
            const color = statColors[index % statColors.length];
            const useGradient = index === 0; // 第一个卡片使用渐变

            return (
              <div
                key={stat.name}
                className={`
                  card-elevated rounded-lg p-6 border
                  ${useGradient ? `gradient-${color} text-white` : `bg-card border-${color}/20`}
                  animate-fade-in
                `}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p
                      className={`text-sm font-medium mb-2 ${useGradient ? 'text-white/90' : 'text-mutedForeground'}`}
                    >
                      {stat.name}
                    </p>
                    <p
                      className={`text-3xl font-title font-bold ${useGradient ? 'text-white' : `text-${color}`}`}
                    >
                      {stat.value}
                    </p>
                    {stat.change && (
                      <p
                        className={`text-sm mt-1 ${useGradient ? 'text-white/80' : 'text-secondary'}`}
                      >
                        {stat.change}
                      </p>
                    )}
                  </div>
                  <div className={useGradient ? 'text-white/80' : `text-${color} opacity-80`}>
                    {IconComponent && <IconComponent className="w-12 h-12" />}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 快速操作 */}
      <div className="card-elevated rounded-lg p-6 bg-card border border-border animate-slide-in">
        <h2 className="text-lg font-title font-bold text-foreground mb-4">快速操作</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <a
            href="/workflow-designer"
            className="flex items-center gap-3 p-4 border border-border rounded-lg bg-card hover:bg-primary/5 hover:border-primary/30 transition-all duration-300 group"
          >
            <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
              <GitBranch className="w-6 h-6" />
            </div>
            <div>
              <p className="font-medium text-foreground font-body">创建工作流</p>
              <p className="text-sm text-mutedForeground">设计新的业务流程</p>
            </div>
          </a>
          <a
            href="/admin/users"
            className="flex items-center gap-3 p-4 border border-border rounded-lg bg-card hover:bg-secondary/5 hover:border-secondary/30 transition-all duration-300 group"
          >
            <div className="p-2 rounded-lg bg-secondary/10 text-secondary group-hover:bg-secondary group-hover:text-white transition-colors">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <p className="font-medium text-foreground font-body">管理用户</p>
              <p className="text-sm text-mutedForeground">查看和管理用户</p>
            </div>
          </a>
          <a
            href="/admin/tools"
            className="flex items-center gap-3 p-4 border border-border rounded-lg bg-card hover:bg-accent/5 hover:border-accent/30 transition-all duration-300 group"
          >
            <div className="p-2 rounded-lg bg-accent/10 text-accent group-hover:bg-accent group-hover:text-white transition-colors">
              <Wrench className="w-6 h-6" />
            </div>
            <div>
              <p className="font-medium text-foreground font-body">管理工具</p>
              <p className="text-sm text-mutedForeground">配置MCP工具</p>
            </div>
          </a>
        </div>
      </div>

      {/* 最近活动 */}
      <div className="card-elevated rounded-lg p-6 bg-card border border-border animate-slide-in">
        <h2 className="text-lg font-title font-bold text-foreground mb-4">最近活动</h2>
        <div className="space-y-4">
          {[
            { action: '创建工作流', user: 'admin', time: '2分钟前', color: 'primary' },
            { action: '执行工作流', user: 'user1', time: '15分钟前', color: 'secondary' },
            { action: '注册新工具', user: 'admin', time: '1小时前', color: 'accent' },
            { action: '更新用户权限', user: 'admin', time: '2小时前', color: 'primary' },
          ].map((activity, index) => (
            <div
              key={index}
              className="flex items-center gap-4 p-3 border-b border-border last:border-0 hover:bg-muted/50 transition-colors rounded-lg animate-fade-in"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div
                className={`w-10 h-10 rounded-full bg-${activity.color}/10 flex items-center justify-center`}
              >
                <FileText className={`w-5 h-5 text-${activity.color}`} />
              </div>
              <div className="flex-1">
                <p className="text-sm text-foreground font-body">
                  <span className="font-bold">{activity.user}</span> {activity.action}
                </p>
                <p className="text-xs text-mutedForeground">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
