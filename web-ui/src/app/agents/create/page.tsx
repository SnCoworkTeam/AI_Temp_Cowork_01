'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import { ArrowLeftIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

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

export default function CreateAgentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/v1/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '创建智能体失败');
      }

      const agent = await response.json();
      router.push(`/agents/${agent.id}`);
    } catch (error) {
      console.error('Failed to create agent:', error);
      alert(error instanceof Error ? error.message : '创建智能体失败');
    } finally {
      setLoading(false);
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
            <h1 className="text-3xl font-bold text-gray-900">创建智能体</h1>
            <p className="mt-2 text-sm text-gray-600">创建一个新的智能体，配置其能力和行为</p>
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
                    placeholder="例如：SAP查询智能体"
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
                    placeholder="描述智能体的功能和用途"
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
                placeholder="定义智能体的行为、角色和任务..."
              />
              <p className="mt-2 text-xs text-gray-500">系统提示词用于指导智能体的行为和响应方式</p>
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
                        placeholder="sap_query&#10;knowledge_search"
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
                        placeholder="例如：sap-mcp-server"
                      />
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex items-center justify-end gap-4 pt-6 border-t border-gray-200">
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
                    <span>创建中...</span>
                  </>
                ) : (
                  <>
                    <CheckIcon className="w-5 h-5" />
                    <span>创建智能体</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </AuthGuard>
  );
}
