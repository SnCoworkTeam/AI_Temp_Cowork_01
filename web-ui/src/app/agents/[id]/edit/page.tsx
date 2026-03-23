'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import { ArrowLeftIcon, CheckIcon, TrashIcon } from '@heroicons/react/24/outline';

interface AgentFormData {
  name: string;
  description: string;
  capabilities: string[];
  system_prompt: string;
  config: {
    preferred_tools?: string[];
    use_tool_integration?: boolean;
    auto_analysis?: boolean;
    default_table?: string;
  };
  metadata: {
    mcp_server?: string;
    integration_type?: string;
    version?: string;
  };
}

const AVAILABLE_CAPABILITIES = [
  { value: 'data_analysis', label: '数据分析' },
  { value: 'document_processing', label: '文档处理' },
  { value: 'workflow_orchestration', label: '工作流编排' },
  { value: 'code_generation', label: '代码生成' },
  { value: 'knowledge_retrieval', label: '知识检索' },
  { value: 'conversation', label: '对话' },
  { value: 'task_planning', label: '任务规划' },
  { value: 'multi_agent_coordination', label: '多智能体协调' },
];

export default function EditAgentPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [formData, setFormData] = useState<AgentFormData>({
    name: '',
    description: '',
    capabilities: [],
    system_prompt: '',
    config: {
      preferred_tools: [],
      use_tool_integration: false,
      auto_analysis: false,
      default_table: '',
    },
    metadata: {
      mcp_server: '',
      integration_type: 'mcp_tool',
      version: '1.0.0',
    },
  });

  useEffect(() => {
    fetchAgent();
  }, [agentId]);

  const fetchAgent = async () => {
    try {
      setFetching(true);
      const response = await fetch(`/api/v1/agents/${agentId}`);
      if (!response.ok) {
        throw new Error('获取智能体详情失败');
      }
      const agent = await response.json();

      setFormData({
        name: agent.name || '',
        description: agent.description || '',
        capabilities: agent.capabilities || [],
        system_prompt: agent.system_prompt || '',
        config: agent.config || {
          preferred_tools: [],
          use_tool_integration: false,
          auto_analysis: false,
          default_table: '',
        },
        metadata: agent.metadata || {
          mcp_server: '',
          integration_type: 'mcp_tool',
          version: '1.0.0',
        },
      });
    } catch (error) {
      console.error('Failed to fetch agent:', error);
      alert('获取智能体详情失败');
      router.push('/agents');
    } finally {
      setFetching(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`/api/v1/agents/${agentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '更新智能体失败');
      }

      router.push(`/agents/${agentId}`);
    } catch (error) {
      console.error('Failed to update agent:', error);
      alert(error instanceof Error ? error.message : '更新智能体失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('确定要删除这个智能体吗？此操作不可撤销。')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/agents/${agentId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '删除智能体失败');
      }

      router.push('/agents');
    } catch (error) {
      console.error('Failed to delete agent:', error);
      alert(error instanceof Error ? error.message : '删除智能体失败');
    }
  };

  const toggleCapability = (capability: string) => {
    setFormData((prev) => ({
      ...prev,
      capabilities: prev.capabilities.includes(capability)
        ? prev.capabilities.filter((c) => c !== capability)
        : [...prev.capabilities, capability],
    }));
  };

  if (fetching) {
    return (
      <AuthGuard requireAuth>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="ml-3 text-gray-600">加载中...</span>
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard requireAuth>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* 页面标题 */}
          <div className="mb-8">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
            >
              <ArrowLeftIcon className="w-5 h-5" />
              <span>返回</span>
            </button>
            <h1 className="text-3xl font-bold text-gray-900">编辑智能体</h1>
            <p className="mt-2 text-sm text-gray-600">修改智能体的配置和行为</p>
          </div>

          {/* 表单 */}
          <form
            onSubmit={handleSubmit}
            className="bg-white rounded-lg border border-gray-200 p-6 space-y-6"
          >
            {/* 基本信息 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">基本信息</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    智能体名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    描述 <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    required
                    value={formData.description}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, description: e.target.value }))
                    }
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* 能力配置 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">能力配置</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {AVAILABLE_CAPABILITIES.map((cap) => (
                  <button
                    key={cap.value}
                    type="button"
                    onClick={() => toggleCapability(cap.value)}
                    className={`px-4 py-2 rounded-lg border text-sm transition-colors ${
                      formData.capabilities.includes(cap.value)
                        ? 'bg-blue-50 border-blue-500 text-blue-700'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {cap.label}
                  </button>
                ))}
              </div>
            </div>

            {/* 系统提示词 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">系统提示词</label>
              <textarea
                value={formData.system_prompt}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, system_prompt: e.target.value }))
                }
                rows={8}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              />
            </div>

            {/* MCP工具集成配置 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">MCP工具集成</h2>

              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="use_tool_integration"
                    checked={formData.config.use_tool_integration}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        config: { ...prev.config, use_tool_integration: e.target.checked },
                      }))
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="use_tool_integration" className="text-sm text-gray-700">
                    启用工具集成（允许智能体调用MCP工具）
                  </label>
                </div>

                {formData.config.use_tool_integration && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        优先使用的工具（每行一个）
                      </label>
                      <textarea
                        value={formData.config.preferred_tools?.join('\n') || ''}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            config: {
                              ...prev.config,
                              preferred_tools: e.target.value.split('\n').filter((t) => t.trim()),
                            },
                          }))
                        }
                        rows={3}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        MCP服务器名称
                      </label>
                      <input
                        type="text"
                        value={formData.metadata.mcp_server || ''}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            metadata: { ...prev.metadata, mcp_server: e.target.value },
                          }))
                        }
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex items-center justify-between pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={handleDelete}
                className="px-4 py-2 text-red-600 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors flex items-center gap-2"
              >
                <TrashIcon className="w-5 h-5" />
                <span>删除智能体</span>
              </button>

              <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={loading || !formData.name || !formData.description}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>保存中...</span>
                    </>
                  ) : (
                    <>
                      <CheckIcon className="w-5 h-5" />
                      <span>保存更改</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </AuthGuard>
  );
}
