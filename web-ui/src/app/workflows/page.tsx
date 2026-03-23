'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  PlusIcon,
  PlayIcon,
  PencilIcon,
  TrashIcon,
  ClockIcon,
  CheckCircleIcon,
  LinkIcon,
  ClipboardIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { Modal } from '@/components/UI/Modal';
import { Button } from '@/components/UI/Button';
import { WorkflowPreview } from '@/components/WorkflowPreview';
import ErrorMessage from '@/components/ErrorMessage';
import { ErrorBoundary } from '@/components/ErrorBoundary';

interface Workflow {
  id: string;
  name: string;
  description: string;
  version: string;
  status: 'draft' | 'active' | 'inactive' | 'archived';
  created_at: string;
  updated_at: string;
  execution_count?: number;
}

export default function WorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // 执行对话框状态
  const [executeModalOpen, setExecuteModalOpen] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [inputData, setInputData] = useState('{}');
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);

  // 发布成功对话框状态
  const [publishSuccessModalOpen, setPublishSuccessModalOpen] = useState(false);
  const [publishedWorkflowLink, setPublishedWorkflowLink] = useState<string>('');

  // 预览对话框状态
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [previewWorkflowId, setPreviewWorkflowId] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkflows();
  }, [filterStatus]);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      if (filterStatus !== 'all') {
        params.append('status', filterStatus);
      }

      const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      const response = await fetch(`${API_BASE}/api/workflows?${params.toString()}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '获取工作流列表失败' }));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.workflows) {
        setWorkflows(data.workflows);
      } else {
        setWorkflows([]);
      }
    } catch (error: any) {
      console.error('Failed to fetch workflows:', error);
      setError(error?.message || '获取工作流列表失败，请稍后重试');
      setWorkflows([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkflow = () => {
    router.push('/workflow-designer');
  };

  const handleEditWorkflow = (id: string) => {
    router.push(`/workflow-designer?id=${id}`);
  };

  // 打开预览对话框
  const handlePreviewWorkflow = (id: string) => {
    setPreviewWorkflowId(id);
    setPreviewModalOpen(true);
  };

  // 关闭预览对话框
  const handleClosePreview = () => {
    setPreviewModalOpen(false);
    setPreviewWorkflowId(null);
  };

  // 打开执行对话框
  const handleOpenExecuteDialog = (workflow: Workflow) => {
    setSelectedWorkflow(workflow);
    setInputData('{}');
    setExecutionResult(null);
    setExecutionError(null);
    setExecuteModalOpen(true);
  };

  // 执行工作流
  const handleExecuteWorkflow = async () => {
    if (!selectedWorkflow) return;

    try {
      setExecuting(true);
      setExecutionError(null);
      setExecutionResult(null);

      // 解析输入数据
      let parsedInputData = {};
      try {
        parsedInputData = JSON.parse(inputData);
      } catch (e) {
        setExecutionError('输入数据格式错误，请输入有效的 JSON');
        setExecuting(false);
        return;
      }

      const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      const response = await fetch(`${API_BASE}/api/workflows/${selectedWorkflow.id}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input_data: parsedInputData,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setExecutionResult(data);
        fetchWorkflows(); // 刷新列表以更新执行次数
      } else {
        setExecutionError(data.error || '工作流执行失败');
      }
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      setExecutionError('执行失败: ' + (error instanceof Error ? error.message : '未知错误'));
    } finally {
      setExecuting(false);
    }
  };

  // 关闭执行对话框
  const handleCloseExecuteDialog = () => {
    setExecuteModalOpen(false);
    setSelectedWorkflow(null);
    setInputData('{}');
    setExecutionResult(null);
    setExecutionError(null);
  };

  // 复制工作流访问链接
  const handleCopyLink = (workflowId: string) => {
    const link = `${window.location.origin}/workflows/${workflowId}/run`;
    navigator.clipboard
      .writeText(link)
      .then(() => {
        setSuccessMessage('链接已复制到剪贴板');
        setTimeout(() => setSuccessMessage(null), 3000);
      })
      .catch(() => {
        setError('复制失败，请手动复制: ' + link);
      });
  };

  const handleDeleteWorkflow = async (id: string, name: string) => {
    if (!confirm(`确定要删除工作流 "${name}" 吗？`)) {
      return;
    }

    try {
      setError(null);
      const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      const response = await fetch(`${API_BASE}/api/workflows/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setSuccessMessage('工作流删除成功');
        setTimeout(() => setSuccessMessage(null), 3000);
        fetchWorkflows();
      } else {
        const errorData = await response.json().catch(() => ({ detail: '删除失败' }));
        setError(errorData.detail || '工作流删除失败');
      }
    } catch (error: any) {
      console.error('Failed to delete workflow:', error);
      setError(error?.message || '工作流删除失败，请稍后重试');
    }
  };

  const handlePublishWorkflow = async (id: string, name: string) => {
    if (
      !confirm(
        `确定要发布工作流 "${name}" 吗？发布后工作流状态将变为"激活"状态，可以通过公开链接访问。`
      )
    ) {
      return;
    }

    try {
      setError(null);
      const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      const response = await fetch(`${API_BASE}/api/workflows/${id}/status?status=active`, {
        method: 'PATCH',
      });

      if (response.ok) {
        const link = `${window.location.origin}/workflows/${id}/run`;
        setPublishedWorkflowLink(link);
        setPublishSuccessModalOpen(true);
        // 自动复制链接
        navigator.clipboard.writeText(link).catch(() => {});
        fetchWorkflows();
      } else {
        const errorData = await response.json().catch(() => ({ detail: '发布失败' }));
        setError(errorData.detail || '工作流发布失败');
      }
    } catch (error: any) {
      console.error('Failed to publish workflow:', error);
      setError(error?.message || '工作流发布失败，请稍后重试');
    }
  };

  const filteredWorkflows = workflows.filter(
    (workflow) =>
      workflow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      workflow.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const badges = {
      draft: { bg: 'bg-gray-100', text: 'text-gray-800', label: '草稿' },
      active: { bg: 'bg-green-100', text: 'text-green-800', label: '激活' },
      inactive: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: '未激活' },
      archived: { bg: 'bg-red-100', text: 'text-red-800', label: '已归档' },
    };

    const badge = badges[status as keyof typeof badges] || badges.draft;

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}
      >
        {badge.label}
      </span>
    );
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* 错误和成功提示 */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <ErrorMessage message={error} type="error" onClose={() => setError(null)} />
          <ErrorMessage message={successMessage} type="success" onClose={() => setSuccessMessage(null)} autoClose />
        </div>

        {/* Header */}
        <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">工作流</h1>
                <p className="mt-1 text-sm text-gray-500">创建和管理自动化工作流</p>
              </div>
              <button
                onClick={handleCreateWorkflow}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                创建工作流
              </button>
            </div>

            {/* Search and Filter */}
            <div className="mt-6 flex items-center gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="搜索工作流..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">全部状态</option>
                <option value="draft">草稿</option>
                <option value="active">激活</option>
                <option value="inactive">未激活</option>
                <option value="archived">已归档</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Workflow List */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredWorkflows.length === 0 ? (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">暂无工作流</h3>
            <p className="mt-1 text-sm text-gray-500">点击上方按钮创建您的第一个工作流</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredWorkflows.map((workflow) => (
              <div
                key={workflow.id}
                className="bg-white rounded-lg border border-gray-200 hover:border-blue-500 hover:shadow-lg transition-all duration-200"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">{workflow.name}</h3>
                      <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                        {workflow.description || '暂无描述'}
                      </p>
                    </div>
                    {getStatusBadge(workflow.status)}
                  </div>

                  <div className="flex items-center gap-4 text-xs text-gray-500 mb-4">
                    <div className="flex items-center gap-1">
                      <ClockIcon className="h-4 w-4" />
                      <span>版本 {workflow.version}</span>
                    </div>
                    {workflow.execution_count !== undefined && (
                      <div className="flex items-center gap-1">
                        <CheckCircleIcon className="h-4 w-4" />
                        <span>执行 {workflow.execution_count} 次</span>
                      </div>
                    )}
                  </div>

                  <div className="text-xs text-gray-400 mb-4">
                    更新于 {new Date(workflow.updated_at).toLocaleDateString('zh-CN')}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handlePreviewWorkflow(workflow.id)}
                      className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      title="预览工作流"
                    >
                      <EyeIcon className="h-4 w-4 mr-1" />
                      预览
                    </button>
                    <button
                      onClick={() => handleOpenExecuteDialog(workflow)}
                      className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <PlayIcon className="h-4 w-4 mr-1" />
                      执行
                    </button>
                    {workflow.status === 'active' && (
                      <button
                        onClick={() => handleCopyLink(workflow.id)}
                        className="inline-flex items-center justify-center p-2 border border-blue-300 rounded-lg text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        title="复制访问链接"
                      >
                        <LinkIcon className="h-4 w-4" />
                      </button>
                    )}
                    {workflow.status === 'draft' && (
                      <button
                        onClick={() => handlePublishWorkflow(workflow.id, workflow.name)}
                        className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-green-300 rounded-lg text-sm font-medium text-green-700 bg-green-50 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                        title="发布工作流"
                      >
                        发布
                      </button>
                    )}
                    <button
                      onClick={() => handleEditWorkflow(workflow.id)}
                      className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-blue-300 rounded-lg text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <PencilIcon className="h-4 w-4 mr-1" />
                      编辑
                    </button>
                    <button
                      onClick={() => handleDeleteWorkflow(workflow.id, workflow.name)}
                      className="inline-flex items-center justify-center p-2 border border-red-300 rounded-lg text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 执行对话框 */}
      <Modal
        isOpen={executeModalOpen}
        onClose={handleCloseExecuteDialog}
        title={selectedWorkflow ? `执行工作流: ${selectedWorkflow.name}` : '执行工作流'}
        size="lg"
      >
        <div className="space-y-4">
          {selectedWorkflow && (
            <>
              <div>
                <p className="text-sm text-gray-600 mb-2">
                  {selectedWorkflow.description || '暂无描述'}
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    输入参数 (JSON格式)
                  </label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setInputData('{\n  "input": "请输入您的问题或内容"\n}')}
                      className="text-xs text-blue-600 hover:text-blue-800 underline"
                      disabled={executing}
                    >
                      简单示例
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputData('{\n  "query": "搜索关键词",\n  "limit": 5\n}')}
                      className="text-xs text-blue-600 hover:text-blue-800 underline"
                      disabled={executing}
                    >
                      搜索示例
                    </button>
                    <button
                      type="button"
                      onClick={() => setInputData('{}')}
                      className="text-xs text-gray-600 hover:text-gray-800 underline"
                      disabled={executing}
                    >
                      清空
                    </button>
                  </div>
                </div>
                <textarea
                  value={inputData}
                  onChange={(e) => setInputData(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  rows={10}
                  placeholder='{"input": "您的问题或内容"}'
                  disabled={executing}
                />
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-gray-500">
                    💡 提示：输入参数会被放入工作流的{' '}
                    <code className="bg-gray-100 px-1 rounded">input</code> 字段
                  </p>
                  <p className="text-xs text-gray-500">📝 常见格式：</p>
                  <ul className="text-xs text-gray-500 ml-4 list-disc">
                    <li>
                      简单文本：
                      <code className="bg-gray-100 px-1 rounded">
                        {'{'}&quot;input&quot;: &quot;问题&quot;{'}'}
                      </code>
                    </li>
                    <li>
                      多字段：
                      <code className="bg-gray-100 px-1 rounded">
                        {'{'}&quot;query&quot;: &quot;关键词&quot;, &quot;limit&quot;: 10{'}'}
                      </code>
                    </li>
                    <li>
                      空输入：<code className="bg-gray-100 px-1 rounded">{'{}'}</code>
                      （如果工作流不需要参数）
                    </li>
                  </ul>
                </div>
              </div>

              {executionError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <svg
                      className="h-5 w-5 text-red-500 mr-2"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <p className="text-sm text-red-700">{executionError}</p>
                  </div>
                </div>
              )}

              {executionResult && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-green-800">执行成功</h4>
                    <span className="text-xs text-green-600">
                      执行时间: {executionResult.execution_time?.toFixed(2) || 'N/A'} 秒
                    </span>
                  </div>
                  <div className="mt-2">
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      执行结果:
                    </label>
                    <pre className="bg-white border border-gray-200 rounded p-3 text-xs overflow-auto max-h-64">
                      {JSON.stringify(executionResult.result || executionResult, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t">
                <Button variant="outline" onClick={handleCloseExecuteDialog} disabled={executing}>
                  关闭
                </Button>
                <Button
                  variant="primary"
                  onClick={handleExecuteWorkflow}
                  loading={executing}
                  disabled={executing}
                >
                  {executing ? '执行中...' : '执行工作流'}
                </Button>
              </div>
            </>
          )}
        </div>
      </Modal>

      {/* 发布成功对话框 */}
      <Modal
        isOpen={publishSuccessModalOpen}
        onClose={() => setPublishSuccessModalOpen(false)}
        title="工作流发布成功"
        size="md"
      >
        <div className="space-y-4">
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircleIcon className="h-10 w-10 text-green-600" />
            </div>
          </div>

          <p className="text-center text-gray-700">工作流已成功发布！现在可以通过以下链接访问：</p>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={publishedWorkflowLink}
                readOnly
                className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm font-mono"
              />
              <button
                onClick={() => {
                  navigator.clipboard.writeText(publishedWorkflowLink).then(() => {
                    alert('链接已复制到剪贴板');
                  });
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <ClipboardIcon className="h-4 w-4" />
                复制
              </button>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-xs text-blue-700">
              💡 提示：您可以将此链接分享给其他人，他们无需登录即可访问和执行此工作流。
            </p>
          </div>

          <div className="flex justify-end pt-4">
            <Button
              variant="primary"
              onClick={() => {
                setPublishSuccessModalOpen(false);
                // 可选：在新标签页打开链接
                window.open(publishedWorkflowLink, '_blank');
              }}
            >
              打开工作流页面
            </Button>
          </div>
        </div>
      </Modal>

      {/* 预览对话框 */}
      <Modal
        isOpen={previewModalOpen}
        onClose={handleClosePreview}
        title={previewWorkflowId ? `预览工作流` : '预览工作流'}
        size="xl"
      >
        <div className="h-[600px]">
          {previewWorkflowId && (
            <WorkflowPreview workflowId={previewWorkflowId} onClose={handleClosePreview} />
          )}
        </div>
      </Modal>
      </div>
    </ErrorBoundary>
  );
}
