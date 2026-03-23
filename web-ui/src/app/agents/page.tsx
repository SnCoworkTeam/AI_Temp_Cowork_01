'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import ErrorMessage from '@/components/ErrorMessage';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import {
  PlusIcon,
  PlayIcon,
  PencilIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface Agent {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  status: 'active' | 'inactive' | 'training' | 'error';
  system_prompt?: string;
  config?: Record<string, any>;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/v1/agents');
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '获取智能体列表失败' }));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();

      // 适配不同的响应格式
      if (Array.isArray(data)) {
        setAgents(data);
      } else if (data.agents && Array.isArray(data.agents)) {
        setAgents(data.agents);
      } else {
        setAgents([]);
      }
    } catch (error: any) {
      console.error('Failed to fetch agents:', error);
      setError(error?.message || '获取智能体列表失败，请稍后重试');
      setAgents([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredAgents = agents.filter((agent) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      agent.name.toLowerCase().includes(query) ||
      agent.description.toLowerCase().includes(query) ||
      (agent.capabilities && agent.capabilities.some((cap) => cap.toLowerCase().includes(query)))
    );
  });

  // 状态颜色已直接在JSX中使用主题变量，此函数保留用于兼容性
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-secondary/10 text-secondary border-secondary/20';
      case 'inactive':
        return 'bg-muted text-mutedForeground border-border';
      case 'error':
        return 'bg-destructive/10 text-destructive border-destructive/20';
      case 'updating':
      case 'training':
        return 'bg-accent/10 text-accent border-accent/20';
      default:
        return 'bg-muted text-mutedForeground border-border';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '运行中';
      case 'inactive':
        return '已停用';
      case 'error':
        return '错误';
      case 'updating':
        return '更新中';
      default:
        return status;
    }
  };

  return (
    <AuthGuard requireAuth>
      <ErrorBoundary>
        <div className="min-h-screen bg-background">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* 错误提示 */}
            <ErrorMessage message={error} type="error" onClose={() => setError(null)} />

            {/* 页面标题和操作栏 */}
            <div className="mb-8 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-3xl font-title font-bold text-foreground">智能体</h1>
                <p className="mt-2 text-sm text-mutedForeground font-body">
                  管理和使用智能体，让AI助手更智能
                </p>
              </div>
              <button
                onClick={() => router.push('/agents/create')}
                className="btn-primary inline-flex items-center gap-2 px-4 py-2 rounded-lg font-body"
              >
                <PlusIcon className="w-5 h-5" />
                <span>创建智能体</span>
              </button>
            </div>

            {/* 搜索栏 */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mutedForeground" />
              <input
                type="text"
                placeholder="搜索智能体..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent font-body transition-all"
              />
            </div>
          </div>

          {/* 加载状态 */}
          {loading ? (
            <div className="flex items-center justify-center py-12 animate-fade-in">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
              <span className="ml-3 text-mutedForeground font-body">加载中...</span>
            </div>
          ) : filteredAgents.length === 0 ? (
            /* 空状态 */
            <div className="text-center py-12 bg-card rounded-lg border border-border card-elevated animate-fade-in">
              <SparklesIcon className="mx-auto h-12 w-12 text-mutedForeground" />
              <h3 className="mt-4 text-lg font-title font-bold text-foreground">暂无智能体</h3>
              <p className="mt-2 text-sm text-mutedForeground font-body">
                {searchQuery ? '没有找到匹配的智能体' : '创建您的第一个智能体开始使用'}
              </p>
              {!searchQuery && (
                <button
                  onClick={() => router.push('/agents/create')}
                  className="mt-4 btn-primary inline-flex items-center gap-2 px-4 py-2 rounded-lg font-body"
                >
                  <PlusIcon className="w-5 h-5" />
                  <span>创建智能体</span>
                </button>
              )}
            </div>
          ) : (
            /* 智能体列表 */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredAgents.map((agent, index) => (
                <div
                  key={agent.id}
                  className="card-elevated bg-card rounded-lg border border-border cursor-pointer animate-fade-in"
                  style={{ animationDelay: `${index * 0.1}s` }}
                  onClick={() => router.push(`/agents/${agent.id}`)}
                >
                  <div className="p-6">
                    {/* 头部 */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-title font-bold text-foreground mb-1">
                          {agent.name}
                        </h3>
                        {agent.capabilities && agent.capabilities.length > 0 && (
                          <p className="text-xs text-mutedForeground font-body">
                            {agent.capabilities.join(', ')}
                          </p>
                        )}
                      </div>
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded border font-body ${
                          agent.status === 'active'
                            ? 'bg-secondary/10 text-secondary border-secondary/20'
                            : agent.status === 'error'
                              ? 'bg-destructive/10 text-destructive border-destructive/20'
                              : agent.status === 'updating' || agent.status === 'training'
                                ? 'bg-accent/10 text-accent border-accent/20'
                                : 'bg-muted text-mutedForeground border-border'
                        }`}
                      >
                        {getStatusText(agent.status)}
                      </span>
                    </div>

                    {/* 描述 */}
                    <p className="text-sm text-mutedForeground mb-4 line-clamp-2 font-body">
                      {agent.description || '暂无描述'}
                    </p>

                    {/* 元信息 */}
                    <div className="flex items-center justify-between text-xs text-mutedForeground mb-4 font-body">
                      {agent.capabilities && agent.capabilities.length > 0 && (
                        <span>能力: {agent.capabilities.length}个</span>
                      )}
                      {agent.metadata?.mcp_server && <span>MCP: {agent.metadata.mcp_server}</span>}
                    </div>

                    {/* 操作按钮 */}
                    <div className="flex items-center gap-2 pt-4 border-t border-border">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/agents/${agent.id}`);
                        }}
                        className="flex-1 inline-flex items-center justify-center gap-2 px-3 py-2 text-sm bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors font-body"
                      >
                        <PlayIcon className="w-4 h-4" />
                        <span>执行</span>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/agents/${agent.id}/edit`);
                        }}
                        className="px-3 py-2 text-sm text-mutedForeground hover:bg-muted rounded-lg transition-colors"
                      >
                        <PencilIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // TODO: 实现删除功能
                        }}
                        className="px-3 py-2 text-sm text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      </ErrorBoundary>
    </AuthGuard>
  );
}
